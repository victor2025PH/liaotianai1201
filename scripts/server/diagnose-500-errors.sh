#!/bin/bash
# ============================================================
# 诊断 500 Internal Server Error 问题
# ============================================================

set -e

echo "=========================================="
echo "诊断 500 Internal Server Error"
echo "=========================================="

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
BACKEND_SERVICE="luckyred-api"

# 自动检测后端服务名
if systemctl cat telegram-backend.service >/dev/null 2>&1; then
    BACKEND_SERVICE="telegram-backend"
fi

echo "检测到的后端服务: $BACKEND_SERVICE"
echo ""

# 1. 检查服务状态
echo "[1/6] 检查后端服务状态..."
echo "----------------------------------------"
SERVICE_STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
echo "服务状态: $SERVICE_STATUS"

if [ "$SERVICE_STATUS" != "active" ]; then
    echo "⚠️  后端服务未运行！"
    echo "尝试启动服务..."
    sudo systemctl start "$BACKEND_SERVICE" || true
    sleep 5
    SERVICE_STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
    echo "启动后状态: $SERVICE_STATUS"
fi
echo ""

# 2. 检查端口监听
echo "[2/6] 检查端口 8000 监听..."
echo "----------------------------------------"
PORT_8000=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
if [ -z "$PORT_8000" ]; then
    echo "❌ 端口 8000 未监听"
else
    echo "✅ 端口 8000 正在监听:"
    echo "$PORT_8000"
fi
echo ""

# 3. 检查后端日志（最近的错误）
echo "[3/6] 检查后端服务最近日志（最后 50 行）..."
echo "----------------------------------------"
sudo journalctl -u "$BACKEND_SERVICE" -n 50 --no-pager | tail -30 || true
echo ""

# 4. 检查 Python 语法错误
echo "[4/6] 检查 Python 代码语法..."
echo "----------------------------------------"
cd "$BACKEND_DIR" || exit 1

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    
    echo "检查主应用文件..."
    python3 -m py_compile app/main.py 2>&1 || echo "⚠️  主应用文件有语法错误"
    
    echo "检查 AI Provider API..."
    python3 -m py_compile app/api/group_ai/ai_provider.py 2>&1 || echo "⚠️  AI Provider API 有语法错误"
    
    echo "检查模型文件..."
    python3 -m py_compile app/models/group_ai.py 2>&1 || echo "⚠️  模型文件有语法错误"
    
    deactivate
else
    echo "⚠️  虚拟环境不存在"
fi
echo ""

# 5. 测试本地 API 连接
echo "[5/6] 测试本地 API 连接..."
echo "----------------------------------------"
echo "测试健康检查端点..."
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:8000/health 2>&1 || echo "ERROR")
HEALTH_HTTP_CODE=$(echo "$HEALTH_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2 || echo "000")

if [ "$HEALTH_HTTP_CODE" = "200" ]; then
    echo "✅ 健康检查通过 (HTTP $HEALTH_HTTP_CODE)"
    echo "$HEALTH_RESPONSE" | grep -v "HTTP_CODE" | head -5
else
    echo "❌ 健康检查失败 (HTTP $HEALTH_HTTP_CODE)"
    echo "响应:"
    echo "$HEALTH_RESPONSE" | head -10
fi
echo ""

echo "测试 AI Provider API..."
AI_PROVIDER_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:8000/api/v1/group-ai/ai-provider/providers 2>&1 || echo "ERROR")
AI_PROVIDER_HTTP_CODE=$(echo "$AI_PROVIDER_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2 || echo "000")

if [ "$AI_PROVIDER_HTTP_CODE" = "200" ] || [ "$AI_PROVIDER_HTTP_CODE" = "401" ]; then
    echo "✅ AI Provider API 可访问 (HTTP $AI_PROVIDER_HTTP_CODE)"
else
    echo "❌ AI Provider API 失败 (HTTP $AI_PROVIDER_HTTP_CODE)"
    echo "响应:"
    echo "$AI_PROVIDER_RESPONSE" | head -20
fi
echo ""

# 6. 检查数据库连接
echo "[6/6] 检查数据库连接..."
echo "----------------------------------------"
cd "$BACKEND_DIR" || exit 1
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    
    echo "测试数据库连接..."
    python3 << 'PYTHON_SCRIPT'
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from app.db import SessionLocal
    db = SessionLocal()
    # 尝试执行一个简单查询
    db.execute("SELECT 1")
    db.close()
    print("✅ 数据库连接正常")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    sys.exit(1)
PYTHON_SCRIPT
    
    deactivate
else
    echo "⚠️  虚拟环境不存在，无法测试数据库"
fi
echo ""

echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "如果发现问题，请检查："
echo "  1. 后端服务日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager"
echo "  2. 后端应用日志: tail -n 100 $PROJECT_DIR/logs/backend.log"
echo "  3. 数据库文件: ls -lh $BACKEND_DIR/admin.db"
echo ""

