# 觸發 CI 測試腳本
# 推送到 develop 分支以觸發 CI 工作流

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "觸發 CI/CD 測試" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "步驟 1: 檢查當前分支" -ForegroundColor Yellow
$currentBranch = git branch --show-current
Write-Host "當前分支: $currentBranch" -ForegroundColor Green
Write-Host ""

Write-Host "步驟 2: 切換到 develop 分支" -ForegroundColor Yellow
git checkout develop
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 切換分支失敗，develop 分支可能不存在" -ForegroundColor Red
    Write-Host "   請先創建 develop 分支：" -ForegroundColor Yellow
    Write-Host "   git checkout -b develop" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ 已切換到 develop 分支" -ForegroundColor Green
Write-Host ""

Write-Host "步驟 3: 創建測試文件" -ForegroundColor Yellow
$testContent = "# CI/CD 測試 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"
$testContent | Out-File -FilePath "test-cicd-develop.md" -Encoding UTF8 -Append
Write-Host "✅ 已創建測試文件: test-cicd-develop.md" -ForegroundColor Green
Write-Host ""

Write-Host "步驟 4: 添加並提交" -ForegroundColor Yellow
git add test-cicd-develop.md
git commit -m "test: CI/CD 流程驗證 - develop 分支"
Write-Host "✅ 已提交" -ForegroundColor Green
Write-Host ""

Write-Host "步驟 5: 推送到遠程（會觸發 CI）" -ForegroundColor Yellow
Write-Host "正在推送..." -ForegroundColor Gray
git push origin develop
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ 推送成功！CI 工作流已觸發" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步：" -ForegroundColor Yellow
    Write-Host "  1. 等待 1-2 分鐘讓工作流開始運行" -ForegroundColor White
    Write-Host "  2. 訪問 GitHub 倉庫頁面" -ForegroundColor White
    Write-Host "  3. 點擊頂部的 'Actions' 標籤" -ForegroundColor White
    Write-Host "  4. 查看 'CI' 工作流運行狀態" -ForegroundColor White
    Write-Host ""
    Write-Host "直接訪問 URL（替換 <倉庫名>）：" -ForegroundColor Yellow
    Write-Host "  https://github.com/victor2025PH/<倉庫名>/actions" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ 推送失敗，請檢查錯誤信息" -ForegroundColor Red
    exit 1
}
