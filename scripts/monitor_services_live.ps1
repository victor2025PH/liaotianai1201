# 實時監控服務日誌和狀態
param(
    [int]$Interval = 10
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   服務監控腳本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "監控間隔: $Interval 秒" -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止監控`n" -ForegroundColor Yellow

$errorCount = 0
$successCount = 0

while ($true) {
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] 檢查服務狀態..." -ForegroundColor Gray
    
    # 檢查後端服務
    $backend = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue
    if ($backend.TcpTestSucceeded) {
        try {
            $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -UseBasicParsing
            Write-Host "[$timestamp] ✅ 後端服務正常" -ForegroundColor Green
            $successCount++
        } catch {
            Write-Host "[$timestamp] ❌ 後端服務響應錯誤: $($_.Exception.Message)" -ForegroundColor Red
            $errorCount++
        }
    } else {
        Write-Host "[$timestamp] ❌ 後端服務未運行" -ForegroundColor Red
        $errorCount++
    }
    
    # 檢查前端服務
    $frontend = Test-NetConnection -ComputerName localhost -Port 3000 -WarningAction SilentlyContinue
    if ($frontend.TcpTestSucceeded) {
        Write-Host "[$timestamp] ✅ 前端服務正常" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "[$timestamp] ❌ 前端服務未運行" -ForegroundColor Red
        $errorCount++
    }
    
    # 測試關鍵 API
    try {
        $accounts = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/group-ai/accounts/" -TimeoutSec 3 -UseBasicParsing
        Write-Host "[$timestamp] ✅ 帳號API正常" -ForegroundColor Green
        $successCount++
    } catch {
        Write-Host "[$timestamp] ⚠️  帳號API: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Start-Sleep -Seconds $Interval
}

