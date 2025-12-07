# ============================================================
# 檢查並同步腳本到服務器 (本地執行 - PowerShell)
# ============================================================
# 
# 功能：檢查服務器腳本狀態並同步到 GitHub
# 運行環境：本地 Windows 環境 (PowerShell)
# 
# 一鍵執行：scripts\local\check-and-sync-scripts.ps1
# ============================================================

# 設置 UTF-8 編碼
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "檢查並同步服務器腳本到 GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 切換到項目根目錄
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Join-Path $ScriptDir "..\.."
Set-Location $ProjectRoot

# 檢查是否在項目根目錄
if (-not (Test-Path "scripts\server\")) {
    Write-Host "❌ 錯誤：請在項目根目錄執行此腳本" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[1/4] 檢查 Git 狀態..." -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "[2/4] 檢查服務器腳本文件..." -ForegroundColor Yellow
$serverScripts = Get-ChildItem -Path "scripts\server\" -File -Recurse | Where-Object { $_.Extension -in @('.sh', '.md', '.py') }
Write-Host "找到 $($serverScripts.Count) 個服務器腳本文件：" -ForegroundColor Green
foreach ($script in $serverScripts) {
    $status = git status --short $script.FullName
    if ($status) {
        Write-Host "  ⚠ $($script.Name) - 未提交" -ForegroundColor Yellow
    } else {
        Write-Host "  ✓ $($script.Name) - 已提交" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "[3/4] 添加服務器腳本文件..." -ForegroundColor Yellow
# 添加所有服務器腳本
git add scripts/server/*.sh
git add scripts/server/*.md
git add scripts/server/README.md
# 添加相關文檔（如果存在，已重命名為英文）
if (Test-Path "server-deployment-quick-guide.md") { git add server-deployment-quick-guide.md }
if (Test-Path "server-download-scripts-guide.md") { git add server-download-scripts-guide.md }
# 添加規則文件
git add .cursor/rules/file-organization.mdc
# 強制添加所有服務器目錄下的文件
git add -f scripts/server/

Write-Host ""
Write-Host "[4/4] 提交並推送到 GitHub..." -ForegroundColor Yellow
# 使用英文提交信息，避免亂碼
$commitMessage = "Add server deployment scripts: install-dependencies, setup-server, quick-start, sync guide"
git commit -m $commitMessage

Write-Host ""
Write-Host "正在推送到 GitHub..." -ForegroundColor Yellow
$pushResult = git push origin main 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ 推送成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "已上傳的文件：" -ForegroundColor Cyan
    git log -1 --name-only --pretty=format:"" | Where-Object { $_ -match "scripts/server" }
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "❌ 推送失敗！" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host $pushResult -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 下一步：在服務器上執行以下命令" -ForegroundColor Yellow
Write-Host ""
Write-Host "   cd ~/telegram-ai-system" -ForegroundColor Cyan
Write-Host "   git pull origin main" -ForegroundColor Cyan
Write-Host "   chmod +x scripts/server/*.sh" -ForegroundColor Cyan
Write-Host "   bash scripts/server/quick-start.sh" -ForegroundColor Cyan
Write-Host ""
pause

