# ============================================================
# 修复 Git 历史中的 OpenAI API Key (PowerShell 版本)
# ============================================================
# 功能：从 Git 历史中移除硬编码的 OpenAI API Key
# 使用方法：在 PowerShell 中执行: .\scripts\fix-openai-api-key-in-history.ps1
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🔧 修复 Git 历史中的 OpenAI API Key (PowerShell)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "⚠️  警告：此操作会重写 Git 历史" -ForegroundColor Yellow
Write-Host "⚠️  如果仓库是共享的，需要通知所有协作者" -ForegroundColor Yellow
Write-Host ""
Write-Host "按 Ctrl+C 取消，或等待 5 秒后继续..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Write-Host ""

# 设置工作目录
$RepoRoot = (Get-Location).Path
if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
    Write-Host "❌ 错误：当前目录不是 Git 仓库" -ForegroundColor Red
    exit 1
}

Set-Location $RepoRoot

# 要替换的 API Key（从 GitHub 错误信息中获取）
# 注意：将下面的占位符替换为 GitHub 错误信息中显示的完整 API Key
$OLD_API_KEY = "<从 GitHub 错误信息中获取的完整 API Key>"
$NEW_PLACEHOLDER = "YOUR_OPENAI_API_KEY"

# 检查是否已设置 API Key
if ($OLD_API_KEY -eq "<从 GitHub 错误信息中获取的完整 API Key>") {
    Write-Host "❌ 错误：请先设置 OLD_API_KEY 变量" -ForegroundColor Red
    Write-Host "   从 GitHub 推送错误信息中复制完整的 API Key，然后修改此脚本" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   例如：" -ForegroundColor Yellow
    Write-Host "   `$OLD_API_KEY = 'sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'" -ForegroundColor Gray
    exit 1
}

# 备份当前分支
$BackupBranch = "backup-before-api-key-fix-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Write-Host "创建备份分支: $BackupBranch" -ForegroundColor Cyan
git branch $BackupBranch
Write-Host "✅ 备份完成" -ForegroundColor Green
Write-Host ""

# 注意：git filter-branch 在 PowerShell 中执行复杂命令时可能有问题
# 建议使用 Git Bash 执行，或者使用 BFG Repo-Cleaner

Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "⚠️  重要提示" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "由于 PowerShell 对多行命令的支持限制，" -ForegroundColor Yellow
Write-Host "建议使用以下方法之一：" -ForegroundColor Yellow
Write-Host ""
Write-Host "方法 1: 使用 Git Bash 执行 bash 脚本" -ForegroundColor Cyan
Write-Host "   bash scripts/fix-openai-api-key-in-history.sh" -ForegroundColor Gray
Write-Host ""
Write-Host "方法 2: 使用 BFG Repo-Cleaner（推荐）" -ForegroundColor Cyan
Write-Host "   1. 下载 BFG: https://rtyley.github.io/bfg-repo-cleaner/" -ForegroundColor Gray
Write-Host "   2. 创建 passwords.txt 文件" -ForegroundColor Gray
Write-Host "   3. 运行: java -jar bfg.jar --replace-text passwords.txt .git" -ForegroundColor Gray
Write-Host ""
Write-Host "方法 3: 使用 GitHub 的允许机制（临时方案）" -ForegroundColor Cyan
Write-Host "   访问 GitHub 提供的 unblock URL" -ForegroundColor Gray
Write-Host ""

# 如果用户确认要继续，提供 Git Bash 命令
Write-Host "如果要在 Git Bash 中执行，使用以下命令：" -ForegroundColor Cyan
Write-Host ""
$bashCommand = @"
git filter-branch --force --tree-filter "if [ -f AI_ROBOT_SETUP.md ]; then sed -i 's|$OLD_API_KEY|$NEW_PLACEHOLDER|g' AI_ROBOT_SETUP.md; fi" --prune-empty --tag-name-filter cat -- --all
"@
Write-Host $bashCommand -ForegroundColor Gray
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "脚本执行完成（请使用上述方法之一完成修复）" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "备份分支: $BackupBranch" -ForegroundColor Green
Write-Host "如需恢复，执行: git reset --hard $BackupBranch" -ForegroundColor Gray
Write-Host ""
