# 快速測試腳本 (PowerShell)
# 用於快速檢查系統狀態

Write-Host "`n=== 系統狀態檢查 ===" -ForegroundColor Cyan
Write-Host ""

# 檢查後端
Write-Host "[1/3] 檢查後端服務..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ 後端服務正常運行 (http://localhost:8000)" -ForegroundColor Green
    } else {
        Write-Host "❌ 後端響應異常: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ 後端服務未運行或無法連接" -ForegroundColor Red
    Write-Host "   請運行: cd admin-backend; py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor Yellow
}

# 檢查前端
Write-Host "`n[2/3] 檢查前端服務..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ 前端服務正常運行 (http://localhost:3000)" -ForegroundColor Green
    } else {
        Write-Host "❌ 前端響應異常: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ 前端服務未運行或無法連接" -ForegroundColor Red
    Write-Host "   請運行: cd saas-demo; npm run dev" -ForegroundColor Yellow
}

# 檢查環境
Write-Host "`n[3/3] 檢查環境配置..." -ForegroundColor Yellow
$rootDir = Get-Location
if (Test-Path ".env") {
    Write-Host "✅ 找到 .env 文件" -ForegroundColor Green
} else {
    Write-Host "⚠️  未找到 .env 文件" -ForegroundColor Yellow
}

if (Test-Path "sessions") {
    $sessionFiles = Get-ChildItem "sessions" -Filter "*.session" -ErrorAction SilentlyContinue
    if ($sessionFiles) {
        Write-Host "✅ 找到 $($sessionFiles.Count) 個 session 文件" -ForegroundColor Green
    } else {
        Write-Host "⚠️  sessions 目錄中沒有 .session 文件" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  sessions 目錄不存在" -ForegroundColor Yellow
}

Write-Host "`n=== 檢查完成 ===" -ForegroundColor Cyan
Write-Host ""

