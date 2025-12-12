#!/bin/bash
# ============================================================
# 诊断后端服务启动问题
# ============================================================

echo "=========================================="
echo "诊断后端服务启动问题"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"

# 1. 检查服务状态
echo "[1/6] 检查服务状态..."
BACKEND_SERVICE=""
if systemctl cat luckyred-api.service >/dev/null 2>&1; then
    BACKEND_SERVICE="luckyred-api"
elif systemctl cat telegram-backend.service >/dev/null 2>&1; then
    BACKEND_SERVICE="telegram-backend"
fi

if [ -z "$BACKEND_SERVICE" ]; then
    echo "  ❌ 后端服务未找到"
    exit 1
fi

STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
echo "  服务: $BACKEND_SERVICE"
echo "  状态: $STATUS"
echo ""

# 2. 检查端口占用
echo "[2/6] 检查端口 8000 占用..."
PORT_8000_PID=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || echo "")
if [ -n "$PORT_8000_PID" ]; then
    echo "  ⚠️  端口 8000 被进程 $PORT_8000_PID 占用"
    PROCESS_CMD=$(ps -p "$PORT_8000_PID" -o cmd --no-headers 2>/dev/null | head -1 || echo "")
    if [ -n "$PROCESS_CMD" ]; then
        echo "  进程命令: $PROCESS_CMD"
    fi
else
    echo "  ✅ 端口 8000 未被占用"
fi
echo ""

# 3. 检查后端代码和依赖
echo "[3/6] 检查后端代码和依赖..."
if [ ! -d "$BACKEND_DIR" ]; then
    echo "  ❌ 后端目录不存在: $BACKEND_DIR"
    exit 1
fi

if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "  ❌ 虚拟环境不存在: $BACKEND_DIR/venv"
    exit 1
fi

if [ ! -f "$BACKEND_DIR/venv/bin/uvicorn" ]; then
    echo "  ❌ uvicorn 未安装"
    exit 1
fi

echo "  ✅ 后端代码和依赖正常"
echo ""

# 4. 检查环境变量
echo "[4/6] 检查环境变量..."
if [ -f "$BACKEND_DIR/.env" ]; then
    echo "  ✅ .env 文件存在"
else
    echo "  ⚠️  .env 文件不存在"
fi

# 检查关键环境变量
if [ -f "$BACKEND_DIR/.env" ]; then
    if grep -q "DATABASE_URL" "$BACKEND_DIR/.env"; then
        echo "  ✅ DATABASE_URL 已配置"
    else
        echo "  ⚠️  DATABASE_URL 未配置"
    fi
fi
echo ""

# 5. 检查服务日志
echo "[5/6] 检查服务日志（最近50行）..."
echo "  错误和警告:"
sudo journalctl -u "$BACKEND_SERVICE" -n 50 --no-pager 2>/dev/null | grep -iE "error|warning|traceback|failed|exception" | tail -20 || echo "  未找到错误"
echo ""

# 6. 尝试手动启动测试
echo "[6/6] 尝试手动启动测试..."
cd "$BACKEND_DIR" || exit 1

# 激活虚拟环境并测试启动
source venv/bin/activate

echo "  测试 uvicorn 命令..."
if python3 -c "import uvicorn; print('✅ uvicorn 可导入')" 2>/dev/null; then
    echo "  ✅ uvicorn 可导入"
else
    echo "  ❌ uvicorn 无法导入"
    exit 1
fi

echo "  测试 app.main 模块..."
if python3 -c "from app.main import app; print('✅ app.main 可导入')" 2>/dev/null; then
    echo "  ✅ app.main 可导入"
else
    echo "  ❌ app.main 无法导入"
    echo "  错误详情:"
    python3 -c "from app.main import app" 2>&1 | head -10
    exit 1
fi

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "如果服务状态为 active 但端口未监听，可能原因："
echo "  1. 服务启动后立即崩溃"
echo "  2. 端口被其他进程占用"
echo "  3. 服务配置错误"
echo ""
echo "建议操作："
echo "  1. 查看完整日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager"
echo "  2. 检查服务配置: sudo systemctl cat $BACKEND_SERVICE"
echo "  3. 手动测试启动: cd $BACKEND_DIR && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""

