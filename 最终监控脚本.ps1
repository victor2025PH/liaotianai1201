# 最终监控脚本 - 持续检查直到所有任务完成

$Server = "ubuntu@165.154.233.55"
$MaxChecks = 500  # 最多检查约2小时
$CheckInterval = 10

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "最终自动监控系统" -ForegroundColor Cyan
Write-Host "开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Invoke-SSH {
    param($Cmd)
    try {
        $result = ssh $Server $Cmd 2>&1
        return $result -join "`n"
    } catch {
        return ""
    }
}

# 准备并启动
Write-Host "[启动] 准备并启动测试..." -ForegroundColor Yellow
Invoke-SSH "cd ~/liaotian/saas-demo && git pull origin master > /dev/null 2>&1" | Out-Null
Invoke-SSH "cd ~/liaotian/saas-demo && chmod +x 直接执行并反馈.sh && nohup bash 直接执行并反馈.sh > ~/liaotian/test_logs/final_run.log 2>&1 &" | Out-Null
Start-Sleep -Seconds 5
Write-Host "✅ 测试已启动" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "开始持续监控" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$checkCount = 0
$lastSize = 0
$consecutiveEmpty = 0

while ($checkCount -lt $MaxChecks) {
    $checkCount++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] 检查 #$checkCount" -ForegroundColor Cyan
    
    # 获取日志
    $logContent = Invoke-SSH "cat ~/liaotian/test_logs/final_run.log 2>/dev/null || echo ''"
    
    if ($logContent) {
        $currentSize = $logContent.Length
        
        if ($currentSize -ne $lastSize) {
            # 显示新内容
            $newContent = if ($currentSize -gt $lastSize) {
                $logContent.Substring($lastSize)
            } else {
                $logContent
            }
            
            if ($newContent) {
                $lines = $newContent -split "`n"
                foreach ($line in $lines) {
                    if ($line.Trim()) {
                        Write-Host "  $line"
                    }
                }
            }
            
            $lastSize = $currentSize
            $consecutiveEmpty = 0
        }
        
        # 检查完成
        if ($logContent -match "所有任务完成|所有测试通过|✅.*成功|测试.*成功") {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "✅ 所有任务成功完成！" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
            Write-Host $logContent
            exit 0
        }
        elseif ($logContent -match "测试失败|❌|错误|error|failed") {
            Write-Host ""
            Write-Host "检测到错误，尝试修复..." -ForegroundColor Yellow
            
            # 修复
            Invoke-SSH "cd ~/liaotian/admin-backend && source .venv/bin/activate && export ADMIN_DEFAULT_PASSWORD=testpass123 && python reset_admin_user.py > /dev/null 2>&1" | Out-Null
            Start-Sleep -Seconds 2
            
            # 重启
            Invoke-SSH "cd ~/liaotian/saas-demo && nohup bash 直接执行并反馈.sh > ~/liaotian/test_logs/final_run.log 2>&1 &" | Out-Null
            Start-Sleep -Seconds 5
            
            $lastSize = 0
            Write-Host ""
        }
    } else {
        $consecutiveEmpty++
        if ($consecutiveEmpty -lt 10) {
            Write-Host "  等待日志生成..." -ForegroundColor Gray
        } else {
            # 长时间没有日志，可能脚本未启动，重新启动
            Write-Host "  长时间无日志，重新启动..." -ForegroundColor Yellow
            Invoke-SSH "cd ~/liaotian/saas-demo && nohup bash 直接执行并反馈.sh > ~/liaotian/test_logs/final_run.log 2>&1 &" | Out-Null
            Start-Sleep -Seconds 5
            $consecutiveEmpty = 0
        }
    }
    
    Write-Host ""
    Start-Sleep -Seconds $CheckInterval
}

Write-Host "达到最大检查次数" -ForegroundColor Yellow
$finalLog = Invoke-SSH "cat ~/liaotian/test_logs/final_run.log 2>/dev/null"
if ($finalLog) {
    Write-Host "`n最终日志:"
    Write-Host $finalLog
}

exit 1
