#!/bin/bash
# 应用 AI 使用统计表的数据库迁移

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "应用 AI 使用统计表迁移"
echo "=========================================="
echo ""

# 项目路径
PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_ROOT/admin-backend"

# 检查目录
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ 后端目录不存在: $BACKEND_DIR${NC}"
    exit 1
fi

cd "$BACKEND_DIR" || exit 1

# 检查虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo -e "${YELLOW}⚠️  未找到虚拟环境，使用系统 Python${NC}"
fi

# 检查 alembic
if ! command -v alembic &> /dev/null; then
    echo -e "${RED}❌ Alembic 未安装${NC}"
    echo "请先安装: pip install alembic"
    exit 1
fi

# 检查迁移文件
MIGRATION_FILE="alembic/versions/xxxx_add_ai_usage_tables.py"
if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${YELLOW}⚠️  迁移文件不存在: $MIGRATION_FILE${NC}"
    echo "请先运行: bash scripts/create_ai_usage_migration.sh"
    exit 1
fi

echo -e "${GREEN}✅ 环境检查通过${NC}"
echo ""

# 检查当前数据库版本
echo "检查当前数据库版本..."
CURRENT_VERSION=$(alembic current 2>/dev/null | grep -oP '\(head\)|\([a-f0-9]+\)' | head -1 || echo "unknown")
echo "当前版本: $CURRENT_VERSION"
echo ""

# 预览迁移
echo "预览迁移计划..."
alembic upgrade head --sql 2>/dev/null | tail -20 || echo "无法预览（可能需要先执行迁移）"
echo ""

# 确认
read -p "是否继续执行迁移？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

# 执行迁移
echo "执行迁移..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 迁移成功完成${NC}"
    echo ""
    echo "验证："
    echo "1. 检查表是否创建:"
    echo "   sqlite3 admin.db '.tables' | grep ai_usage"
    echo ""
    echo "2. 检查表结构:"
    echo "   sqlite3 admin.db '.schema ai_usage_logs'"
    echo "   sqlite3 admin.db '.schema ai_usage_stats'"
else
    echo ""
    echo -e "${RED}❌ 迁移失败${NC}"
    echo "请检查错误信息并修复"
    exit 1
fi

echo ""
echo "=========================================="
echo "迁移完成"
echo "=========================================="

