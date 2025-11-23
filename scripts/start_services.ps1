# Telegram 群組 AI 系統啟動腳本 (PowerShell)
# 使用方法: .\scripts\start_services.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Telegram 群組 AI 系統啟動腳本" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 獲取項目根目錄
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "admin-backend"
$frontendDir = Join-Path $projectRoot "saas-demo"

# 檢查目錄
if (-not (Test-Path $backendDir)) {
    Write-Host "[錯誤] 後端目錄不存在: $backendDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $frontendDir)) {
    Write-Host "[錯誤] 前端目錄不存在: $frontendDir" -ForegroundColor Red
    exit 1
}

# 檢查依賴
Write-Host "檢查依賴..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "  Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  [錯誤] Node.js 未安裝或不在 PATH 中" -ForegroundColor Red
    exit 1
}

try {
    $npmVersion = npm --version
    Write-Host "  npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "  [錯誤] npm 未安裝或不在 PATH 中" -ForegroundColor Red
    exit 1
}

# 啟動後端服務
Write-Host "`n啟動後端服務..." -ForegroundColor Yellow
$backendProcess = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$backendDir'; Write-Host '後端服務啟動中...' -ForegroundColor Cyan; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
) -PassThru -WindowStyle Normal

Write-Host "  後端服務啟動中... (PID: $($backendProcess.Id))" -ForegroundColor Green

# 等待後端啟動
Start-Sleep -Seconds 5

# 啟動前端服務
Write-Host "`n啟動前端服務..." -ForegroundColor Yellow
$frontendProcess = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$frontendDir'; Write-Host '前端服務啟動中...' -ForegroundColor Cyan; `$env:PORT = '3000'; npm run dev"
) -PassThru -WindowStyle Normal

Write-Host "  前端服務啟動中... (PID: $($frontendProcess.Id))" -ForegroundColor Green

# 等待前端啟動
Start-Sleep -Seconds 5

# 檢查服務狀態
Write-Host "`n檢查服務狀態..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

$backendOk = $false
$frontendOk = $false

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
    $backendOk = $true
    Write-Host "  [OK] 後端服務已啟動: http://localhost:8000" -ForegroundColor Green
} catch {
    Write-Host "  [警告] 後端服務可能還在啟動中..." -ForegroundColor Yellow
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
    $frontendOk = $true
    Write-Host "  [OK] 前端服務已啟動: http://localhost:3000" -ForegroundColor Green
} catch {
    Write-Host "  [警告] 前端服務可能還在啟動中..." -ForegroundColor Yellow
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  服務啟動完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "後端 API:  http://localhost:8000" -ForegroundColor White
Write-Host "前端界面: http://localhost:3000" -ForegroundColor White
Write-Host "API 文檔: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "服務已在獨立的 PowerShell 窗口中運行" -ForegroundColor Yellow
Write-Host "關閉那些窗口即可停止服務" -ForegroundColor Yellow
Write-Host ""

