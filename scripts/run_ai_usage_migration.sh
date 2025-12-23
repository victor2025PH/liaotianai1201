#!/bin/bash
# 执行 AI 使用统计表的数据库迁移

set -e

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_ROOT/admin-backend"

echo "🚀 开始执行 AI 使用统计表迁移..."

# 1. 进入后端目录
cd "$BACKEND_DIR" || {
    echo "❌ 无法进入后端目录: $BACKEND_DIR"
    exit 1
}

# 2. 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ 已激活虚拟环境"
elif [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 已激活虚拟环境"
else
    echo "⚠️  未找到虚拟环境，使用系统 Python"
fi

# 3. 检查 Alembic 是否安装
if ! python -m alembic --version > /dev/null 2>&1; then
    echo "❌ Alembic 未安装，正在安装..."
    pip install alembic
fi

# 4. 显示当前迁移状态
echo "📊 当前迁移状态:"
python -m alembic current

# 5. 执行迁移
echo "🔄 执行迁移到最新版本..."
python -m alembic upgrade head

# 6. 验证迁移结果
echo "✅ 迁移完成！"
echo "📊 迁移后状态:"
python -m alembic current

echo "🎉 AI 使用统计表迁移完成！"

