#!/bin/bash
# 运行站点管理数据库迁移

set -e

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
ADMIN_BACKEND="$PROJECT_ROOT/admin-backend"
VENV_PATH="$ADMIN_BACKEND/.venv"

cd "$ADMIN_BACKEND" || { echo "❌ 无法进入后端目录: $ADMIN_BACKEND"; exit 1; }

# 激活虚拟环境
echo "🐍 激活虚拟环境..."
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "✅ 虚拟环境已激活: $VENV_PATH"
elif [ -d "$ADMIN_BACKEND/venv" ]; then
    source "$ADMIN_BACKEND/venv/bin/activate"
    echo "✅ 虚拟环境已激活: $ADMIN_BACKEND/venv"
else
    echo "❌ 未找到虚拟环境，请手动激活或创建。"
    exit 1
fi

# 运行迁移
echo "🔄 运行数据库迁移..."
if alembic upgrade head; then
    echo "✅ 数据库迁移成功！"
else
    echo "❌ 数据库迁移失败"
    exit 1
fi

# 初始化站点数据
echo "📝 初始化站点数据..."
if python scripts/init_sites.py; then
    echo "✅ 站点数据初始化成功！"
else
    echo "⚠️  站点数据初始化失败，但迁移已完成。"
fi

echo "=========================================="
echo "✅ 站点管理数据库迁移完成！"
echo "=========================================="

