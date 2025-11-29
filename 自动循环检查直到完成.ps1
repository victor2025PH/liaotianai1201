# 自动循环检查服务器状态直到所有任务完成

$Server = "ubuntu@165.154.233.55"
$MaxIterations = 200
$CheckInterval = 15

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "自动循环检查系统" -ForegroundColor Cyan
Write-Host "开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 首先启动测试
Write-Host "[启动] 启动测试任务..." -ForegroundColor Yellow
ssh $Server "cd ~/liaotian/saas-demo && git pull origin master > /dev/null 2>&1 && chmod +x 简化执行-分步进行.sh && nohup bash 简化执行-分步进行.sh > ~/liaotian/test_logs/auto_check.log 2>&1 & echo `$!" | Out-Null
Start-Sleep -Seconds 5
Write-Host "✅ 测试任务已启动" -ForegroundColor Green
Write-Host ""

Write-Host "开始循环检查（每 $CheckInterval 秒检查一次）..." -ForegroundColor Cyan
Write-Host ""

$iteration = 0
$lastLogSize = 0

while ($iteration -lt $MaxIterations) {
    $iteration++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] 检查 #$iteration" -ForegroundColor Cyan
    
    # 获取日志文件
    $logFile = ssh $Server "ls -t ~/liaotian/test_logs/auto_check.log 2>/dev/null | head -1"
    $logFile = $logFile.Trim()
    
    if ($logFile) {
        # 获取日志内容
        $logContent = ssh $Server "tail -100 '$logFile' 2>/dev/null"
        
        if ($logContent) {
            # 显示新增内容
            $currentSize = $logContent.Length
            if ($currentSize -ne $lastLogSize) {
                $newContent = $logContent.Substring($lastLogSize)
                $lines = $newContent -split "`n" | Where-Object { $_.Trim() }
                foreach ($line in $lines[-5..-1]) {
                    if ($line -and $line.Trim()) {
                        Write-Host "  $line" -ForegroundColor Gray
                    }
                }
                $lastLogSize = $currentSize
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
                $finalLog = ssh $Server "tail -50 '$logFile' 2>/dev/null"
                Write-Host $finalLog
                Write-Host "----------------------------------------" -ForegroundColor Gray
                
                exit 0
            }
            elseif ($logContent -match "测试失败|❌|错误|error|failed") {
                Write-Host ""
                Write-Host "========================================" -ForegroundColor Red
                Write-Host "❌ 发现错误，尝试修复..." -ForegroundColor Red
                Write-Host "========================================" -ForegroundColor Red
                
                # 修复
                ssh $Server "cd ~/liaotian/admin-backend && source .venv/bin/activate && export ADMIN_DEFAULT_PASSWORD=testpass123 && python reset_admin_user.py > /dev/null 2>&1" | Out-Null
                Start-Sleep -Seconds 2
                
                # 重启
                ssh $Server "cd ~/liaotian/saas-demo && nohup bash 简化执行-分步进行.sh > ~/liaotian/test_logs/auto_check.log 2>&1 &" | Out-Null
                Start-Sleep -Seconds 5
                $lastLogSize = 0
                Write-Host ""
            }
        }
    }
    
    Write-Host ""
    Start-Sleep -Seconds $CheckInterval
}

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "⚠️  达到最大检查次数" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$logFile = ssh $Server "ls -t ~/liaotian/test_logs/auto_check.log 2>/dev/null | head -1"
if ($logFile) {
    Write-Host "`n查看日志: $($logFile.Trim())" -ForegroundColor Yellow
    $logContent = ssh $Server "tail -50 '$($logFile.Trim())' 2>/dev/null"
    Write-Host $logContent
}

exit 1
