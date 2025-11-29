# 持续检查服务器状态直到所有任务完成

$Server = "ubuntu@165.154.233.55"
$CheckInterval = 15
$MaxChecks = 400

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "持续检查服务器状态" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$checkCount = 0
$lastContent = ""

while ($checkCount -lt $MaxChecks) {
    $checkCount++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] 检查 #$checkCount" -ForegroundColor Cyan
    
    # 获取日志内容
    $logContent = ssh $Server "tail -100 ~/liaotian/test_logs/direct_exec.log 2>/dev/null || echo ''"
    
    if ($logContent -and $logContent -ne $lastContent) {
        # 显示新内容
        $diff = if ($lastContent) {
            $lines1 = $lastContent -split "`n"
            $lines2 = $logContent -split "`n"
            $lines2[$lines1.Count..($lines2.Count-1)] -join "`n"
        } else {
            $logContent
        }
        
        if ($diff) {
            $lines = $diff -split "`n"
            foreach ($line in $lines) {
                if ($line.Trim()) {
                    if ($line -match '✅|成功|通过|SUCCESS') {
                        Write-Host "  $line" -ForegroundColor Green
                    } elseif ($line -match '❌|失败|错误|ERROR') {
                        Write-Host "  $line" -ForegroundColor Red
                    } else {
                        Write-Host "  $line" -ForegroundColor Gray
                    }
                }
            }
        }
        
        $lastContent = $logContent
        
        # 检查完成
        if ($logContent -match "所有任务完成|所有测试通过|✅.*成功") {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "✅ 所有任务成功完成！" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
            Write-Host $logContent
            exit 0
        }
    } else {
        Write-Host "  等待日志内容..." -ForegroundColor Gray
    }
    
    Write-Host ""
    Start-Sleep -Seconds $CheckInterval
}

Write-Host "达到最大检查次数" -ForegroundColor Yellow
exit 1
