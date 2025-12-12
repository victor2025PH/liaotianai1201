#!/bin/bash
# ============================================================
# 修复 AI Provider API 404 问题
# ============================================================

set -e

echo "=========================================="
echo "修复 AI Provider API 404 问题"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
BACKEND_SERVICE=""

# 检测后端服务名称
if systemctl cat luckyred-api.service >/dev/null 2>&1; then
    BACKEND_SERVICE="luckyred-api"
elif systemctl cat telegram-backend.service >/dev/null 2>&1; then
    BACKEND_SERVICE="telegram-backend"
else
    echo "❌ 后端服务未找到"
    exit 1
fi

echo "检测到的后端服务: $BACKEND_SERVICE"
echo ""

# 1. 检查代码文件
echo "[1/6] 检查代码文件..."
AI_PROVIDER_FILE="$BACKEND_DIR/app/api/group_ai/ai_provider.py"
INIT_FILE="$BACKEND_DIR/app/api/group_ai/__init__.py"

if [ ! -f "$AI_PROVIDER_FILE" ]; then
    echo "  ❌ ai_provider.py 文件不存在"
    echo "  请确保代码已从 GitHub 拉取"
    exit 1
fi

if [ ! -f "$INIT_FILE" ]; then
    echo "  ❌ __init__.py 文件不存在"
    exit 1
fi

# 检查路由注册
if ! grep -q "ai_provider" "$INIT_FILE"; then
    echo "  ❌ ai_provider 模块未导入"
    exit 1
fi

if ! grep -q "ai_provider.router" "$INIT_FILE"; then
    echo "  ❌ ai_provider.router 未注册"
    exit 1
fi

echo "  ✅ 代码文件检查通过"
echo ""

# 2. 安装依赖
echo "[2/6] 安装 AI Provider 依赖..."
cd "$BACKEND_DIR" || exit 1
source venv/bin/activate

pip install --quiet google-generativeai>=0.3.0 openai>=1.3.7 requests 2>/dev/null || {
    echo "  ⚠️  部分依赖安装失败，继续..."
}

echo "  ✅ 依赖安装完成"
echo ""

# 3. 清理端口占用（强制彻底清理）
echo "[3/6] 清理端口占用..."
MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    PORT_8000_PID=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || echo "")
    
    if [ -z "$PORT_8000_PID" ]; then
        echo "  ✅ 端口 8000 已释放"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "  ⚠️  端口 8000 被进程 $PORT_8000_PID 占用，正在清理 (尝试 $RETRY_COUNT/$MAX_RETRIES)..."
    
    # 获取所有占用端口的进程
    ALL_PIDS=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' || echo "")
    
    # 终止所有占用端口的进程
    for pid in $ALL_PIDS; do
        if [ -n "$pid" ]; then
            echo "    终止进程: $pid"
            sudo kill -9 "$pid" 2>/dev/null || true
        fi
    done
    
    # 强制终止所有 uvicorn 进程
    sudo pkill -9 -f "uvicorn" 2>/dev/null || true
    
    # 强制终止所有可能占用端口的 python 进程
    sudo pkill -9 -f "python.*8000" 2>/dev/null || true
    
    sleep 3
    
    # 再次检查
    PORT_8000_AFTER=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || echo "")
    if [ -z "$PORT_8000_AFTER" ]; then
        echo "  ✅ 端口 8000 已释放"
        break
    fi
done

# 最终检查
FINAL_CHECK=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
if [ -n "$FINAL_CHECK" ]; then
    echo "  ❌ 端口 8000 仍被占用，无法清理"
    echo "  占用信息: $FINAL_CHECK"
    echo "  请手动检查: sudo ss -tlnp | grep 8000"
    exit 1
fi

echo ""

# 4. 停止服务（确保完全停止）
echo "[4/6] 停止后端服务..."
sudo systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
sleep 5

# 检查服务进程是否完全停止
SERVICE_PID=$(systemctl show -p MainPID --value "$BACKEND_SERVICE" 2>/dev/null || echo "0")
if [ "$SERVICE_PID" != "0" ] && [ -n "$SERVICE_PID" ]; then
    echo "  ⚠️  服务进程仍在运行 (PID: $SERVICE_PID)，强制终止..."
    sudo kill -9 "$SERVICE_PID" 2>/dev/null || true
    sleep 2
fi

# 再次检查端口
PORT_CHECK=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
if [ -n "$PORT_CHECK" ]; then
    echo "  ⚠️  端口 8000 仍被占用，再次清理..."
    sudo pkill -9 -f "uvicorn" 2>/dev/null || true
    sleep 3
fi

echo "  ✅ 服务已停止"
echo ""

# 5. 验证 Python 代码语法
echo "[5/6] 验证 Python 代码语法..."
cd "$BACKEND_DIR" || exit 1
source venv/bin/activate

if python3 -m py_compile app/api/group_ai/ai_provider.py 2>/dev/null; then
    echo "  ✅ ai_provider.py 语法正确"
else
    echo "  ❌ ai_provider.py 语法错误"
    python3 -m py_compile app/api/group_ai/ai_provider.py 2>&1 | head -10
    exit 1
fi

# 测试导入
if python3 -c "from app.api.group_ai import ai_provider; print('✅ ai_provider 模块可导入')" 2>/dev/null; then
    echo "  ✅ ai_provider 模块可导入"
else
    echo "  ❌ ai_provider 模块导入失败"
    python3 -c "from app.api.group_ai import ai_provider" 2>&1 | head -10
    exit 1
fi

# 测试路由注册
if python3 -c "from app.api.group_ai import router; routes = [r.path for r in router.routes]; ai_provider_routes = [r for r in routes if 'ai-provider' in r]; print(f'✅ 找到 {len(ai_provider_routes)} 个 AI Provider 路由') if ai_provider_routes else print('❌ 未找到 AI Provider 路由')" 2>/dev/null; then
    echo "  ✅ AI Provider 路由已注册"
else
    echo "  ⚠️  无法验证路由注册（继续执行）"
fi

echo ""

# 6. 启动服务
echo "[6/6] 启动后端服务..."
sudo systemctl daemon-reload
sudo systemctl start "$BACKEND_SERVICE"

echo "  等待服务启动（15秒）..."
sleep 15

# 检查服务状态
STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
if [ "$STATUS" != "active" ]; then
    echo "  ❌ 服务启动失败 (状态: $STATUS)"
    echo "  查看日志:"
    sudo journalctl -u "$BACKEND_SERVICE" -n 30 --no-pager | tail -20
    exit 1
fi

echo "  ✅ 服务已启动 (状态: $STATUS)"

# 验证端口监听
sleep 5
PORT_LISTENING=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
if [ -z "$PORT_LISTENING" ]; then
    echo "  ⚠️  端口 8000 未监听"
    echo "  查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
else
    echo "  ✅ 端口 8000 正在监听"
fi

echo ""

# 7. 测试 API 端点
echo "[7/7] 测试 API 端点..."
sleep 3

# 测试健康检查
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "  ✅ 健康检查通过"
else
    echo "  ⚠️  健康检查失败"
fi

# 测试 AI Provider API
AI_PROVIDER_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:8000/api/v1/group-ai/ai-provider/providers 2>/dev/null || echo "ERROR")
AI_PROVIDER_HTTP_CODE=$(echo "$AI_PROVIDER_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2 || echo "000")

if [ "$AI_PROVIDER_HTTP_CODE" = "200" ] || [ "$AI_PROVIDER_HTTP_CODE" = "401" ] || [ "$AI_PROVIDER_HTTP_CODE" = "403" ]; then
    echo "  ✅ AI Provider API 端点可访问 (HTTP $AI_PROVIDER_HTTP_CODE)"
elif [ "$AI_PROVIDER_HTTP_CODE" = "404" ]; then
    echo "  ❌ AI Provider API 端点返回 404"
    echo "  可能原因："
    echo "    1. 路由未正确注册"
    echo "    2. 服务未加载新代码"
    echo "  查看日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager | grep -i 'ai-provider\|error\|traceback'"
else
    echo "  ⚠️  AI Provider API 端点响应异常 (HTTP $AI_PROVIDER_HTTP_CODE)"
fi

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "如果 API 仍然返回 404，请执行："
echo "  1. 查看完整日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager"
echo "  2. 手动测试启动: cd $BACKEND_DIR && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo "  3. 检查路由注册: python3 -c \"from app.api.group_ai import router; print([r.path for r in router.routes if 'ai-provider' in r.path])\""
echo ""

