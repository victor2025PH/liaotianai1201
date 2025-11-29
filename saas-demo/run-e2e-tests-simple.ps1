# 簡單的 E2E 測試運行腳本
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "開始運行 E2E 測試" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查目錄
if (-not (Test-Path "package.json")) {
    Write-Host "錯誤：請在 saas-demo 目錄下運行此腳本" -ForegroundColor Red
    exit 1
}

# 顯示當前目錄
Write-Host "當前目錄: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# 檢查 Playwright 是否可用
Write-Host "檢查 Playwright 安裝..." -ForegroundColor Yellow
try {
    $version = npx playwright --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Playwright 已安裝" -ForegroundColor Green
        Write-Host "  版本: $version" -ForegroundColor Gray
    } else {
        Write-Host "⚠ Playwright 可能需要安裝瀏覽器" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ 無法檢查 Playwright 版本" -ForegroundColor Yellow
}

Write-Host ""

# 列出測試文件
Write-Host "測試文件列表:" -ForegroundColor Cyan
Get-ChildItem e2e -Filter *.spec.ts | ForEach-Object {
    Write-Host "  - $($_.Name)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "開始運行測試..." -ForegroundColor Green
Write-Host "注意：這可能需要幾分鐘時間" -ForegroundColor Yellow
Write-Host ""

# 運行測試並捕獲輸出
$outputFile = "test-output-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
Write-Host "測試輸出將保存到: $outputFile" -ForegroundColor Gray
Write-Host ""

# 運行測試
try {
    npx playwright test --reporter=list,html 2>&1 | Tee-Object -FilePath $outputFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "✓ 所有測試通過！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "查看 HTML 報告: npx playwright show-report" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "✗ 部分測試失敗" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "查看詳細輸出: $outputFile" -ForegroundColor Yellow
        Write-Host "查看 HTML 報告: npx playwright show-report" -ForegroundColor Yellow
    }
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ 測試運行出錯" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "錯誤信息: $_" -ForegroundColor Red
    Write-Host "查看詳細輸出: $outputFile" -ForegroundColor Yellow
    exit 1
}

exit $LASTEXITCODE
