#!/bin/bash
# 设置 Git 自动推送功能
# 创建 post-commit hook，在每次提交后自动推送到 GitHub

set -e

GIT_DIR="$(git rev-parse --git-dir)"
HOOK_FILE="$GIT_DIR/hooks/post-commit"

echo "=========================================="
echo "🔧 设置 Git 自动推送"
echo "=========================================="
echo ""

# 检查是否已存在 post-commit hook
if [ -f "$HOOK_FILE" ]; then
    echo "⚠️  已存在 post-commit hook"
    echo "当前内容:"
    head -10 "$HOOK_FILE"
    echo ""
    read -p "是否覆盖? (y/n): " overwrite
    if [ "$overwrite" != "y" ]; then
        echo "已取消"
        exit 0
    fi
fi

# 创建 post-commit hook
cat > "$HOOK_FILE" << 'HOOK_EOF'
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
HOOK_EOF

# 添加执行权限
chmod +x "$HOOK_FILE"

echo "✅ Git post-commit hook 已创建"
echo ""
echo "📋 配置说明:"
echo "   - 每次 commit 后会自动推送到 GitHub (main 分支)"
echo "   - 只在 main 分支上触发"
echo "   - Hook 文件位置: $HOOK_FILE"
echo ""
echo "⚠️  注意:"
echo "   - 如果推送失败（需要认证等），会显示警告"
echo "   - 可以稍后手动执行: git push origin main"
echo ""
echo "💡 如需禁用自动推送，删除文件:"
echo "   rm $HOOK_FILE"
echo ""

