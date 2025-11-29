# 自动监控服务器测试执行并反馈
# 持续检查直到所有任务完成

$Server = "ubuntu@165.154.233.55"
$MaxChecks = 200
$CheckInterval = 15

function Write-Status {
    param($Message, $Type = "Info")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $colors = @{
        "Success" = "Green"
        "Error" = "Red"
        "Warning" = "Yellow"
        "Info" = "Cyan"
    }
    $color = $colors[$Type]
    Write-Host "[$timestamp] $Message" -ForegroundColor $color
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "自动监控系统启动" -ForegroundColor Cyan
Write-Host "开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 准备阶段
Write-Status "准备环境..." "Info"
$result = ssh $Server "cd ~/liaotian/saas-demo && git pull origin master 2>&1"
$result = ssh $Server "cd ~/liaotian/saas-demo && chmod +x *.sh 2>&1"
Write-Status "环境准备完成" "Success"
Write-Host ""

# 检查后端服务
Write-Status "检查后端服务..." "Info"
$health = ssh $Server "curl -s http://localhost:8000/health 2>&1"
if ($health -match "ok|status") {
    Write-Status "后端服务正常" "Success"
} else {
    Write-Status "后端服务未运行，脚本会等待或提示" "Warning"
}
Write-Host ""

# 启动测试
Write-Status "启动测试任务..." "Info"
$startResult = ssh $Server "cd ~/liaotian/saas-demo && nohup bash 简化执行-分步进行.sh > ~/liaotian/test_logs/ps_auto_run.log 2>&1 & echo `$!"
Write-Status "测试已启动" "Success"
Write-Host ""

# 持续监控
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "开始持续监控（每 $CheckInterval 秒检查）" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$checkCount = 0
$lastLogContent = ""

while ($checkCount -lt $MaxChecks) {
    $checkCount++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] 检查 #$checkCount" -ForegroundColor Cyan
    
    # 获取日志文件
    $logFile = ssh $Server "ls -t ~/liaotian/test_logs/ps_auto_run.log 2>/dev/null | head -1"
    $logFile = $logFile.Trim()
    
    if ($logFile) {
        # 获取最新日志内容
        $logContent = ssh $Server "tail -50 '$logFile' 2>/dev/null"
        
        if ($logContent -ne $lastLogContent) {
            # 日志有更新
            $newLines = Compare-Object ($lastLogContent -split "`n") ($logContent -split "`n") | Where-Object {$_.SideIndicator -eq "=>"} | Select-Object -ExpandProperty InputObject
            
            if ($newLines) {
                foreach ($line in $newLines[-5..-1]) {
                    if ($line -and $line.Trim()) {
                        Write-Host "  $line" -ForegroundColor Gray
                    }
                }
            }
            
            $lastLogContent = $logContent
        }
        
        # 检查是否完成
        if ($logContent -match "所有任务成功完成|所有测试通过|✅.*成功|测试.*成功") {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "✅ 所有任务成功完成！" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
            
            Write-Host "最终日志:" -ForegroundColor Yellow
            Write-Host "----------------------------------------" -ForegroundColor Gray
            $finalLog = ssh $Server "tail -30 '$logFile' 2>/dev/null"
            Write-Host $finalLog
            Write-Host "----------------------------------------" -ForegroundColor Gray
            
            exit 0
        }
        elseif ($logContent -match "测试失败|❌.*失败|错误|error|failed") {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Red
            Write-Host "❌ 测试失败，尝试修复..." -ForegroundColor Red
            Write-Host "========================================" -ForegroundColor Red
            
            # 修复并重启
            Write-Status "修复测试用户..." "Info"
            ssh $Server "cd ~/liaotian/admin-backend && source .venv/bin/activate && export ADMIN_DEFAULT_PASSWORD=testpass123 && python reset_admin_user.py 2>&1" | Out-Null
            Start-Sleep -Seconds 2
            
            Write-Status "重新启动测试..." "Info"
            ssh $Server "cd ~/liaotian/saas-demo && nohup bash 简化执行-分步进行.sh > ~/liaotian/test_logs/ps_auto_run.log 2>&1 &" | Out-Null
            Start-Sleep -Seconds 5
            $lastLogContent = ""
        }
        else {
            # 显示进度
            $lastLine = ($logContent -split "`n") | Where-Object {$_.Trim()} | Select-Object -Last 1
            if ($lastLine) {
                $displayLine = $lastLine.Substring(0, [Math]::Min(70, $lastLine.Length))
                Write-Host "  进度: $displayLine..." -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "  等待日志文件..." -ForegroundColor Gray
    }
    
    Write-Host ""
    Start-Sleep -Seconds $CheckInterval
}

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "⚠️  达到最大检查次数" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$finalLog = ssh $Server "ls -t ~/liaotian/test_logs/ps_auto_run.log 2>/dev/null | head -1"
if ($finalLog) {
    Write-Host "`n查看日志: $($finalLog.Trim())" -ForegroundColor Yellow
    $logContent = ssh $Server "tail -50 '$($finalLog.Trim())' 2>/dev/null"
    Write-Host $logContent
}

exit 1
