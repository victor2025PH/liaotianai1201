#!/bin/bash
# ============================================================
# 修复 Git 历史中的 OpenAI API Key
# ============================================================
# 功能：从 Git 历史中移除硬编码的 OpenAI API Key
# 使用方法：bash scripts/fix-openai-api-key-in-history.sh
# ============================================================

set -e

echo "============================================================"
echo "🔧 修复 Git 历史中的 OpenAI API Key"
echo "============================================================"
echo ""
echo "⚠️  警告：此操作会重写 Git 历史"
echo "⚠️  如果仓库是共享的，需要通知所有协作者"
echo ""
echo "按 Ctrl+C 取消，或等待 5 秒后继续..."
sleep 5
echo ""

cd "$(git rev-parse --show-toplevel)"

# 要替换的 API Key（从 GitHub 错误信息中获取）
# 注意：将下面的占位符替换为 GitHub 错误信息中显示的完整 API Key
OLD_API_KEY="<从 GitHub 错误信息中获取的完整 API Key>"
NEW_PLACEHOLDER="YOUR_OPENAI_API_KEY"

# 检查是否已设置 API Key
if [ "$OLD_API_KEY" = "<从 GitHub 错误信息中获取的完整 API Key>" ]; then
    echo "❌ 错误：请先设置 OLD_API_KEY 变量"
    echo "   从 GitHub 推送错误信息中复制完整的 API Key，然后修改此脚本"
    exit 1
fi

# 备份当前分支
BACKUP_BRANCH="backup-before-api-key-fix-$(date +%Y%m%d-%H%M%S)"
echo "创建备份分支: $BACKUP_BRANCH"
git branch "$BACKUP_BRANCH"
echo "✅ 备份完成"
echo ""

# 方法 1: 使用 git filter-branch（如果 BFG 不可用）
echo "方法 1: 使用 git filter-branch 替换 API Key..."
echo "----------------------------------------"

# 创建替换脚本
cat > /tmp/replace-api-key.sh << 'EOFSCRIPT'
#!/bin/bash
# 替换文件中的 API Key
sed -i "s|$OLD_API_KEY|$NEW_PLACEHOLDER|g" "$@"
EOFSCRIPT
chmod +x /tmp/replace-api-key.sh

# 使用 git filter-branch
git filter-branch --force --tree-filter \
  "if [ -f AI_ROBOT_SETUP.md ]; then
     sed -i 's|$OLD_API_KEY|$NEW_PLACEHOLDER|g' AI_ROBOT_SETUP.md
   fi" \
  --prune-empty --tag-name-filter cat -- --all

echo ""
echo "✅ Git 历史已重写"
echo ""

# 清理
echo "清理临时文件..."
rm -f /tmp/replace-api-key.sh
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "============================================================"
echo "✅ 修复完成"
echo "============================================================"
echo ""
echo "下一步："
echo "  1. 检查修复结果: git log --all -p | grep -A5 -B5 'OPENAI_API_KEY'"
echo "  2. 如果确认无误，强制推送: git push origin --force --all"
echo "  3. 通知协作者重新克隆仓库或执行: git fetch origin && git reset --hard origin/main"
echo ""
echo "备份分支: $BACKUP_BRANCH"
echo "如需恢复，执行: git reset --hard $BACKUP_BRANCH"
echo ""
