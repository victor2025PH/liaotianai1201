# 定期进度报告系统 - 每5分钟报告一次运行进度和问题

$Server = "ubuntu@165.154.233.55"
$ReportInterval = 300  # 5分钟 = 300秒
$MaxReports = 48  # 最多报告48次（4小时）

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "定期进度报告系统" -ForegroundColor Cyan
Write-Host "报告间隔: 5分钟" -ForegroundColor Gray
Write-Host "开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Invoke-SSH {
    param($Cmd)
    try {
        $result = ssh $Server $Cmd 2>&1
        return $result -join "`n"
    } catch {
        return "错误: $_"
    }
}

function Get-Timestamp {
    return Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

function Write-Report {
    param($Title, $Content, $Type = "Info")
    
    $colors = @{
        "Success" = "Green"
        "Error" = "Red"
        "Warning" = "Yellow"
        "Info" = "Cyan"
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor $colors[$Type]
    Write-Host "$Title" -ForegroundColor $colors[$Type]
    Write-Host "$(Get-Timestamp)" -ForegroundColor Gray
    Write-Host "========================================" -ForegroundColor $colors[$Type]
    Write-Host ""
    
    if ($Content) {
        Write-Host $Content
    }
    Write-Host ""
}

function Get-LatestLog {
    $log1 = Invoke-SSH "ls -t ~/liaotian/test_logs/final_run.log 2>/dev/null | head -1"
    $log2 = Invoke-SSH "ls -t ~/liaotian/test_logs/realtime_monitor_*.log 2>/dev/null | head -1"
    $log3 = Invoke-SSH "ls -t ~/liaotian/test_logs/direct_exec.log 2>/dev/null | head -1"
    
    $logs = @($log1, $log2, $log3) | Where-Object { $_ -and $_.Trim() }
    return $logs | Select-Object -First 1
}

function Analyze-Progress {
    param($LogContent)
    
    $progress = @{
        "Stage" = "未知"
        "Progress" = ""
        "Issues" = @()
        "Recommendations" = @()
    }
    
    # 检测阶段
    if ($LogContent -match "步骤 1|步骤 2|步骤 3|步骤 4|步骤 5|步骤 6") {
        $matches = [regex]::Matches($LogContent, "步骤 (\d)")
        if ($matches.Count -gt 0) {
            $lastStep = $matches[$matches.Count - 1].Groups[1].Value
            $stages = @{
                "1" = "更新代码"
                "2" = "检查后端服务"
                "3" = "创建测试用户"
                "4" = "验证登录"
                "5" = "安装浏览器"
                "6" = "运行测试"
            }
            $progress.Stage = $stages[$lastStep]
        }
    }
    
    if ($LogContent -match "开始运行|Running|tests") {
        $progress.Stage = "运行测试中"
    }
    
    if ($LogContent -match "所有任务完成|所有测试通过|✅.*成功|passed|PASS") {
        $progress.Stage = "已完成"
    }
    
    # 检测进度
    if ($LogContent -match "(\d+)/(\d+) tests|测试 (\d+)/(\d+)") {
        $progress.Progress = "正在执行测试用例"
    }
    
    # 检测问题
    $issues = @()
    
    if ($LogContent -match "后端服务未运行|backend.*down|连接失败") {
        $issues += "后端服务未运行"
        $progress.Recommendations += "启动后端服务: cd ~/liaotian/admin-backend && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
    }
    
    if ($LogContent -match "登录失败|auth.*failed|unauthorized|邮箱或密码错误") {
        $issues += "认证失败"
        $progress.Recommendations += "修复用户: cd ~/liaotian/admin-backend && source .venv/bin/activate && export ADMIN_DEFAULT_PASSWORD=testpass123 && python reset_admin_user.py"
    }
    
    if ($LogContent -match "浏览器|browser.*not found|chromium") {
        $issues += "浏览器未安装"
        $progress.Recommendations += "安装浏览器: cd ~/liaotian/saas-demo && npx playwright install chromium"
    }
    
    if ($LogContent -match "timeout|超时|timed out") {
        $issues += "超时错误"
        $progress.Recommendations += "检查网络连接和服务器资源"
    }
    
    if ($LogContent -match "错误|error|failed|失败" -and $LogContent -notmatch "已完成|成功") {
        $issues += "执行错误"
    }
    
    $progress.Issues = $issues
    
    # 检测测试结果
    if ($LogContent -match "(\d+) passed") {
        $progress.Progress = "测试通过: $($matches[0])"
    }
    if ($LogContent -match "(\d+) failed") {
        $progress.Progress = "测试失败: $($matches[0])"
        $issues += "部分测试失败"
    }
    
    return $progress
}

function Auto-Fix {
    param($Issues, $LogContent)
    
    $fixed = @()
    
    foreach ($issue in $Issues) {
        if ($issue -eq "认证失败") {
            Write-Host "  [自动修复] 修复认证问题..." -ForegroundColor Yellow
            Invoke-SSH "cd ~/liaotian/admin-backend && source .venv/bin/activate && export ADMIN_DEFAULT_PASSWORD=testpass123 && python reset_admin_user.py > /dev/null 2>&1" | Out-Null
            Start-Sleep -Seconds 2
            $fixed += "认证问题已修复"
        }
        
        if ($issue -eq "后端服务未运行") {
            Write-Host "  [自动修复] 后端服务需要手动启动" -ForegroundColor Yellow
        }
        
        if ($issue -eq "浏览器未安装") {
            Write-Host "  [自动修复] 安装浏览器..." -ForegroundColor Yellow
            Invoke-SSH "cd ~/liaotian/saas-demo && npx playwright install chromium > /dev/null 2>&1" | Out-Null
            $fixed += "浏览器安装已启动"
        }
    }
    
    return $fixed
}

# 主循环
$reportCount = 0
$lastLogContent = ""

while ($reportCount -lt $MaxReports) {
    $reportCount++
    $nextCheck = (Get-Date).AddSeconds($ReportInterval).ToString("HH:mm:ss")
    
    Write-Report "进度报告 #$reportCount" "下一次报告时间: $nextCheck" "Info"
    
    # 1. 检查后端服务状态
    Write-Host "[1] 检查后端服务状态..." -ForegroundColor Cyan
    $health = Invoke-SSH "curl -s http://localhost:8000/health 2>&1"
    if ($health -match "ok|status") {
        Write-Host "  ✅ 后端服务正常运行" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 后端服务未运行或无法访问" -ForegroundColor Red
    }
    Write-Host ""
    
    # 2. 检查进程状态
    Write-Host "[2] 检查测试进程..." -ForegroundColor Cyan
    $processes = Invoke-SSH "ps aux | grep -E '直接执行|playwright|test|服务器端实时监控' | grep -v grep"
    if ($processes) {
        Write-Host "  ✅ 测试进程正在运行:" -ForegroundColor Green
        $processes -split "`n" | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    } else {
        Write-Host "  ⚠️  未发现测试进程" -ForegroundColor Yellow
    }
    Write-Host ""
    
    # 3. 获取日志文件
    Write-Host "[3] 分析日志文件..." -ForegroundColor Cyan
    $logFile = Get-LatestLog
    
    if ($logFile) {
        Write-Host "  📄 日志文件: $([System.IO.Path]::GetFileName($logFile.Trim()))" -ForegroundColor Gray
        
        $logContent = Invoke-SSH "cat '$($logFile.Trim())' 2>/dev/null || tail -200 '$($logFile.Trim())' 2>/dev/null"
        
        if ($logContent) {
            # 分析进度
            $progress = Analyze-Progress $logContent
            
            Write-Host "  📊 当前阶段: $($progress.Stage)" -ForegroundColor Cyan
            if ($progress.Progress) {
                Write-Host "  📈 进度: $($progress.Progress)" -ForegroundColor Cyan
            }
            Write-Host ""
            
            # 显示最近的日志
            $recentLines = ($logContent -split "`n") | Select-Object -Last 20
            Write-Host "  📝 最近日志 (最后20行):" -ForegroundColor Gray
            foreach ($line in $recentLines) {
                if ($line.Trim()) {
                    if ($line -match '✅|成功|通过|SUCCESS') {
                        Write-Host "    $line" -ForegroundColor Green
                    } elseif ($line -match '❌|失败|错误|ERROR|FAILED') {
                        Write-Host "    $line" -ForegroundColor Red
                    } else {
                        Write-Host "    $line" -ForegroundColor Gray
                    }
                }
            }
            Write-Host ""
            
            # 显示问题和建议
            if ($progress.Issues.Count -gt 0) {
                Write-Host "  ⚠️  发现的问题:" -ForegroundColor Yellow
                foreach ($issue in $progress.Issues) {
                    Write-Host "    • $issue" -ForegroundColor Yellow
                }
                Write-Host ""
                
                # 自动修复
                Write-Host "  🔧 自动修复尝试..." -ForegroundColor Cyan
                $fixed = Auto-Fix $progress.Issues $logContent
                if ($fixed.Count -gt 0) {
                    foreach ($fix in $fixed) {
                        Write-Host "    ✅ $fix" -ForegroundColor Green
                    }
                }
                Write-Host ""
                
                if ($progress.Recommendations.Count -gt 0) {
                    Write-Host "  💡 建议的操作:" -ForegroundColor Cyan
                    foreach ($rec in $progress.Recommendations) {
                        Write-Host "    • $rec" -ForegroundColor Gray
                    }
                    Write-Host ""
                }
            } else {
                Write-Host "  ✅ 未发现明显问题" -ForegroundColor Green
                Write-Host ""
            }
            
            # 检查是否完成
            if ($logContent -match "所有任务完成|所有测试通过|✅.*成功|测试.*成功|所有测试.*完成") {
                Write-Host "========================================" -ForegroundColor Green
                Write-Host "✅ 所有任务成功完成！" -ForegroundColor Green
                Write-Host "========================================" -ForegroundColor Green
                Write-Host ""
                
                # 提取测试结果
                if ($logContent -match "(\d+) passed|通过.*?(\d+)") {
                    Write-Host "测试结果摘要:" -ForegroundColor Cyan
                    $logContent -split "`n" | Where-Object { $_ -match "passed|failed|通过|失败" } | Select-Object -First 10 | ForEach-Object {
                        Write-Host "  $_" -ForegroundColor Gray
                    }
                }
                
                exit 0
            }
            
            $lastLogContent = $logContent
        } else {
            Write-Host "  ⚠️  日志文件为空" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ⚠️  未找到日志文件" -ForegroundColor Yellow
        Write-Host "  💡 建议: 检查脚本是否已启动" -ForegroundColor Gray
    }
    Write-Host ""
    
    # 4. 检查状态文件
    Write-Host "[4] 检查状态文件..." -ForegroundColor Cyan
    $status = Invoke-SSH "cat ~/liaotian/test_logs/current_status.txt 2>/dev/null || echo ''"
    if ($status.Trim()) {
        Write-Host "  📋 当前状态: $($status.Trim())" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠️  状态文件不存在" -ForegroundColor Yellow
    }
    Write-Host ""
    
    # 5. 磁盘空间检查
    Write-Host "[5] 系统资源检查..." -ForegroundColor Cyan
    $disk = Invoke-SSH "df -h ~/liaotian | tail -1"
    if ($disk) {
        Write-Host "  💾 磁盘使用: $disk" -ForegroundColor Gray
    }
    Write-Host ""
    
    # 等待下一次报告
    if ($reportCount -lt $MaxReports) {
        $minutes = [math]::Round($ReportInterval / 60, 1)
        Write-Host "========================================" -ForegroundColor Gray
        Write-Host "等待 $minutes 分钟后进行下一次报告..." -ForegroundColor Gray
        Write-Host "当前时间: $(Get-Timestamp)" -ForegroundColor Gray
        Write-Host "下一次报告: $nextCheck" -ForegroundColor Gray
        Write-Host "========================================" -ForegroundColor Gray
        Write-Host ""
        
        Start-Sleep -Seconds $ReportInterval
    }
}

Write-Report "达到最大报告次数" "系统已监控 $($MaxReports * $ReportInterval / 60) 分钟" "Warning"

exit 0
