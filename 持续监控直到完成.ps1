# 持续监控直到所有任务完成
$Server = "ubuntu@165.154.233.55"
$OutputFile = "monitor_output.txt"
$MaxWait = 3600  # 最多等待1小时
$CheckInterval = 10

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "持续监控系统" -ForegroundColor Cyan
Write-Host "开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 启动测试
Write-Host "[启动] 启动测试任务..." -ForegroundColor Yellow

# 使用后台任务并重定向输出
$job = Start-Job -ScriptBlock {
    param($server)
    ssh $server "cd ~/liaotian/saas-demo && git pull origin master && chmod +x 简化执行-分步进行.sh && bash 简化执行-分步进行.sh 2>&1"
} -ArgumentList $Server

Write-Host "✅ 测试任务已启动 (Job ID: $($job.Id))" -ForegroundColor Green
Write-Host ""

# 持续监控
Write-Host "开始监控（每 $CheckInterval 秒检查一次）..." -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date
$lastOutput = ""

while (((Get-Date) - $startTime).TotalSeconds -lt $MaxWait) {
    # 获取任务输出
    $output = Receive-Job -Job $job -Keep
    
    if ($output -ne $lastOutput) {
        $newOutput = $output | Select-Object -Last 10
        foreach ($line in $newOutput) {
            if ($line -and $line.Trim()) {
                Write-Host "  $line" -ForegroundColor Gray
            }
        }
        $lastOutput = $output
    }
    
    # 检查任务状态
    $jobState = Get-Job -Id $job.Id | Select-Object -ExpandProperty State
    
    if ($jobState -eq "Completed") {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "任务已完成" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        
        # 获取最终输出
        $finalOutput = Receive-Job -Job $job
        
        Write-Host "完整输出:" -ForegroundColor Yellow
        Write-Host "----------------------------------------" -ForegroundColor Gray
        Write-Host $finalOutput
        Write-Host "----------------------------------------" -ForegroundColor Gray
        
        # 检查是否成功
        if ($finalOutput -match "所有任务成功完成|所有测试通过|✅.*成功") {
            Write-Host ""
            Write-Host "✅ 所有任务成功完成！" -ForegroundColor Green
            Remove-Job -Job $job
            exit 0
        } else {
            Write-Host ""
            Write-Host "❌ 任务失败或状态未知" -ForegroundColor Red
            Remove-Job -Job $job
            exit 1
        }
    }
    elseif ($jobState -eq "Failed") {
        Write-Host ""
        Write-Host "❌ 任务执行失败" -ForegroundColor Red
        $errorOutput = Receive-Job -Job $job -Error
        Write-Host $errorOutput
        Remove-Job -Job $job
        exit 1
    }
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] 监控中... (任务状态: $jobState)" -ForegroundColor Cyan
    
    Start-Sleep -Seconds $CheckInterval
}

Write-Host ""
Write-Host "⚠️  达到最大等待时间" -ForegroundColor Yellow
$finalOutput = Receive-Job -Job $job
Write-Host $finalOutput
Remove-Job -Job $job
exit 1
