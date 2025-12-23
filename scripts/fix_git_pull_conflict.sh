#!/bin/bash
# 修复 Git Pull 冲突脚本
# 解决未跟踪文件覆盖问题

set -e

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"

echo "🔧 开始修复 Git Pull 冲突..."

cd "$PROJECT_ROOT" || {
    echo "❌ 无法进入项目目录: $PROJECT_ROOT"
    exit 1
}

# 1. 检查 Git 状态
echo "📊 检查 Git 状态..."
git status --short | head -20

# 2. 备份冲突的文件（如果需要）
BACKUP_DIR="$PROJECT_ROOT/backup_$(date +%Y%m%d_%H%M%S)"
echo "💾 创建备份目录: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# 3. 处理冲突的目录
CONFLICT_DIRS=("aizkw20251219" "hbwy20251220" "tgmini20251220")

for dir in "${CONFLICT_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "📁 处理目录: $dir"
        
        # 检查是否有未跟踪的文件
        if git status --porcelain "$dir" | grep -q "^??"; then
            echo "  ⚠️  发现未跟踪文件，备份到: $BACKUP_DIR/$dir"
            mkdir -p "$BACKUP_DIR/$dir"
            
            # 备份未跟踪的文件
            git status --porcelain "$dir" | grep "^??" | awk '{print $2}' | while read file; do
                if [ -f "$file" ]; then
                    mkdir -p "$BACKUP_DIR/$(dirname "$file")"
                    cp "$file" "$BACKUP_DIR/$file" 2>/dev/null || true
                fi
            done
            
            # 删除未跟踪的文件（这些文件会在 pull 后重新创建）
            echo "  🗑️  删除未跟踪文件..."
            git clean -fd "$dir" || {
                # 如果 git clean 失败，手动删除
                git status --porcelain "$dir" | grep "^??" | awk '{print $2}' | while read file; do
                    if [ -f "$file" ]; then
                        rm -f "$file"
                    fi
                done
            }
        fi
    fi
done

# 4. 清理未跟踪的文件
echo "🧹 清理未跟踪的文件..."
git clean -fd || true

# 5. 重新拉取
echo "⬇️  重新拉取代码..."
git pull origin main || {
    echo "❌ Git pull 仍然失败"
    echo "💡 建议手动执行以下命令："
    echo "   cd $PROJECT_ROOT"
    echo "   git stash"
    echo "   git pull origin main"
    echo "   git stash pop"
    exit 1
}

echo "✅ Git pull 成功！"

# 6. 显示备份位置
if [ -d "$BACKUP_DIR" ] && [ "$(ls -A $BACKUP_DIR)" ]; then
    echo "📦 备份文件保存在: $BACKUP_DIR"
    echo "   如需恢复，请手动复制文件"
fi

echo "🎉 修复完成！"

