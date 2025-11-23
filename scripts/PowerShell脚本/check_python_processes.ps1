# 检查所有Python进程
Write-Host "检查所有Python进程..." -ForegroundColor Yellow
Write-Host ""

$processes = Get-Process -Name "python" -ErrorAction SilentlyContinue

if ($processes) {
    Write-Host "找到 $($processes.Count) 个Python进程:" -ForegroundColor Green
    Write-Host ""
    
    foreach ($proc in $processes) {
        Write-Host "PID: $($proc.Id)" -ForegroundColor Cyan
        Write-Host "  启动时间: $($proc.StartTime)"
        Write-Host "  内存使用: $([math]::Round($proc.WorkingSet64 / 1MB, 2)) MB"
        
        # 尝试获取命令行
        $cmdline = $null
        try {
            $wmiProc = Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue
            if ($wmiProc) {
                $cmdline = $wmiProc.CommandLine
            }
        } catch {
            # 忽略错误
        }
        
        if ($cmdline) {
            $shortCmd = if ($cmdline.Length -gt 150) { $cmdline.Substring(0, 150) + "..." } else { $cmdline }
            Write-Host "  命令行: $shortCmd"
            
            # 检查是否与session相关
            if ($cmdline -match "session|main\.py|uvicorn|account") {
                Write-Host "  [警告] 此进程可能与session文件相关！" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  命令行: 无法获取"
        }
        Write-Host ""
    }
} else {
    Write-Host "未找到Python进程" -ForegroundColor Green
}

Write-Host ""
Write-Host "建议:" -ForegroundColor Yellow
Write-Host "  1. 如果发现与session相关的进程，停止它们"
Write-Host "  2. 等待5-10分钟让Telegram服务器端释放session"
Write-Host "  3. 或使用新的session文件"
