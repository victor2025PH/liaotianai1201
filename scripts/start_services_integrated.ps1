# Telegram 群組 AI 系統啟動腳本 (用於 Cursor 集成終端)
# 使用方法: 在 Cursor 終端中運行: .\scripts\start_services_integrated.ps1
# 或者: cd scripts; .\start_services_integrated.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Telegram 群組 AI 系統啟動腳本 (集成終端版本)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 獲取項目根目錄
$scriptPath = $PSScriptRoot
if (-not $scriptPath) {
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$projectRoot = Split-Path -Parent $scriptPath
$backendDir = Join-Path $projectRoot "admin-backend"
$frontendDir = Join-Path $projectRoot "saas-demo"
$adminFrontendDir = Join-Path $projectRoot "admin-frontend"

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

try {
    $pythonVersion = python --version
    Write-Host "  Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [錯誤] Python 未安裝或不在 PATH 中" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  提示: 服務將在當前終端中以後台任務運行" -ForegroundColor Yellow
Write-Host "  要停止服務，請按 Ctrl+C 或關閉終端" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 啟動後端服務（後台任務）
Write-Host "[1/3] 啟動後端服務..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:backendDir
    $env:PYTHONPATH = (Get-Location).Parent.FullName
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} -Name "BackendService"

Write-Host "  後端服務已啟動 (Job ID: $($backendJob.Id))" -ForegroundColor Green
Write-Host "  地址: http://localhost:8000" -ForegroundColor Gray

# 等待後端啟動
Start-Sleep -Seconds 3

# 啟動前端服務（後台任務）
Write-Host "[2/3] 啟動前端服務..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:frontendDir
    $env:PORT = '3000'
    npm run dev
} -Name "FrontendService"

Write-Host "  前端服務已啟動 (Job ID: $($frontendJob.Id))" -ForegroundColor Green
Write-Host "  地址: http://localhost:3000" -ForegroundColor Gray

# 等待前端啟動
Start-Sleep -Seconds 5

# 檢查服務狀態
Write-Host "[3/3] 檢查服務狀態..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

$backendOk = $false
$frontendOk = $false

# 檢查後端
for ($i = 0; $i -lt 5; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "  [OK] 後端服務正常運行" -ForegroundColor Green
            $backendOk = $true
            break
        }
    } catch {
        if ($i -eq 4) {
            Write-Host "  [警告] 後端服務可能還在啟動中..." -ForegroundColor Yellow
        } else {
            Start-Sleep -Seconds 2
        }
    }
}

# 檢查前端
for ($i = 0; $i -lt 5; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "  [OK] 前端服務正常運行" -ForegroundColor Green
            $frontendOk = $true
            break
        }
    } catch {
        if ($i -eq 4) {
            Write-Host "  [警告] 前端服務可能還在啟動中..." -ForegroundColor Yellow
        } else {
            Start-Sleep -Seconds 2
        }
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  服務啟動完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "後端 API:  http://localhost:8000" -ForegroundColor White
Write-Host "前端界面: http://localhost:3000" -ForegroundColor White
Write-Host "API 文檔: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "服務正在後台運行..." -ForegroundColor Yellow
Write-Host ""
Write-Host "查看服務日誌:" -ForegroundColor Cyan
Write-Host "  Get-Job | Receive-Job -Keep" -ForegroundColor Gray
Write-Host ""
Write-Host "查看特定服務日誌:" -ForegroundColor Cyan
Write-Host "  Receive-Job -Name BackendService -Keep" -ForegroundColor Gray
Write-Host "  Receive-Job -Name FrontendService -Keep" -ForegroundColor Gray
Write-Host ""
Write-Host "停止服務:" -ForegroundColor Cyan
Write-Host "  Stop-Job -Name BackendService,FrontendService" -ForegroundColor Gray
Write-Host "  Remove-Job -Name BackendService,FrontendService" -ForegroundColor Gray
Write-Host ""
Write-Host "按任意鍵查看實時日誌，或按 Ctrl+C 退出..." -ForegroundColor Yellow

# 等待用戶輸入或 Ctrl+C
try {
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Write-Host ""
    Write-Host "顯示服務日誌 (按 Ctrl+C 停止)..." -ForegroundColor Cyan
    Write-Host ""
    
    # 持續顯示日誌
    while ($true) {
        Get-Job | Receive-Job -Keep
        Start-Sleep -Seconds 1
    }
} catch {
    Write-Host ""
    Write-Host "正在停止服務..." -ForegroundColor Yellow
    Stop-Job -Name BackendService,FrontendService -ErrorAction SilentlyContinue
    Remove-Job -Name BackendService,FrontendService -ErrorAction SilentlyContinue
    Write-Host "服務已停止" -ForegroundColor Green
}

