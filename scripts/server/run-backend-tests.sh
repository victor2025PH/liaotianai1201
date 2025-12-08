#!/bin/bash
# ============================================================
# Run Backend Tests on Server
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Run pytest tests for backend
#
# One-click execution: bash scripts/server/run-backend-tests.sh
# ============================================================

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"

echo "============================================================"
echo "🧪 运行后端测试 (Backend Tests)"
echo "============================================================"
echo ""

cd "$BACKEND_DIR"

# 检查虚拟环境
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ 虚拟环境不存在，请先创建虚拟环境"
    exit 1
fi

# 激活虚拟环境
echo "[1/3] 激活虚拟环境..."
source venv/bin/activate

# 检查 pytest 是否安装
if ! python -m pytest --version > /dev/null 2>&1; then
    echo "[2/3] 安装 pytest..."
    pip install pytest pytest-asyncio pytest-cov
else
    echo "[2/3] pytest 已安装"
fi

# 运行测试
echo "[3/3] 运行测试..."
echo ""

python -m pytest tests/ -v --tb=short

echo ""
echo "============================================================"
echo "✅ 测试完成"
echo "============================================================"

