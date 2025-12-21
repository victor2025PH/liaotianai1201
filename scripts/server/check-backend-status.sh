#!/bin/bash
# ============================================================
# 检查后端服务状态
# ============================================================

echo "=========================================="
echo "检查后端服务状态"
echo "=========================================="
echo ""

# 1. 检查 PM2 进程
echo "[1] 检查 PM2 进程..."
echo "----------------------------------------"
if command -v pm2 >/dev/null 2>&1; then
    echo "PM2 进程列表："
    pm2 list
    echo ""
    
    # 检查是否有 backend
    if pm2 list | grep -qE "backend|api"; then
        echo "✅ 找到后端进程"
        BACKEND_NAME=$(pm2 list | grep -E "backend|api" | awk '{print $2}' | head -1)
        echo "后端进程名称: $BACKEND_NAME"
        echo ""
        echo "查看日志（最后 30 行，不进入实时模式）:"
        pm2 logs "$BACKEND_NAME" --lines 30 --nostream 2>/dev/null | tail -30
    else
        echo "❌ 未找到后端进程"
        echo ""
        echo "当前只有以下进程："
        pm2 list | grep -v "id\|name\|───" | awk '{print "  - " $2}'
    fi
else
    echo "PM2 未安装"
fi
echo ""

# 2. 检查 systemd 服务
echo "[2] 检查 systemd 服务..."
echo "----------------------------------------"
BACKEND_SERVICES=$(systemctl list-units --type=service --state=running 2>/dev/null | grep -E "backend|api|telegram" | awk '{print $1}')
if [ -n "$BACKEND_SERVICES" ]; then
    echo "找到以下后端服务："
    echo "$BACKEND_SERVICES" | while read -r svc; do
        echo "  - $svc"
        sudo systemctl status "$svc" --no-pager -l | head -15
    done
else
    echo "未找到运行中的后端 systemd 服务"
fi
echo ""

# 3. 检查 Python 进程
echo "[3] 检查 Python 后端进程..."
echo "----------------------------------------"
PYTHON_PROCS=$(ps aux | grep -E "uvicorn|gunicorn|python.*main.py|python.*app.py" | grep -v grep)
if [ -n "$PYTHON_PROCS" ]; then
    echo "找到以下 Python 进程："
    echo "$PYTHON_PROCS"
else
    echo "未找到运行中的 Python 后端进程"
fi
echo ""

# 4. 检查端口 8000
echo "[4] 检查端口 8000（后端 API）..."
echo "----------------------------------------"
if sudo lsof -i :8000 >/dev/null 2>&1; then
    echo "✅ 端口 8000 正在监听"
    sudo lsof -i :8000
else
    echo "❌ 端口 8000 未被占用（后端可能未运行）"
fi
echo ""

# 5. 测试后端 API
echo "[5] 测试后端 API..."
echo "----------------------------------------"
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null | grep -q "200\|404"; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health)
    echo "✅ 后端 API 响应 (HTTP $HTTP_CODE)"
    curl -s http://127.0.0.1:8000/health | head -5
else
    echo "❌ 后端 API 无响应"
fi
echo ""

# 6. 检查 Redis 连接
echo "[6] 检查 Redis 连接..."
echo "----------------------------------------"
ACTUAL_PASSWORD=$(sudo grep "^requirepass" /etc/redis/redis.conf 2>/dev/null | awk '{print $2}')
if [ -n "$ACTUAL_PASSWORD" ]; then
    if redis-cli -a "$ACTUAL_PASSWORD" -h 127.0.0.1 PING 2>/dev/null | grep -q "PONG"; then
        echo "✅ Redis 连接正常"
    else
        echo "❌ Redis 连接失败"
    fi
else
    echo "⚠️  无法获取 Redis 密码"
fi
echo ""

echo "=========================================="
echo "检查完成"
echo "=========================================="
echo ""
echo "如果后端未运行，需要启动后端服务"
echo ""
