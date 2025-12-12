#!/bin/bash
# 诊断后端服务问题

set -e

echo "=========================================="
echo "诊断后端服务问题"
echo "=========================================="

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
ADMIN_BACKEND="$PROJECT_ROOT/admin-backend"
VENV_PATH="$ADMIN_BACKEND/.venv"

echo ""
echo "[1] 检查服务状态..."
sudo systemctl status luckyred-api --no-pager -l | head -20

echo ""
echo "[2] 检查端口 8000 监听..."
if sudo ss -tlnp | grep -q ":8000"; then
    echo "✅ 端口 8000 正在监听"
    sudo ss -tlnp | grep ":8000"
else
    echo "❌ 端口 8000 未监听"
fi

echo ""
echo "[3] 检查进程..."
if pgrep -f "uvicorn.*8000" > /dev/null; then
    echo "✅ uvicorn 进程存在"
    ps aux | grep "uvicorn.*8000" | grep -v grep
else
    echo "❌ uvicorn 进程不存在"
fi

echo ""
echo "[4] 检查服务日志（最近30行）..."
sudo journalctl -u luckyred-api -n 30 --no-pager | tail -30

echo ""
echo "[5] 测试本地连接..."
echo -n "测试 http://localhost:8000/api/v1/health ... "
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://localhost:8000/api/v1/health" 2>&1 || echo "000")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "✅ HTTP $HEALTH_RESPONSE"
    curl -s "http://localhost:8000/api/v1/health" | head -5
else
    echo "❌ HTTP $HEALTH_RESPONSE 或连接失败"
    echo "   详细错误:"
    curl -v "http://localhost:8000/api/v1/health" 2>&1 | head -10 || echo "   无法连接"
fi

echo ""
echo "[6] 检查 Python 环境..."
cd "$ADMIN_BACKEND"
if [ -f "$VENV_PATH/bin/python3" ]; then
    echo "✅ Python 环境存在"
    echo "   Python 版本: $($VENV_PATH/bin/python3 --version)"
    echo "   uvicorn 路径: $($VENV_PATH/bin/which uvicorn || echo '未找到')"
else
    echo "❌ Python 环境不存在"
fi

echo ""
echo "[7] 检查代码和配置..."
if [ -f "$ADMIN_BACKEND/app/main.py" ]; then
    echo "✅ main.py 存在"
    # 检查导入
    source "$VENV_PATH/bin/activate" 2>/dev/null || true
    if python3 -c "import app.main" 2>/dev/null; then
        echo "✅ 可以导入 app.main"
    else
        echo "❌ 无法导入 app.main"
        python3 -c "import app.main" 2>&1 | head -10
    fi
else
    echo "❌ main.py 不存在"
fi

echo ""
echo "[8] 尝试手动启动测试..."
cd "$ADMIN_BACKEND"
source "$VENV_PATH/bin/activate" 2>/dev/null || true

# 检查是否可以启动（不实际启动，只检查命令）
if command -v uvicorn > /dev/null; then
    echo "✅ uvicorn 命令可用"
    echo "   测试命令: uvicorn app.main:app --host 0.0.0.0 --port 8000"
    echo "   （不实际启动，只检查命令是否可用）"
else
    echo "❌ uvicorn 命令不可用"
    echo "   尝试安装: pip install uvicorn[standard]"
fi

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "建议的修复步骤："
echo "1. 如果端口未监听，重启服务: sudo systemctl restart luckyred-api"
echo "2. 如果服务启动失败，查看详细日志: sudo journalctl -u luckyred-api -n 100"
echo "3. 如果导入失败，检查依赖: cd $ADMIN_BACKEND && source $VENV_PATH/bin/activate && pip install -r requirements.txt"
echo ""

