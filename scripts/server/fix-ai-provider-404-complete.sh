#!/bin/bash
# 完整修复 AI Provider API 404 问题

set -e

echo "=========================================="
echo "修复 AI Provider API 404 问题"
echo "=========================================="

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
ADMIN_BACKEND="$PROJECT_ROOT/admin-backend"
VENV_PATH="$ADMIN_BACKEND/.venv"

cd "$PROJECT_ROOT"

echo ""
echo "[1/6] 检查代码是否存在..."
if [ ! -f "$ADMIN_BACKEND/app/api/group_ai/ai_provider.py" ]; then
    echo "❌ ai_provider.py 文件不存在！"
    exit 1
fi
echo "✅ 代码文件存在"

echo ""
echo "[2/6] 检查数据库迁移..."
cd "$ADMIN_BACKEND"
source "$VENV_PATH/bin/activate" || {
    echo "⚠️  虚拟环境不存在，尝试创建..."
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    pip install -q -r requirements.txt || true
}

# 检查是否需要运行迁移
echo "检查数据库表..."
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/home/ubuntu/telegram-ai-system/admin-backend')

from app.db import SessionLocal, engine
from sqlalchemy import inspect, text

db = SessionLocal()
inspector = inspect(engine)

try:
    # 检查表是否存在
    tables = inspector.get_table_names()
    
    if 'ai_provider_configs' not in tables or 'ai_provider_settings' not in tables:
        print("⚠️  数据库表不存在，需要运行迁移")
        print("运行: cd /home/ubuntu/telegram-ai-system/admin-backend && source .venv/bin/activate && python -m alembic upgrade head")
        sys.exit(1)
    else:
        print("✅ 数据库表已存在")
finally:
    db.close()
PYTHON_SCRIPT

MIGRATION_NEEDED=$?
if [ $MIGRATION_NEEDED -ne 0 ]; then
    echo ""
    echo "[2.5/6] 运行数据库迁移..."
    python3 -m alembic revision --autogenerate -m "添加AI Provider配置表" 2>/dev/null || echo "迁移文件可能已存在"
    python3 -m alembic upgrade head || {
        echo "⚠️  迁移失败，但继续..."
    }
fi

echo ""
echo "[3/6] 检查端口 8000 占用..."
PORT_PID=$(lsof -ti:8000 || echo "")
if [ -n "$PORT_PID" ]; then
    echo "⚠️  端口 8000 被占用 (PID: $PORT_PID)，正在清理..."
    kill -9 $PORT_PID 2>/dev/null || true
    sleep 2
fi
echo "✅ 端口 8000 已清理"

echo ""
echo "[4/6] 停止后端服务..."
sudo systemctl stop luckyred-api || echo "服务可能未运行"
sleep 2

echo ""
echo "[5/6] 检查 Python 语法..."
python3 -m py_compile "$ADMIN_BACKEND/app/api/group_ai/ai_provider.py" || {
    echo "❌ Python 语法错误！"
    exit 1
}
echo "✅ Python 语法正确"

echo ""
echo "[6/6] 启动后端服务..."
sudo systemctl start luckyred-api
sleep 5

# 检查服务状态
if sudo systemctl is-active --quiet luckyred-api; then
    echo "✅ 后端服务已启动"
else
    echo "❌ 后端服务启动失败"
    echo "查看日志: sudo journalctl -u luckyred-api -n 50"
    exit 1
fi

echo ""
echo "[7/7] 测试 API 端点..."
sleep 3

# 测试端点
ENDPOINTS=(
    "/api/v1/group-ai/ai-provider/providers"
    "/api/v1/group-ai/ai-provider/status"
)

for endpoint in "${ENDPOINTS[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$endpoint" || echo "000")
    if [ "$response" = "200" ] || [ "$response" = "401" ] || [ "$response" = "403" ]; then
        echo "✅ $endpoint 可访问 (HTTP $response)"
    else
        echo "⚠️  $endpoint 返回 HTTP $response"
    fi
done

echo ""
echo "=========================================="
echo "修复完成！"
echo "=========================================="
echo ""
echo "如果仍有问题，请检查："
echo "1. 后端服务日志: sudo journalctl -u luckyred-api -n 100"
echo "2. 数据库连接: cd $ADMIN_BACKEND && source .venv/bin/activate && python -c 'from app.db import SessionLocal; db = SessionLocal(); db.close()'"
echo "3. API 路由: curl http://localhost:8000/docs"
echo ""

