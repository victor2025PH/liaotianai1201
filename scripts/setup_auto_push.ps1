# Git 自动推送配置脚本 (PowerShell 版本)
# 创建 post-commit hook，在每次提交后自动推送到 GitHub

$ErrorActionPreference = "Stop"

$GitDir = git rev-parse --git-dir
$HookFile = Join-Path $GitDir "hooks\post-commit"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🔧 设置 Git 自动推送" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否已存在 post-commit hook
if (Test-Path $HookFile) {
    Write-Host "⚠️  已存在 post-commit hook" -ForegroundColor Yellow
    Write-Host "当前内容:" -ForegroundColor Gray
    Get-Content $HookFile -Head 10
    Write-Host ""
    $overwrite = Read-Host "是否覆盖? (y/n)"
    if ($overwrite -ne "y") {
        Write-Host "已取消"
        exit 0
    }
}

# 确保 hooks 目录存在
$hooksDir = Split-Path $HookFile -Parent
if (-not (Test-Path $hooksDir)) {
    New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null
}

# 创建 post-commit hook (使用 bash，因为 Git for Windows 自带 bash)
$hookContent = @'
#!/bin/bash
# Git post-commit hook - 自动推送到远程仓库
# 此 hook 在每次 commit 后自动执行 git push

# 获取当前分支
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# 只在 main 分支上自动推送
if [ "$CURRENT_BRANCH" = "main" ]; then
    echo ""
    echo "=========================================="
    echo "🚀 自动推送到 GitHub..."
    echo "=========================================="
    echo ""
    
    # 尝试推送
    if git push origin main 2>&1; then
        echo ""
        echo "✅ 自动推送成功！"
        echo ""
    else
        echo ""
        echo "⚠️  自动推送失败（可能需要认证或网络问题）"
        echo "   可以稍后手动执行: git push origin main"
        echo ""
    fi
fi

exit 0
'@

# 写入文件（使用 UTF-8 无 BOM）
$Utf8NoBomEncoding = New-Object System.Text.UTF8Encoding $False
[System.IO.File]::WriteAllText($HookFile, $hookContent, $Utf8NoBomEncoding)

Write-Host "✅ Git post-commit hook 已创建" -ForegroundColor Green
Write-Host ""
Write-Host "📋 配置说明:" -ForegroundColor Cyan
Write-Host "   - 每次 commit 后会自动推送到 GitHub (main 分支)" -ForegroundColor Gray
Write-Host "   - 只在 main 分支上触发" -ForegroundColor Gray
Write-Host "   - Hook 文件位置: $HookFile" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  注意:" -ForegroundColor Yellow
Write-Host "   - 如果推送失败（需要认证等），会显示警告" -ForegroundColor Gray
Write-Host "   - 可以稍后手动执行: git push origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 如需禁用自动推送，删除文件:" -ForegroundColor Cyan
Write-Host "   Remove-Item '$HookFile'" -ForegroundColor Gray
Write-Host ""

