#!/bin/bash
# 修复 Alembic 多个 head 版本问题

set -e

echo "=========================================="
echo "修复 Alembic 多个 head 版本"
echo "=========================================="

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
ADMIN_BACKEND="$PROJECT_ROOT/admin-backend"
VENV_PATH="$ADMIN_BACKEND/.venv"

cd "$ADMIN_BACKEND"
source "$VENV_PATH/bin/activate"

echo ""
echo "[1] 检查当前迁移状态..."
python3 -m alembic heads

echo ""
echo "[2] 查看所有 head 版本..."
HEADS=$(python3 -m alembic heads | grep -v "INFO" | grep -v "Context" | grep -v "Will assume" | tr '\n' ' ')
echo "找到的 head 版本: $HEADS"

echo ""
echo "[3] 合并 head 版本..."
# 获取所有 head 版本
HEAD_LIST=$(python3 -m alembic heads 2>&1 | grep -E "^[a-f0-9]+" | head -2)

if [ $(echo "$HEAD_LIST" | wc -l) -gt 1 ]; then
    echo "发现多个 head 版本，需要合并..."
    FIRST_HEAD=$(echo "$HEAD_LIST" | head -1 | awk '{print $1}')
    SECOND_HEAD=$(echo "$HEAD_LIST" | tail -1 | awk '{print $1}')
    
    echo "合并 $FIRST_HEAD 和 $SECOND_HEAD..."
    python3 -m alembic merge -m "合并多个head版本" "$FIRST_HEAD" "$SECOND_HEAD" || {
        echo "⚠️  自动合并失败，尝试手动合并..."
        echo "请手动执行: python3 -m alembic merge -m '合并head' <revision1> <revision2>"
    }
else
    echo "✅ 只有一个 head 版本，无需合并"
fi

echo ""
echo "[4] 升级到最新版本..."
python3 -m alembic upgrade head || {
    echo "⚠️  升级失败，尝试升级到所有 heads..."
    python3 -m alembic upgrade heads
}

echo ""
echo "[5] 验证迁移状态..."
python3 -m alembic current

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="

