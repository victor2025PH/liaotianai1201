#!/bin/bash
# 强制修复 Git Pull 冲突 - 删除冲突目录后重新拉取

set -e

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"

echo "🔧 强制修复 Git Pull 冲突..."

cd "$PROJECT_ROOT" || {
    echo "❌ 无法进入项目目录"
    exit 1
}

# 1. 显示当前状态
echo "📊 当前 Git 状态:"
git status --short | head -10

# 2. 暂存所有更改
echo "📦 暂存所有更改..."
git stash || true

# 3. 删除冲突的目录（这些目录应该从远程仓库拉取）
echo "🗑️  删除冲突目录..."
rm -rf aizkw20251219 hbwy20251220 tgmini20251220 2>/dev/null || true

# 4. 清理所有未跟踪的文件
echo "🧹 清理未跟踪的文件..."
git clean -fd || true

# 5. 重置到远程状态
echo "🔄 获取远程更新..."
git fetch origin main

# 6. 强制重置到远程状态
echo "🔄 重置到远程状态..."
git reset --hard origin/main || {
    echo "⚠️  重置失败，尝试其他方法..."
    
    # 备用方法：直接拉取
    git pull origin main --allow-unrelated-histories || {
        echo "❌ 仍然失败，请手动处理"
        exit 1
    }
}

# 7. 验证
echo "✅ 验证拉取结果..."
if [ -d "aizkw20251219" ] && [ -d "hbwy20251220" ] && [ -d "tgmini20251220" ]; then
    echo "✅ 所有目录已恢复"
    git status
else
    echo "⚠️  部分目录可能未恢复，请检查"
    ls -la | grep -E "aizkw|hbwy|tgmini"
fi

echo "🎉 修复完成！"

