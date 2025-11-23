# 服务监控脚本
# 实时监控前后端服务的日志输出

$backendLog = "admin-backend\backend_stdout.log"
$backendErrLog = "admin-backend\backend_stderr.log"
$frontendLog = "admin-frontend\frontend_stdout.log"
$frontendErrLog = "admin-frontend\frontend_stderr.log"

Write-Host "=== 服务监控开始 ===" -ForegroundColor Green
Write-Host "按 Ctrl+C 停止监控`n" -ForegroundColor Yellow

$backendLastSize = 0
$frontendLastSize = 0

while ($true) {
    # 检查后端日志
    if (Test-Path $backendLog) {
        $currentSize = (Get-Item $backendLog).Length
        if ($currentSize -gt $backendLastSize) {
            $newContent = Get-Content $backendLog -Tail 10 -ErrorAction SilentlyContinue
            if ($newContent) {
                Write-Host "`n[后端] $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
                $newContent | ForEach-Object { Write-Host "  $_" }
            }
            $backendLastSize = $currentSize
        }
    }
    
    if (Test-Path $backendErrLog) {
        $errContent = Get-Content $backendErrLog -Tail 5 -ErrorAction SilentlyContinue
        if ($errContent) {
            Write-Host "`n[后端错误] $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Red
            $errContent | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        }
    }
    
    # 检查前端日志
    if (Test-Path $frontendLog) {
        $currentSize = (Get-Item $frontendLog).Length
        if ($currentSize -gt $frontendLastSize) {
            $newContent = Get-Content $frontendLog -Tail 10 -ErrorAction SilentlyContinue
            if ($newContent) {
                Write-Host "`n[前端] $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Magenta
                $newContent | ForEach-Object { Write-Host "  $_" }
            }
            $frontendLastSize = $currentSize
        }
    }
    
    if (Test-Path $frontendErrLog) {
        $errContent = Get-Content $frontendErrLog -Tail 5 -ErrorAction SilentlyContinue
        if ($errContent) {
            Write-Host "`n[前端错误] $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Red
            $errContent | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        }
    }
    
    Start-Sleep -Seconds 2
}

