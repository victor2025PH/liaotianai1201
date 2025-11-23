# 檢查服務狀態

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "服務狀態檢查" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "E:\002-工作文件\重要程序\聊天AI群聊程序"

# 檢查進程
Write-Host "運行中的進程:" -ForegroundColor Yellow
$pythonProcesses = Get-Process | Where-Object {$_.ProcessName -eq "python"} -ErrorAction SilentlyContinue
$nodeProcesses = Get-Process | Where-Object {$_.ProcessName -eq "node"} -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Host "  Python進程: $($pythonProcesses.Count) 個" -ForegroundColor Green
    $pythonProcesses | ForEach-Object {
        Write-Host "    PID: $($_.Id), CPU: $($_.CPU), 內存: $([math]::Round($_.WorkingSet64/1MB,2))MB" -ForegroundColor Gray
    }
} else {
    Write-Host "  Python進程: 無" -ForegroundColor Red
}

if ($nodeProcesses) {
    Write-Host "  Node進程: $($nodeProcesses.Count) 個" -ForegroundColor Green
    $nodeProcesses | ForEach-Object {
        Write-Host "    PID: $($_.Id), CPU: $($_.CPU), 內存: $([math]::Round($_.WorkingSet64/1MB,2))MB" -ForegroundColor Gray
    }
} else {
    Write-Host "  Node進程: 無" -ForegroundColor Red
}

Write-Host ""

# 檢查端口
Write-Host "端口占用情況:" -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue

if ($port8000) {
    $pid8000 = $port8000.OwningProcess
    $process8000 = Get-Process -Id $pid8000 -ErrorAction SilentlyContinue
    Write-Host "  端口8000: 被PID $pid8000 占用 ($($process8000.ProcessName))" -ForegroundColor Green
} else {
    Write-Host "  端口8000: 未被占用" -ForegroundColor Red
}

if ($port3000) {
    $pid3000 = $port3000.OwningProcess
    $process3000 = Get-Process -Id $pid3000 -ErrorAction SilentlyContinue
    Write-Host "  端口3000: 被PID $pid3000 占用 ($($process3000.ProcessName))" -ForegroundColor Green
} else {
    Write-Host "  端口3000: 未被占用" -ForegroundColor Red
}

Write-Host ""

# 測試服務可訪問性
Write-Host "服務可訪問性測試:" -ForegroundColor Yellow

# 測試後端
Write-Host "  後端服務 (http://localhost:8000)..." -ForegroundColor Gray -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host " [OK]" -ForegroundColor Green
    Write-Host "    響應: $($response.Content)" -ForegroundColor DarkGray
} catch {
    Write-Host " [FAIL]" -ForegroundColor Red
    Write-Host "    錯誤: $_" -ForegroundColor DarkGray
}

# 測試前端
Write-Host "  前端服務 (http://localhost:3000)..." -ForegroundColor Gray -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host " [OK]" -ForegroundColor Green
    Write-Host "    狀態碼: $($response.StatusCode)" -ForegroundColor DarkGray
} catch {
    Write-Host " [FAIL]" -ForegroundColor Red
    Write-Host "    錯誤: $_" -ForegroundColor DarkGray
    Write-Host "    提示: 前端服務可能需要30-60秒才能完全啟動" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "檢查完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "如果服務無法訪問，請執行:" -ForegroundColor Yellow
Write-Host "  .\scripts\test\fix_and_start_services.ps1" -ForegroundColor Cyan

