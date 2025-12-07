# PowerShell 腳本：自動執行所有部署準備任務
# 編碼：UTF-8

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 自動執行所有部署準備任務" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 切換到腳本所在目錄
Set-Location $PSScriptRoot

# 任務 1: 檢查安全配置
Write-Host "[1/3] 🔒 檢查安全配置..." -ForegroundColor Yellow
$securityCheck = & python scripts\check_security_config.py
$securityExitCode = $LASTEXITCODE

if ($securityExitCode -ne 0) {
    Write-Host ""
    Write-Host "⚠️  發現安全問題，正在設置生產環境安全配置..." -ForegroundColor Yellow
    Write-Host ""
    
    $setupResult = & python scripts\setup_production_security.py
    $setupExitCode = $LASTEXITCODE
    
    if ($setupExitCode -ne 0) {
        Write-Host "❌ 安全配置設置失敗" -ForegroundColor Red
        Read-Host "按 Enter 鍵退出"
        exit 1
    }
    
    Write-Host ""
    Write-Host "再次檢查安全配置..." -ForegroundColor Yellow
    & python scripts\check_security_config.py
}

Write-Host ""

# 任務 2: 檢查環境變量文檔
Write-Host "[2/3] 📋 檢查環境變量文檔..." -ForegroundColor Yellow
if (-not (Test-Path ".env.example")) {
    Write-Host "⚠️  .env.example 不存在" -ForegroundColor Yellow
    Write-Host "請參考 config\worker.env.example 創建 .env.example" -ForegroundColor Yellow
    Write-Host "或運行: Copy-Item config\worker.env.example .env.example" -ForegroundColor Yellow
} else {
    Write-Host "✅ .env.example 已存在" -ForegroundColor Green
}

Write-Host ""

# 任務 3: 前端功能驗證
Write-Host "[3/3] 🧪 前端功能驗證..." -ForegroundColor Yellow
Write-Host "注意：此步驟需要後端和前端服務都在運行" -ForegroundColor Yellow
Write-Host ""
& python scripts\auto_frontend_verification.py

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📊 任務執行完成" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "  1. 檢查上述輸出，確保所有檢查通過" -ForegroundColor White
Write-Host "  2. 如果安全配置有問題，請運行: python scripts\setup_production_security.py" -ForegroundColor White
Write-Host "  3. 完成前端手動驗證（參考：前端功能驗證清單.md）" -ForegroundColor White
Write-Host ""
Read-Host "按 Enter 鍵退出"

