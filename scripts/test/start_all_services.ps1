# 啟動所有服務的PowerShell腳本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "啟動所有服務" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "E:\002-工作文件\重要程序\聊天AI群聊程序"

# 1. 啟動後端服務
Write-Host "[1/3] 啟動後端服務..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot\admin-backend
    $env:PYTHONPATH = (Get-Location).Parent.FullName
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} -Name "BackendService"

Start-Sleep -Seconds 3
Write-Host "  後端服務已啟動 (PID: $($backendJob.Id))" -ForegroundColor Green
Write-Host "  地址: http://localhost:8000" -ForegroundColor Gray

# 2. 啟動前端服務
Write-Host "[2/3] 啟動前端服務..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot\saas-demo
    npm run dev
} -Name "FrontendService"

Start-Sleep -Seconds 5
Write-Host "  前端服務已啟動 (PID: $($frontendJob.Id))" -ForegroundColor Green
Write-Host "  地址: http://localhost:3000" -ForegroundColor Gray

# 3. 檢查服務狀態
Write-Host "[3/3] 檢查服務狀態..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 檢查後端
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  [OK] 後端服務正常運行" -ForegroundColor Green
    }
} catch {
    Write-Host "  [WARN] 後端服務可能還在啟動中..." -ForegroundColor Yellow
}

# 檢查前端
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  [OK] 前端服務正常運行" -ForegroundColor Green
    }
} catch {
    Write-Host "  [WARN] 前端服務可能還在啟動中..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "服務啟動完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "訪問地址:" -ForegroundColor Yellow
Write-Host "  後端API: http://localhost:8000" -ForegroundColor White
Write-Host "  前端頁面: http://localhost:3000" -ForegroundColor White
Write-Host "  服務器管理: http://localhost:3000/group-ai/servers" -ForegroundColor White
Write-Host ""
Write-Host "查看服務狀態:" -ForegroundColor Yellow
Write-Host "  Get-Job" -ForegroundColor White
Write-Host ""
Write-Host "停止服務:" -ForegroundColor Yellow
Write-Host "  Stop-Job -Name BackendService,FrontendService" -ForegroundColor White
Write-Host "  Remove-Job -Name BackendService,FrontendService" -ForegroundColor White

