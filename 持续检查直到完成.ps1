# 持续检查服务器状态直到所有任务完成

$Server = "ubuntu@165.154.233.55"
$MaxIterations = 300
$CheckInterval = 15

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "持续检查监控系统" -ForegroundColor Cyan
Write-Host "开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Get-LatestLog {
    $output = ssh $Server "ls -t ~/liaotian/test_logs/realtime_monitor_*.log 2>/dev/null | head -1"
    return $output.Trim()
}

function Get-LogTail {
    param($LogFile, $Lines = 50)
    if (-not $LogFile) { return "" }
    $output = ssh $Server "tail -$Lines '$LogFile' 2>/dev/null"
    return $output
}

function Get-Status {
    $output = ssh $Server "cat ~/liaotian/test_logs/current_status.txt 2>/dev/null || echo ''"
    return $output.Trim()
}

$iteration = 0
$lastLogPosition = 0
$lastLogFile = ""

while ($iteration -lt $MaxIterations) {
    $iteration++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] 检查 #$iteration" -ForegroundColor Cyan
    
    # 获取状态
    $status = Get-Status
    if ($status) {
        Write-Host "  当前状态: $status" -ForegroundColor Gray
    }
    
    # 获取日志文件
    $logFile = Get-LatestLog
    
    if ($logFile) {
        if ($logFile -ne $lastLogFile) {
            Write-Host "  日志文件: $([System.IO.Path]::GetFileName($logFile))" -ForegroundColor Gray
            $lastLogFile = $logFile
            $lastLogPosition = 0
        }
        
        # 获取日志内容
        $logContent = Get-LogTail $logFile 100
        
        if ($logContent) {
            $lines = $logContent -split "`n"
            
            # 显示新行
            if ($lines.Count -gt $lastLogPosition) {
                $newLines = $lines[$lastLogPosition..($lines.Count - 1)]
                foreach ($line in $newLines) {
                    if ($line.Trim()) {
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
            
            # 检查完成状态
            if ($logContent -match "所有任务成功完成|所有测试通过|✅.*成功|测试.*成功") {
                Write-Host ""
                Write-Host "========================================" -ForegroundColor Green
                Write-Host "✅ 所有任务成功完成！" -ForegroundColor Green
                Write-Host "========================================" -ForegroundColor Green
                Write-Host ""
                
                $finalLog = Get-LogTail $logFile 50
                if ($finalLog) {
                    Write-Host "最终日志摘要:"
                    Write-Host "----------------------------------------"
                    Write-Host $finalLog
                    Write-Host "----------------------------------------"
                }
                
                exit 0
            }
            elseif ($logContent -match "测试失败|❌.*失败|错误|error|failed") {
                Write-Host ""
                Write-Host "检测到错误，检查是否需要修复..." -ForegroundColor Yellow
                
                # 检查是否需要修复
                if ($logContent -match "auth|login|unauthorized") {
                    Write-Host "修复认证问题..." -ForegroundColor Yellow
                    ssh $Server "cd ~/liaotian/admin-backend && source .venv/bin/activate && export ADMIN_DEFAULT_PASSWORD=testpass123 && python reset_admin_user.py > /dev/null 2>&1" | Out-Null
                    Start-Sleep -Seconds 2
                }
                
                # 重新启动
                Write-Host "重新启动监控..." -ForegroundColor Yellow
                ssh $Server "pkill -f '服务器端实时监控执行.sh' 2>/dev/null || true" | Out-Null
                Start-Sleep -Seconds 2
                ssh $Server "cd ~/liaotian/saas-demo && nohup bash 服务器端实时监控执行.sh > /dev/null 2>&1 &" | Out-Null
                Start-Sleep -Seconds 5
                
                $lastLogPosition = 0
                $lastLogFile = ""
            }
        }
    } else {
        Write-Host "  等待日志文件..." -ForegroundColor Gray
    }
    
    Write-Host ""
    Start-Sleep -Seconds $CheckInterval
}

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "达到最大检查次数" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$logFile = Get-LatestLog
if ($logFile) {
    $finalLog = Get-LogTail $logFile 50
    Write-Host "`n最终日志:"
    Write-Host $finalLog
}

exit 1
