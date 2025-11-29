# E2E 測試運行腳本
Write-Host "開始運行 E2E 測試..." -ForegroundColor Green

# 檢查是否在正確的目錄
if (-not (Test-Path "package.json")) {
    Write-Host "錯誤：未找到 package.json，請在 saas-demo 目錄下運行此腳本" -ForegroundColor Red
    exit 1
}

# 檢查 node_modules 是否存在
if (-not (Test-Path "node_modules")) {
    Write-Host "警告：node_modules 不存在，可能需要運行 npm install" -ForegroundColor Yellow
}

# 檢查 Playwright 是否安裝
Write-Host "檢查 Playwright 安裝..." -ForegroundColor Cyan
$playwrightInstalled = npx playwright --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Playwright 未安裝或需要安裝瀏覽器..." -ForegroundColor Yellow
    Write-Host "正在安裝 Playwright 瀏覽器..." -ForegroundColor Cyan
    npx playwright install chromium
}

# 列出所有測試
Write-Host "`n列出所有測試文件..." -ForegroundColor Cyan
Get-ChildItem e2e -Filter *.spec.ts | ForEach-Object {
    Write-Host "  - $($_.Name)" -ForegroundColor Gray
}

# 運行測試
Write-Host "`n開始運行 E2E 測試套件..." -ForegroundColor Green
Write-Host "注意：這將自動啟動開發服務器（如果未運行）" -ForegroundColor Yellow
Write-Host ""

# 運行所有測試
npx playwright test --reporter=list,html

# 檢查測試結果
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ 所有測試通過！" -ForegroundColor Green
} else {
    Write-Host "`n❌ 部分測試失敗，請查看上面的詳細信息" -ForegroundColor Red
    Write-Host "HTML 報告位置：playwright-report/index.html" -ForegroundColor Yellow
}

exit $LASTEXITCODE
