#!/bin/bash
# 修复 502 Bad Gateway 错误

set -e

echo "=========================================="
echo "修复 502 Bad Gateway 错误"
echo "=========================================="

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
ADMIN_BACKEND="$PROJECT_ROOT/admin-backend"
VENV_PATH="$ADMIN_BACKEND/.venv"

cd "$PROJECT_ROOT"

echo ""
echo "[1/8] 检查后端服务状态..."
if sudo systemctl is-active --quiet luckyred-api; then
    echo "✅ 后端服务正在运行"
else
    echo "❌ 后端服务未运行"
    echo "   尝试启动服务..."
    sudo systemctl start luckyred-api
    sleep 3
    if sudo systemctl is-active --quiet luckyred-api; then
        echo "✅ 后端服务已启动"
    else
        echo "❌ 后端服务启动失败"
    fi
fi

echo ""
echo "[2/8] 检查后端服务日志（最近20行）..."
sudo journalctl -u luckyred-api -n 20 --no-pager | tail -20

echo ""
echo "[3/8] 检查端口 8000 占用..."
PORT_PID=$(sudo lsof -ti:8000 || echo "")
if [ -n "$PORT_PID" ]; then
    echo "⚠️  端口 8000 被占用 (PID: $PORT_PID)"
    echo "   检查进程信息..."
    ps aux | grep $PORT_PID | head -5
else
    echo "❌ 端口 8000 未被占用（后端服务可能未启动）"
fi

echo ""
echo "[4/8] 检查后端服务配置..."
if [ -f "/etc/systemd/system/luckyred-api.service" ]; then
    echo "✅ 服务配置文件存在"
    echo "   检查工作目录和命令..."
    grep -E "WorkingDirectory|ExecStart" /etc/systemd/system/luckyred-api.service
else
    echo "❌ 服务配置文件不存在"
fi

echo ""
echo "[5/8] 检查 Python 虚拟环境..."
if [ -d "$VENV_PATH" ]; then
    echo "✅ 虚拟环境存在: $VENV_PATH"
    if [ -f "$VENV_PATH/bin/python3" ]; then
        echo "✅ Python 可执行文件存在"
        echo "   Python 版本: $($VENV_PATH/bin/python3 --version)"
    else
        echo "❌ Python 可执行文件不存在"
    fi
else
    echo "❌ 虚拟环境不存在: $VENV_PATH"
    echo "   创建虚拟环境..."
    cd "$ADMIN_BACKEND"
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    pip install -q -r requirements.txt || echo "⚠️  依赖安装可能失败"
fi

echo ""
echo "[6/8] 检查后端代码..."
if [ -f "$ADMIN_BACKEND/app/main.py" ]; then
    echo "✅ 后端代码存在"
    # 检查 Python 语法
    cd "$ADMIN_BACKEND"
    source "$VENV_PATH/bin/activate" 2>/dev/null || true
    if python3 -m py_compile app/main.py 2>/dev/null; then
        echo "✅ Python 语法正确"
    else
        echo "❌ Python 语法错误"
        python3 -m py_compile app/main.py
    fi
else
    echo "❌ 后端代码不存在"
fi

echo ""
echo "[7/8] 清理并重启后端服务..."
# 停止服务
sudo systemctl stop luckyred-api || true
sleep 2

# 清理端口
if [ -n "$PORT_PID" ]; then
    echo "   清理端口 8000 (PID: $PORT_PID)..."
    sudo kill -9 $PORT_PID 2>/dev/null || true
    sleep 2
fi

# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
echo "   启动后端服务..."
sudo systemctl start luckyred-api
sleep 5

# 检查服务状态
if sudo systemctl is-active --quiet luckyred-api; then
    echo "✅ 后端服务已启动"
else
    echo "❌ 后端服务启动失败"
    echo "   查看详细日志:"
    sudo journalctl -u luckyred-api -n 50 --no-pager | tail -30
fi

echo ""
echo "[8/8] 测试后端连接..."
sleep 3

# 测试本地连接
LOCAL_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/v1/health" 2>/dev/null || echo "000")
if [ "$LOCAL_RESPONSE" = "200" ] || [ "$LOCAL_RESPONSE" = "404" ]; then
    echo "✅ 本地连接成功 (HTTP $LOCAL_RESPONSE)"
else
    echo "❌ 本地连接失败 (HTTP $LOCAL_RESPONSE)"
fi

# 测试 API 端点
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/v1/group-ai/ai-provider/providers" 2>/dev/null || echo "000")
if [ "$API_RESPONSE" = "200" ] || [ "$API_RESPONSE" = "401" ] || [ "$API_RESPONSE" = "403" ]; then
    echo "✅ API 端点可访问 (HTTP $API_RESPONSE)"
else
    echo "⚠️  API 端点返回 HTTP $API_RESPONSE"
fi

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请检查："
echo "1. 后端服务日志: sudo journalctl -u luckyred-api -n 100"
echo "2. Nginx 配置: sudo nginx -t"
echo "3. Nginx 日志: sudo tail -f /var/log/nginx/error.log"
echo "4. 端口监听: sudo ss -tlnp | grep 8000"
echo ""

