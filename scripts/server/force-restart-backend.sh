#!/bin/bash
# ============================================================
# 强制重启后端服务脚本（彻底清理端口冲突）
# ============================================================

set +e # 不在第一个错误时退出

echo "=========================================="
echo "🔧 强制重启后端服务"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_SERVICE="luckyred-api"
BACKEND_PORT=8000

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo "此脚本需要 root 权限，请使用 sudo 运行"
    echo "使用方法: sudo bash $0"
    exit 1
fi

# 1. 停止后端服务
echo "[1/5] 停止后端服务..."
echo "----------------------------------------"
systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
sleep 2
echo "✅ 后端服务已停止"
echo ""

# 2. 彻底清理所有占用端口的进程
echo "[2/5] 清理占用端口 $BACKEND_PORT 的所有进程..."
echo "----------------------------------------"
# 查找所有占用端口的进程
PORT_PIDS=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
if [ -n "$PORT_PIDS" ]; then
    echo "发现占用端口 $BACKEND_PORT 的进程: $PORT_PIDS"
    for PID in $PORT_PIDS; do
        echo "  终止进程 $PID ($(ps -p $PID -o comm= 2>/dev/null || echo 'unknown'))"
        kill -9 $PID 2>/dev/null || true
    done
    sleep 2
    
    # 再次检查
    REMAINING_PIDS=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
    if [ -n "$REMAINING_PIDS" ]; then
        echo "⚠️  警告: 仍有进程占用端口，强制终止..."
        for PID in $REMAINING_PIDS; do
            kill -9 $PID 2>/dev/null || true
        done
        sleep 1
    fi
    echo "✅ 端口 $BACKEND_PORT 已释放"
else
    echo "✅ 端口 $BACKEND_PORT 未被占用"
fi
echo ""

# 3. 清理所有相关的 Python 进程
echo "[3/5] 清理所有相关的 Python 进程..."
echo "----------------------------------------"
# 查找所有 uvicorn/gunicorn 进程
UVICORN_PIDS=$(pgrep -f "uvicorn.*main:app" 2>/dev/null || true)
GUNICORN_PIDS=$(pgrep -f "gunicorn.*main:app" 2>/dev/null || true)
PYTHON_PIDS=$(pgrep -f "python.*app.main" 2>/dev/null || true)

ALL_PIDS="$UVICORN_PIDS $GUNICORN_PIDS $PYTHON_PIDS"
if [ -n "$ALL_PIDS" ]; then
    echo "发现相关进程: $ALL_PIDS"
    for PID in $ALL_PIDS; do
        if [ -n "$PID" ]; then
            echo "  终止进程 $PID ($(ps -p $PID -o comm=,args= 2>/dev/null | head -1 || echo 'unknown'))"
            kill -9 $PID 2>/dev/null || true
        fi
    done
    sleep 1
    echo "✅ 相关进程已清理"
else
    echo "✅ 未发现相关进程"
fi
echo ""

# 4. 验证端口已释放
echo "[4/5] 验证端口已释放..."
echo "----------------------------------------"
sleep 1
FINAL_CHECK=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
if [ -n "$FINAL_CHECK" ]; then
    echo "❌ 错误: 端口 $BACKEND_PORT 仍被占用: $FINAL_CHECK"
    echo "尝试最后一次强制清理..."
    for PID in $FINAL_CHECK; do
        kill -9 $PID 2>/dev/null || true
    done
    sleep 1
    FINAL_CHECK2=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
    if [ -n "$FINAL_CHECK2" ]; then
        echo "❌ 无法释放端口，请手动检查: sudo lsof -i:8000"
        exit 1
    fi
fi
echo "✅ 端口 $BACKEND_PORT 已完全释放"
echo ""

# 5. 重新加载 systemd 并启动服务
echo "[5/5] 重新加载 systemd 并启动服务..."
echo "----------------------------------------"
systemctl daemon-reload
sleep 1
systemctl start "$BACKEND_SERVICE"
sleep 5

# 检查服务状态
if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    echo "✅ 后端服务启动成功"
    systemctl status "$BACKEND_SERVICE" --no-pager -l | head -15
else
    echo "❌ 后端服务启动失败"
    echo "查看错误信息:"
    systemctl status "$BACKEND_SERVICE" --no-pager -l | head -20
    echo ""
    echo "查看详细日志:"
    journalctl -u "$BACKEND_SERVICE" -n 50 --no-pager | tail -30
    exit 1
fi
echo ""

# 6. 验证端口监听
echo "[6/6] 验证端口监听..."
echo "----------------------------------------"
sleep 2
if ss -tlnp | grep -q ":$BACKEND_PORT "; then
    echo "✅ 端口 $BACKEND_PORT 正在监听"
    ss -tlnp | grep ":$BACKEND_PORT " | head -3
    LISTENING_PID=$(ss -tlnp | grep ":$BACKEND_PORT " | grep -oP 'pid=\K\d+' | head -1)
    SERVICE_PID=$(systemctl show "$BACKEND_SERVICE" -p MainPID --value)
    if [ "$LISTENING_PID" = "$SERVICE_PID" ]; then
        echo "✅ 端口监听的进程与服务主进程一致 (PID: $SERVICE_PID)"
    else
        echo "⚠️  警告: 端口监听的进程 (PID: $LISTENING_PID) 与服务主进程 (PID: $SERVICE_PID) 不一致"
    fi
else
    echo "❌ 端口 $BACKEND_PORT 未监听"
    exit 1
fi
echo ""

# 7. 测试 API
echo "[7/7] 测试 API..."
echo "----------------------------------------"
sleep 1
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$BACKEND_PORT/health 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ] || [ "$HTTP_CODE" = "405" ]; then
    echo "✅ 后端服务响应正常 (HTTP $HTTP_CODE)"
    if [ "$HTTP_CODE" = "405" ]; then
        echo "   提示: /health 端点可能只支持 GET 请求"
    fi
else
    echo "⚠️  后端服务响应异常 (HTTP $HTTP_CODE)"
    echo "   尝试完整请求:"
    curl -v http://127.0.0.1:$BACKEND_PORT/health 2>&1 | head -10
fi
echo ""

echo "=========================================="
echo "✅ 强制重启完成"
echo "=========================================="
echo ""
echo "如果仍然出现 502 错误，请检查:"
echo "1. Nginx 配置: sudo nginx -t"
echo "2. Nginx 日志: sudo tail -50 /var/log/nginx/error.log"
echo "3. 后端日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager"
echo ""

