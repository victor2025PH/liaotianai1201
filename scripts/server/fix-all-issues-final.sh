#!/bin/bash
# ============================================================
# 修复所有问题：TypeScript错误、权限、端口、服务配置
# ============================================================

set +e

echo "=========================================="
echo "🔧 修复所有问题"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"
BACKEND_SERVICE="luckyred-api"
FRONTEND_SERVICE="liaotian-frontend"

# 1. 清理端口占用
echo "[1/6] 清理端口占用..."
echo "----------------------------------------"
# 停止服务
systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
systemctl stop "$FRONTEND_SERVICE" 2>/dev/null || true
sleep 2

# 清理端口 8000
PORT_8000_PID=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$PORT_8000_PID" ]; then
    echo "清理端口 8000 (PID: $PORT_8000_PID)..."
    kill -9 $PORT_8000_PID 2>/dev/null || true
    sleep 1
fi

# 清理端口 3000
PORT_3000_PID=$(lsof -ti:3000 2>/dev/null || true)
if [ -n "$PORT_3000_PID" ]; then
    echo "清理端口 3000 (PID: $PORT_3000_PID)..."
    kill -9 $PORT_3000_PID 2>/dev/null || true
    sleep 1
fi
echo "✅ 端口已清理"
echo ""

# 2. 修复前端构建权限问题
echo "[2/6] 修复前端构建权限问题..."
echo "----------------------------------------"
cd "$FRONTEND_DIR" || exit 1

# 清理 .next 目录（修复权限问题）
if [ -d ".next" ]; then
    echo "清理 .next 目录..."
    sudo rm -rf .next
    echo "✅ .next 目录已清理"
fi

# 修复目录权限
echo "修复目录权限..."
sudo chown -R ubuntu:ubuntu "$FRONTEND_DIR"
sudo chmod -R 755 "$FRONTEND_DIR"
echo "✅ 权限已修复"
echo ""

# 3. 修复 TypeScript 错误（代码已修复，拉取最新代码）
echo "[3/6] 拉取最新代码（包含 TypeScript 修复）..."
echo "----------------------------------------"
cd "$PROJECT_DIR"
git pull origin main
echo "✅ 代码已更新"
echo ""

# 4. 重新构建前端
echo "[4/6] 重新构建前端..."
echo "----------------------------------------"
cd "$FRONTEND_DIR"

# 确保依赖已安装
if [ ! -d "node_modules" ]; then
    echo "安装依赖..."
    npm install
fi

# 构建
echo "开始构建（这可能需要几分钟）..."
npm run build

if [ ! -d ".next/standalone" ]; then
    echo "❌ 构建失败，standalone 目录不存在"
    echo "查看构建错误信息..."
    exit 1
fi

echo "✅ 前端构建完成"
cd "$PROJECT_DIR"
echo ""

# 5. 修复 systemd 服务配置
echo "[5/6] 修复 systemd 服务配置..."
echo "----------------------------------------"
# 检查 standalone 目录是否存在
if [ ! -d "$FRONTEND_DIR/.next/standalone" ]; then
    echo "❌ standalone 目录不存在，无法启动服务"
    exit 1
fi

# 更新前端服务配置（使用绝对路径）
cat > /etc/systemd/system/$FRONTEND_SERVICE.service <<EOF
[Unit]
Description=Liaotian Next.js Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$FRONTEND_DIR
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=NODE_OPTIONS=--max-old-space-size=1024
# 使用绝对路径启动 standalone 服务器
ExecStart=/usr/bin/node $FRONTEND_DIR/.next/standalone/server.js
Restart=always
RestartSec=5
LimitNOFILE=65535

StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-frontend

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "✅ 服务配置已更新"
echo ""

# 6. 启动服务
echo "[6/6] 启动服务..."
echo "----------------------------------------"
# 启动后端
echo "启动后端服务..."
systemctl start "$BACKEND_SERVICE"
sleep 5

if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    echo "✅ 后端服务已启动"
    systemctl enable "$BACKEND_SERVICE" 2>/dev/null || true
else
    echo "❌ 后端服务启动失败"
    systemctl status "$BACKEND_SERVICE" --no-pager -l | head -20
    echo ""
    echo "查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
    exit 1
fi

# 启动前端
echo "启动前端服务..."
systemctl start "$FRONTEND_SERVICE"
sleep 5

if systemctl is-active --quiet "$FRONTEND_SERVICE"; then
    echo "✅ 前端服务已启动"
    systemctl enable "$FRONTEND_SERVICE" 2>/dev/null || true
else
    echo "❌ 前端服务启动失败"
    systemctl status "$FRONTEND_SERVICE" --no-pager -l | head -20
    echo ""
    echo "查看日志: sudo journalctl -u $FRONTEND_SERVICE -n 50 --no-pager"
    exit 1
fi
echo ""

# 验证
echo "=========================================="
echo "✅ 修复完成，开始验证..."
echo "=========================================="
echo ""

sleep 3

# 检查端口
PORT_8000=$(lsof -ti:8000 2>/dev/null || true)
PORT_3000=$(lsof -ti:3000 2>/dev/null || true)

if [ -n "$PORT_8000" ]; then
    echo "✅ 端口 8000 正在监听"
else
    echo "❌ 端口 8000 未监听"
fi

if [ -n "$PORT_3000" ]; then
    echo "✅ 端口 3000 正在监听"
else
    echo "❌ 端口 3000 未监听"
fi

# 测试服务
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    echo "✅ 后端健康检查: HTTP 200"
else
    echo "❌ 后端健康检查: HTTP $BACKEND_HEALTH"
fi

FRONTEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/login 2>/dev/null || echo "000")
if [ "$FRONTEND_TEST" = "200" ]; then
    echo "✅ 前端登录页面: HTTP 200"
else
    echo "❌ 前端登录页面: HTTP $FRONTEND_TEST"
fi

echo ""
echo "=========================================="
echo "✅ 所有修复完成"
echo "=========================================="
echo ""
echo "服务状态:"
systemctl status "$BACKEND_SERVICE" --no-pager -l | head -5
systemctl status "$FRONTEND_SERVICE" --no-pager -l | head -5
echo ""

