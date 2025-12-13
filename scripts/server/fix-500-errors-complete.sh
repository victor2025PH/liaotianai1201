#!/bin/bash
# ============================================================
# 全面修复 500 Internal Server Error
# ============================================================

set -e

echo "=========================================="
echo "全面修复 500 Internal Server Error"
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

# 1. 停止服务并清理端口
echo "[1/7] 停止服务并清理端口..."
echo "----------------------------------------"
sudo systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
sleep 3

# 清理端口 8000
PORT_8000_PID=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || echo "")
if [ -n "$PORT_8000_PID" ]; then
    echo "终止占用端口 8000 的进程: $PORT_8000_PID"
    sudo kill -9 "$PORT_8000_PID" 2>/dev/null || true
    sleep 2
fi

# 清理所有 uvicorn 进程
sudo pkill -9 -f "uvicorn.*8000" 2>/dev/null || true
sudo pkill -9 -f "uvicorn.*app.main" 2>/dev/null || true
sudo fuser -k 8000/tcp 2>/dev/null || true
sleep 2
echo "✅ 端口已清理"
echo ""

# 2. 检查 Python 代码语法
echo "[2/7] 检查 Python 代码语法..."
echo "----------------------------------------"
cd "$BACKEND_DIR" || exit 1

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    
    echo "检查关键文件语法..."
    SYNTAX_ERRORS=0
    
    for file in "app/main.py" "app/api/group_ai/ai_provider.py" "app/models/group_ai.py"; do
        if [ -f "$file" ]; then
            if python3 -m py_compile "$file" 2>&1; then
                echo "  ✅ $file - 语法正确"
            else
                echo "  ❌ $file - 语法错误"
                SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
            fi
        fi
    done
    
    if [ $SYNTAX_ERRORS -gt 0 ]; then
        echo "⚠️  发现 $SYNTAX_ERRORS 个语法错误，请修复后再继续"
        deactivate
        exit 1
    fi
    
    deactivate
else
    echo "⚠️  虚拟环境不存在，跳过语法检查"
fi
echo ""

# 3. 检查数据库
echo "[3/7] 检查数据库..."
echo "----------------------------------------"
DB_PATH="$BACKEND_DIR/admin.db"
if [ -f "$DB_PATH" ]; then
    echo "数据库文件存在: $DB_PATH"
    DB_SIZE=$(du -h "$DB_PATH" | awk '{print $1}')
    echo "数据库大小: $DB_SIZE"
    
    # 检查数据库是否可访问
    cd "$BACKEND_DIR" || exit 1
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        
        python3 << 'PYTHON_SCRIPT'
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from app.db import SessionLocal, engine
    from sqlalchemy import text
    
    # 测试数据库连接
    db = SessionLocal()
    result = db.execute(text("SELECT 1"))
    db.close()
    print("  ✅ 数据库连接正常")
except Exception as e:
    print(f"  ❌ 数据库连接失败: {e}")
    sys.exit(1)
PYTHON_SCRIPT
        
        if [ $? -ne 0 ]; then
            echo "⚠️  数据库连接失败，可能需要修复数据库"
        fi
        
        deactivate
    fi
else
    echo "⚠️  数据库文件不存在: $DB_PATH"
fi
echo ""

# 4. 查看最近的错误日志
echo "[4/7] 查看最近的错误日志..."
echo "----------------------------------------"
echo "最近 50 行日志（包含 ERROR 和异常）:"
sudo journalctl -u "$BACKEND_SERVICE" -n 100 --no-pager | grep -i "error\|exception\|traceback\|failed" | tail -30 || echo "未找到错误日志"
echo ""

# 5. 检查应用日志文件
echo "[5/7] 检查应用日志文件..."
echo "----------------------------------------"
LOG_FILE="$PROJECT_DIR/logs/backend.log"
if [ -f "$LOG_FILE" ]; then
    echo "应用日志文件: $LOG_FILE"
    echo "最近错误（最后 30 行）:"
    tail -n 100 "$LOG_FILE" | grep -i "error\|exception\|traceback\|failed" | tail -20 || echo "未找到错误"
else
    echo "⚠️  应用日志文件不存在: $LOG_FILE"
fi
echo ""

# 6. 重新加载 systemd 并启动服务
echo "[6/7] 重新加载 systemd 并启动服务..."
echo "----------------------------------------"
sudo systemctl daemon-reload
sudo systemctl reset-failed "$BACKEND_SERVICE" 2>/dev/null || true

echo "启动后端服务..."
sudo systemctl start "$BACKEND_SERVICE"

# 等待服务启动
echo "等待服务启动（15秒）..."
sleep 15

# 检查服务状态
SERVICE_STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
if [ "$SERVICE_STATUS" = "active" ]; then
    echo "✅ 后端服务已启动 (状态: $SERVICE_STATUS)"
else
    echo "❌ 后端服务启动失败 (状态: $SERVICE_STATUS)"
    echo "查看详细日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager"
    exit 1
fi
echo ""

# 7. 验证 API 健康
echo "[7/7] 验证 API 健康..."
echo "----------------------------------------"
sleep 5

echo "测试健康检查端点..."
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:8000/health 2>&1 || echo "ERROR")
HEALTH_HTTP_CODE=$(echo "$HEALTH_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2 || echo "000")

if [ "$HEALTH_HTTP_CODE" = "200" ]; then
    echo "✅ 健康检查通过 (HTTP $HEALTH_HTTP_CODE)"
else
    echo "❌ 健康检查失败 (HTTP $HEALTH_HTTP_CODE)"
    echo "响应内容:"
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
    echo "响应内容:"
    echo "$AI_PROVIDER_RESPONSE" | head -20
fi
echo ""

echo "=========================================="
if [ "$HEALTH_HTTP_CODE" = "200" ]; then
    echo "✅ 修复完成，服务已恢复正常"
else
    echo "⚠️  服务可能仍有问题，请检查日志"
    echo ""
    echo "查看详细日志:"
    echo "  sudo journalctl -u $BACKEND_SERVICE -n 200 --no-pager"
    echo "  tail -n 100 $PROJECT_DIR/logs/backend.log"
fi
echo "=========================================="

