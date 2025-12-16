#!/bin/bash
# ============================================================
# Fix Frontend Service Path (Server Environment - Linux)
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Fix systemd service path for Next.js 16 standalone output
#
# One-click execution: sudo bash scripts/server/fix-frontend-service-path.sh
# ============================================================

set -e

echo "============================================================"
echo "🔧 修复前端服务路径"
echo "============================================================"
echo ""

SERVICE_FILE="/etc/systemd/system/liaotian-frontend.service"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

# 检查 server.js 实际位置
echo "[1/4] 检查 server.js 实际位置"
echo "----------------------------------------"
cd "$FRONTEND_DIR" || {
  echo "❌ 无法进入前端目录: $FRONTEND_DIR"
  exit 1
}

SERVER_JS=$(find .next -name "server.js" -type f 2>/dev/null | grep -v node_modules | head -1)
if [ -z "$SERVER_JS" ]; then
  echo "❌ 未找到 server.js 文件，需要先构建前端"
  exit 1
fi

echo "✅ 找到 server.js: $SERVER_JS"
ls -la "$SERVER_JS"

# 转换为绝对路径
if [[ "$SERVER_JS" == ./* ]]; then
  SERVER_JS_ABS="$FRONTEND_DIR/${SERVER_JS#./}"
else
  SERVER_JS_ABS="$FRONTEND_DIR/$SERVER_JS"
fi

echo "绝对路径: $SERVER_JS_ABS"

# 转换为相对路径（从 WorkingDirectory 开始）
SERVER_JS_REL="${SERVER_JS#./}"
echo "相对路径（从 WorkingDirectory）: $SERVER_JS_REL"

echo ""
echo "[2/4] 备份当前服务配置"
echo "----------------------------------------"
if [ -f "$SERVICE_FILE" ]; then
  sudo cp "$SERVICE_FILE" "${SERVICE_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
  echo "✅ 已备份到: ${SERVICE_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
else
  echo "⚠️  服务文件不存在，将创建新文件"
fi

echo ""
echo "[3/4] 更新服务配置"
echo "----------------------------------------"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
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
# Next.js 16 standalone 输出在 .next/standalone/saas-demo/ 目录下
ExecStart=/usr/bin/node $SERVER_JS_REL
Restart=always
RestartSec=5
LimitNOFILE=65535

StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-frontend

[Install]
WantedBy=multi-user.target
EOF

echo "✅ 服务配置已更新"
echo ""
echo "新的 ExecStart 路径: $SERVER_JS_REL"

echo ""
echo "[4/4] 重新加载并启动服务"
echo "----------------------------------------"
sudo systemctl daemon-reload
echo "✅ systemd 配置已重新加载"

sudo systemctl stop liaotian-frontend 2>/dev/null || true
sleep 2

sudo systemctl start liaotian-frontend
echo "✅ 服务已启动"

sleep 5

echo ""
echo "=== 服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -15

echo ""
echo "=== 端口监听 ==="
sudo ss -tlnp | grep :3000 || echo "端口 3000 未监听"

echo ""
echo "=== 本地测试 ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:3000 || echo "连接失败"

echo ""
echo "============================================================"
echo "✅ 修复完成"
echo "============================================================"

