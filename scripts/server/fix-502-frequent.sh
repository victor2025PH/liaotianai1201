#!/bin/bash
# ============================================================
# 修复频繁 502 错误脚本
# ============================================================

set +e # 不在第一个错误时退出

echo "=========================================="
echo "🔧 修复频繁 502 Bad Gateway 错误"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_SERVICE="luckyred-api"
BACKEND_PORT=8000

# 1. 先运行诊断
echo "[1/6] 运行诊断..."
echo "----------------------------------------"
if [ -f "$PROJECT_DIR/scripts/server/diagnose-502-frequent.sh" ]; then
    bash "$PROJECT_DIR/scripts/server/diagnose-502-frequent.sh"
else
    echo "⚠️  诊断脚本不存在，跳过诊断"
fi
echo ""

# 2. 停止可能冲突的进程
echo "[2/6] 停止可能冲突的进程..."
echo "----------------------------------------"
# 停止后端服务
systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
sleep 2

# 杀死占用端口的进程
PORT_PIDS=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
if [ -n "$PORT_PIDS" ]; then
    echo "发现占用端口 $BACKEND_PORT 的进程: $PORT_PIDS"
    kill -9 $PORT_PIDS 2>/dev/null || true
    sleep 1
    echo "已终止占用端口的进程"
else
    echo "端口 $BACKEND_PORT 未被占用"
fi

# 杀死所有 uvicorn/gunicorn 进程
pkill -9 -f "uvicorn.*main:app" 2>/dev/null || true
pkill -9 -f "gunicorn.*main:app" 2>/dev/null || true
sleep 1
echo "已清理后端进程"
echo ""

# 3. 检查并修复项目目录
echo "[3/6] 检查项目目录..."
echo "----------------------------------------"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 错误: 项目目录不存在: $PROJECT_DIR"
    exit 1
fi
echo "✅ 项目目录存在: $PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1
echo ""

# 4. 检查虚拟环境
echo "[4/6] 检查虚拟环境..."
echo "----------------------------------------"
VENV_PATH="$PROJECT_DIR/admin-backend/.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "⚠️  虚拟环境不存在: $VENV_PATH"
    echo "尝试创建虚拟环境..."
    cd "$PROJECT_DIR/admin-backend" || exit 1
    python3 -m venv .venv || {
        echo "❌ 创建虚拟环境失败"
        exit 1
    }
    echo "✅ 虚拟环境已创建"
else
    echo "✅ 虚拟环境存在: $VENV_PATH"
fi
echo ""

# 5. 重启后端服务
echo "[5/6] 重启后端服务..."
echo "----------------------------------------"
systemctl daemon-reload
systemctl start "$BACKEND_SERVICE"
sleep 5

if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    echo "✅ 后端服务启动成功"
    systemctl status "$BACKEND_SERVICE" --no-pager -l | head -10
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

# 6. 验证服务
echo "[6/6] 验证服务..."
echo "----------------------------------------"
sleep 3

# 检查端口
if ss -tlnp | grep -q ":$BACKEND_PORT "; then
    echo "✅ 端口 $BACKEND_PORT 正在监听"
else
    echo "❌ 端口 $BACKEND_PORT 未监听"
    exit 1
fi

# 测试 API 健康检查
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$BACKEND_PORT/health 2>/dev/null || echo "000")
if [ "$HEALTH_CHECK" = "200" ] || [ "$HEALTH_CHECK" = "404" ]; then
    echo "✅ 后端服务响应正常 (HTTP $HEALTH_CHECK)"
else
    echo "⚠️  后端服务响应异常 (HTTP $HEALTH_CHECK)"
fi

# 检查 Nginx
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 正在运行"
    systemctl reload nginx 2>/dev/null || systemctl restart nginx
    echo "✅ Nginx 已重新加载配置"
else
    echo "⚠️  Nginx 未运行，尝试启动..."
    systemctl start nginx
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "请等待 10-15 秒后测试网站是否正常"
echo "如果仍然出现 502 错误，请运行诊断脚本:"
echo "  bash $PROJECT_DIR/scripts/server/diagnose-502-frequent.sh"
echo ""

