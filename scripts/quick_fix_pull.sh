#!/bin/bash
# 快速修复 Git Pull 冲突（更激进的方法）

set -e

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"

echo "🚀 快速修复 Git Pull 冲突..."

cd "$PROJECT_ROOT" || {
    echo "❌ 无法进入项目目录"
    exit 1
}

# 方法1: 使用 git stash 暂存所有更改
echo "📦 暂存所有本地更改..."
git stash || true

# 方法2: 强制清理未跟踪的文件
echo "🧹 清理未跟踪的文件..."
git clean -fd || true

# 方法3: 重置到远程状态（如果 stash 不够）
echo "🔄 重置到远程状态..."
git fetch origin main
git reset --hard origin/main || {
    echo "⚠️  重置失败，尝试其他方法..."
    
    # 备用方法：删除冲突目录后重新拉取
    echo "🗑️  删除冲突目录..."
    rm -rf aizkw20251219 hbwy20251220 tgmini20251220 2>/dev/null || true
    
    echo "⬇️  重新拉取..."
    git pull origin main
}

echo "✅ 修复完成！"
echo "💡 如果之前有本地更改，可以使用: git stash pop"

