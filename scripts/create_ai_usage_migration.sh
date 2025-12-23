#!/bin/bash
# 创建 AI 使用统计表的数据库迁移脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "创建 AI 使用统计表迁移"
echo "=========================================="
echo ""

# 项目路径
PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_ROOT/admin-backend"

# 检查目录
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ 后端目录不存在: $BACKEND_DIR"
    exit 1
fi

cd "$BACKEND_DIR" || exit 1

# 检查虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "⚠️  未找到虚拟环境，使用系统 Python"
fi

# 检查 alembic
if ! command -v alembic &> /dev/null; then
    echo "❌ Alembic 未安装"
    echo "请先安装: pip install alembic"
    exit 1
fi

echo -e "${GREEN}✅ 环境检查通过${NC}"
echo ""

# 创建迁移
echo "创建迁移文件..."
alembic revision --autogenerate -m "add_ai_usage_tables" || {
    echo "❌ 自动生成迁移失败，使用手动迁移文件"
    echo "迁移文件已创建: alembic/versions/xxxx_add_ai_usage_tables.py"
    echo "请检查并更新 revision ID"
}

echo ""
echo "=========================================="
echo "迁移文件创建完成"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 检查迁移文件: alembic/versions/xxxx_add_ai_usage_tables.py"
echo "2. 更新 revision ID（如果需要）"
echo "3. 执行迁移: alembic upgrade head"
echo ""

