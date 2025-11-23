# 修復並啟動所有服務

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "修復並啟動所有服務" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "E:\002-工作文件\重要程序\聊天AI群聊程序"

# 1. 停止所有現有服務
Write-Host "[1/5] 停止現有服務..." -ForegroundColor Yellow
Get-Job | Where-Object {$_.Name -like "*Service*"} | Stop-Job
Get-Job | Where-Object {$_.Name -like "*Service*"} | Remove-Job

# 停止可能運行的進程
$pythonProcesses = Get-Process | Where-Object {$_.ProcessName -eq "python" -and $_.CommandLine -like "*uvicorn*"} -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    $pythonProcesses | Stop-Process -Force
    Write-Host "  已停止現有Python進程" -ForegroundColor Green
}

$nodeProcesses = Get-Process | Where-Object {$_.ProcessName -eq "node"} -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    $nodeProcesses | Stop-Process -Force
    Write-Host "  已停止現有Node進程" -ForegroundColor Green
}

Start-Sleep -Seconds 2

# 2. 檢查端口占用
Write-Host "[2/5] 檢查端口占用..." -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue

if ($port8000) {
    Write-Host "  [WARN] 端口8000被占用，嘗試釋放..." -ForegroundColor Yellow
    $pid8000 = $port8000.OwningProcess
    Stop-Process -Id $pid8000 -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

if ($port3000) {
    Write-Host "  [WARN] 端口3000被占用，嘗試釋放..." -ForegroundColor Yellow
    $pid3000 = $port3000.OwningProcess
    Stop-Process -Id $pid3000 -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# 3. 啟動後端服務
Write-Host "[3/5] 啟動後端服務..." -ForegroundColor Yellow
Set-Location "$projectRoot\admin-backend"
$env:PYTHONPATH = (Get-Location).Parent.FullName

$backendProcess = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" -PassThru -WindowStyle Hidden

if ($backendProcess) {
    Write-Host "  後端服務已啟動 (PID: $($backendProcess.Id))" -ForegroundColor Green
    Write-Host "  地址: http://localhost:8000" -ForegroundColor Gray
} else {
    Write-Host "  [FAIL] 後端服務啟動失敗" -ForegroundColor Red
}

Start-Sleep -Seconds 5

# 4. 啟動前端服務
Write-Host "[4/5] 啟動前端服務..." -ForegroundColor Yellow
Set-Location "$projectRoot\saas-demo"

# 使用Start-Job啟動前端服務
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot\saas-demo
    npm run dev
} -Name "FrontendService"

if ($frontendJob) {
    Write-Host "  前端服務已啟動 (Job ID: $($frontendJob.Id))" -ForegroundColor Green
    Write-Host "  地址: http://localhost:3000" -ForegroundColor Gray
    Write-Host "  注意: 前端服務在後台運行，可能需要30-60秒才能完全啟動" -ForegroundColor Yellow
} else {
    Write-Host "  [FAIL] 前端服務啟動失敗" -ForegroundColor Red
}

Start-Sleep -Seconds 10

# 5. 驗證服務
Write-Host "[5/5] 驗證服務狀態..." -ForegroundColor Yellow

# 檢查後端
$backendOk = $false
for ($i = 0; $i -lt 10; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "  [OK] 後端服務正常運行" -ForegroundColor Green
            $backendOk = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $backendOk) {
    Write-Host "  [WARN] 後端服務可能還在啟動中，請稍後訪問 http://localhost:8000/health" -ForegroundColor Yellow
}

# 檢查前端
$frontendOk = $false
for ($i = 0; $i -lt 10; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "  [OK] 前端服務正常運行" -ForegroundColor Green
            $frontendOk = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $frontendOk) {
    Write-Host "  [WARN] 前端服務可能還在啟動中，請稍後訪問 http://localhost:3000" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "服務啟動完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "訪問地址:" -ForegroundColor Yellow
Write-Host "  後端API: http://localhost:8000" -ForegroundColor White
Write-Host "  API文檔: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  前端頁面: http://localhost:3000" -ForegroundColor White
Write-Host "  服務器管理: http://localhost:3000/group-ai/servers" -ForegroundColor White
Write-Host ""
Write-Host "如果服務無法訪問，請檢查:" -ForegroundColor Yellow
Write-Host "  1. 防火牆是否阻止了端口8000和3000" -ForegroundColor White
Write-Host "  2. 查看後端日誌: Get-Content logs\backend_*.log -Tail 50" -ForegroundColor White
Write-Host "  3. 查看前端日誌: Get-Content logs\frontend_*.log -Tail 50" -ForegroundColor White
Write-Host "  4. 檢查進程: Get-Process | Where-Object {`$_.ProcessName -like '*python*' -or `$_.ProcessName -like '*node*'}" -ForegroundColor White

