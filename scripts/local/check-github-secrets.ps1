# ============================================================
# Check GitHub Secrets Configuration (Local Environment - Windows)
# ============================================================
# 
# Running Environment: Local Windows Environment
# Function: Check if GitHub Secrets are configured
# 
# One-click execution: .\scripts\local\check-github-secrets.ps1
# ============================================================

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🔍 GitHub Secrets 配置检查" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "请按照以下步骤检查 GitHub Secrets 配置：`n" -ForegroundColor Yellow

Write-Host "1. 访问 GitHub 仓库设置页面：" -ForegroundColor Cyan
Write-Host "   https://github.com/victor2025PH/liaotianai1201/settings/secrets/actions`n" -ForegroundColor White

Write-Host "2. 检查以下三个 Secrets 是否已配置：`n" -ForegroundColor Cyan

Write-Host "   ✅ SERVER_HOST" -ForegroundColor Yellow
Write-Host "      说明: 服务器 IP 地址" -ForegroundColor Gray
Write-Host "      示例: 165.154.255.48`n" -ForegroundColor Gray

Write-Host "   ✅ SERVER_USER" -ForegroundColor Yellow
Write-Host "      说明: SSH 用户名" -ForegroundColor Gray
Write-Host "      示例: ubuntu`n" -ForegroundColor Gray

Write-Host "   ✅ SERVER_SSH_KEY" -ForegroundColor Yellow
Write-Host "      说明: SSH 私钥内容（完整内容，包括 BEGIN 和 END 行）" -ForegroundColor Gray
Write-Host "      格式: -----BEGIN OPENSSH PRIVATE KEY-----`n" -ForegroundColor Gray

Write-Host "3. 如果 Secrets 未配置，请按照 GITHUB_ACTIONS_SETUP.md 中的说明进行配置。`n" -ForegroundColor Cyan

Write-Host "4. 配置完成后，可以通过以下方式触发部署：`n" -ForegroundColor Cyan

Write-Host "   方式 1: 推送代码到 main 分支（自动触发）" -ForegroundColor Yellow
Write-Host "     git push origin main`n" -ForegroundColor White

Write-Host "   方式 2: 在 GitHub Actions 页面手动触发" -ForegroundColor Yellow
Write-Host "     访问: https://github.com/victor2025PH/liaotianai1201/actions" -ForegroundColor White
Write-Host "     选择 'Deploy to Server' 工作流" -ForegroundColor White
Write-Host "     点击 'Run workflow'`n" -ForegroundColor White

Write-Host "5. 查看部署状态：" -ForegroundColor Cyan
Write-Host "   https://github.com/victor2025PH/liaotianai1201/actions`n" -ForegroundColor White

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ 检查完成" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

