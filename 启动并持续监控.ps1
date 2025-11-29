# 启动服务器监控并持续读取日志显示实时信息

$Server = "ubuntu@165.154.233.55"
$MaxChecks = 200
$CheckInterval = 10

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "启动并持续监控系统" -ForegroundColor Cyan
Write-Host "开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 第一步：准备和启动
Write-Host "[准备] 更新代码并启动监控..." -ForegroundColor Yellow

$startResult = ssh $Server @"
cd ~/liaotian/saas-demo && \
git pull origin master > /dev/null 2>&1 && \
chmod +x 服务器端实时监控执行.sh && \
nohup bash 服务器端实时监控执行.sh > /tmp/monitor_output.log 2>&1 & \
echo \$! && \
sleep 2 && \
echo '===启动完成==='
"@

Write-Host $startResult
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "开始实时监控（每 $CheckInterval 秒检查）" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 持续监控循环
$checkCount = 0
$lastLogPosition = 0
$lastLogFile = ""

while ($checkCount -lt $MaxChecks) {
    $checkCount++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] 检查 #$checkCount" -ForegroundColor Cyan
    
    # 获取状态文件
    $status = ssh $Server "cat ~/liaotian/test_logs/current_status.txt 2>/dev/null || echo ''"
    if ($status.Trim()) {
        Write-Host "  状态: $($status.Trim())" -ForegroundColor Gray
    }
    
    # 获取最新日志文件
    $logFile = ssh $Server "ls -t ~/liaotian/test_logs/realtime_monitor_*.log 2>/dev/null | head -1"
    $logFile = $logFile.Trim()
    
    if ($logFile) {
        if ($logFile -ne $lastLogFile) {
            Write-Host "  日志文件: $([System.IO.Path]::GetFileName($logFile))" -ForegroundColor Gray
            $lastLogFile = $logFile
            $lastLogPosition = 0
        }
        
        # 获取日志内容
        $logContent = ssh $Server "tail -100 '$logFile' 2>/dev/null"
        
        if ($logContent) {
            $lines = $logContent -split "`n"
            
            # 显示新行
            if ($lines.Count -gt $lastLogPosition) {
                $newLines = $lines[$lastLogPosition..($lines.Count - 1)]
                foreach ($line in $newLines) {
                    if ($line.Trim()) {
                        # 根据内容着色
                        if ($line -match '✅|成功|通过|SUCCESS|完成') {
                            Write-Host "  $line" -ForegroundColor Green
                        } elseif ($line -match '❌|失败|错误|ERROR|FAILED') {
                            Write-Host "  $line" -ForegroundColor Red
                        } elseif ($line -match '⚠️|警告|WARNING') {
                            Write-Host "  $line" -ForegroundColor Yellow
                        } elseif ($line -match 'ℹ️|INFO|步骤|STEP') {
                            Write-Host "  $line" -ForegroundColor Cyan
                        } else {
                            Write-Host "  $line" -ForegroundColor Gray
                        }
                    }
                }
                $lastLogPosition = $lines.Count
            }
            
            # 检查是否完成
            if ($logContent -match "所有任务成功完成|所有测试通过|✅.*成功|测试.*成功") {
                Write-Host ""
                Write-Host "========================================" -ForegroundColor Green
                Write-Host "✅ 所有任务成功完成！" -ForegroundColor Green
                Write-Host "========================================" -ForegroundColor Green
                Write-Host ""
                
                Write-Host "最终日志摘要:"
                Write-Host "----------------------------------------"
                $finalLog = ssh $Server "tail -50 '$logFile' 2>/dev/null"
                Write-Host $finalLog
                Write-Host "----------------------------------------"
                
                exit 0
            }
            elseif ($logContent -match "测试失败|❌|错误|error|failed") {
                Write-Host ""
                Write-Host "检测到错误，尝试修复..." -ForegroundColor Yellow
                
                # 修复用户
                ssh $Server "cd ~/liaotian/admin-backend && source .venv/bin/activate && export ADMIN_DEFAULT_PASSWORD=testpass123 && python reset_admin_user.py > /dev/null 2>&1" | Out-Null
                Start-Sleep -Seconds 2
                
                # 重新启动
                ssh $Server "pkill -f '服务器端实时监控执行.sh' 2>/dev/null || true" | Out-Null
                Start-Sleep -Seconds 2
                ssh $Server "cd ~/liaotian/saas-demo && nohup bash 服务器端实时监控执行.sh > /dev/null 2>&1 &" | Out-Null
                Start-Sleep -Seconds 5
                
                $lastLogPosition = 0
                $lastLogFile = ""
                Write-Host "已重新启动，继续监控..." -ForegroundColor Green
                Write-Host ""
            }
        }
    } else {
        Write-Host "  等待日志文件生成..." -ForegroundColor Gray
    }
    
    Write-Host ""
    Start-Sleep -Seconds $CheckInterval
}

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "达到最大检查次数" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$logFile = ssh $Server "ls -t ~/liaotian/test_logs/realtime_monitor_*.log 2>/dev/null | head -1"
if ($logFile.Trim()) {
    Write-Host "`n查看日志: $($logFile.Trim())"
    $finalLog = ssh $Server "tail -50 '$($logFile.Trim())' 2>/dev/null"
    Write-Host $finalLog
}

exit 1
