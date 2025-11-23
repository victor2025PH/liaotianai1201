# 測試所有服務的PowerShell腳本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "測試所有服務" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$testResults = @{}

# 1. 測試後端服務
Write-Host "[1/4] 測試後端服務..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  [OK] 健康檢查通過" -ForegroundColor Green
        $testResults["後端健康檢查"] = "通過"
    }
} catch {
    Write-Host "  [FAIL] 健康檢查失敗: $_" -ForegroundColor Red
    $testResults["後端健康檢查"] = "失敗"
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/group-ai/servers/" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  [OK] 服務器列表API正常" -ForegroundColor Green
        $testResults["後端服務器API"] = "通過"
    }
} catch {
    Write-Host "  [FAIL] 服務器列表API失敗: $_" -ForegroundColor Red
    $testResults["後端服務器API"] = "失敗"
}

# 2. 測試前端服務
Write-Host "[2/4] 測試前端服務..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  [OK] 前端頁面可訪問" -ForegroundColor Green
        $testResults["前端頁面"] = "通過"
    }
} catch {
    Write-Host "  [FAIL] 前端頁面無法訪問: $_" -ForegroundColor Red
    $testResults["前端頁面"] = "失敗"
}

# 3. 測試遠程服務器
Write-Host "[3/4] 測試遠程服務器..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://165.154.254.99:8000/health" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  [OK] 遠程服務器健康檢查通過" -ForegroundColor Green
        $testResults["遠程服務器"] = "通過"
    }
} catch {
    Write-Host "  [WARN] 遠程服務器無法訪問（可能未部署或未啟動）" -ForegroundColor Yellow
    $testResults["遠程服務器"] = "未部署"
}

# 4. 測試API文檔
Write-Host "[4/4] 測試API文檔..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  [OK] API文檔可訪問" -ForegroundColor Green
        $testResults["API文檔"] = "通過"
    }
} catch {
    Write-Host "  [FAIL] API文檔無法訪問: $_" -ForegroundColor Red
    $testResults["API文檔"] = "失敗"
}

# 顯示測試結果
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "測試結果總結" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

foreach ($test in $testResults.Keys) {
    $result = $testResults[$test]
    $color = if ($result -eq "通過") { "Green" } elseif ($result -eq "失敗") { "Red" } else { "Yellow" }
    Write-Host "  $test : $result" -ForegroundColor $color
}

Write-Host ""
Write-Host "詳細測試清單請查看: docs/测试清单/部署测试清单.md" -ForegroundColor Cyan

