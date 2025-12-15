#!/bin/bash
# ============================================================
# 修复部署问题：Node.js版本、数据库权限、服务配置
# ============================================================

set -e

echo "=========================================="
echo "🔧 修复部署问题"
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

# 1. 升级 Node.js 到 20+
echo "[1/6] 升级 Node.js 到 20+..."
echo "----------------------------------------"
NODE_VERSION=$(node -v 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1 || echo "0")
echo "当前 Node.js 版本: $(node -v 2>/dev/null || echo '未安装')"

if [ "$NODE_VERSION" -lt 20 ]; then
    echo "Node.js 版本过低，升级到 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
    echo "✅ Node.js 已升级到: $(node -v)"
else
    echo "✅ Node.js 版本符合要求: $(node -v)"
fi
echo ""

# 2. 修复数据库权限
echo "[2/6] 修复数据库权限..."
echo "----------------------------------------"
DB_DIR="$BACKEND_DIR/data"
DB_FILE="$DB_DIR/app.db"

# 创建数据目录（如果不存在）
mkdir -p "$DB_DIR"

# 修复目录和文件权限
chown -R ubuntu:ubuntu "$DB_DIR"
chmod -R 755 "$DB_DIR"

if [ -f "$DB_FILE" ]; then
    chown ubuntu:ubuntu "$DB_FILE"
    chmod 664 "$DB_FILE"
    echo "✅ 数据库文件权限已修复"
else
    echo "⚠️  数据库文件不存在，将在下一步创建"
fi

# 确保整个项目目录权限正确
chown -R ubuntu:ubuntu "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"

echo "✅ 权限修复完成"
echo ""

# 3. 停止现有服务
echo "[3/6] 停止现有服务..."
echo "----------------------------------------"
systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
systemctl stop "$FRONTEND_SERVICE" 2>/dev/null || true
sleep 2
echo "✅ 服务已停止"
echo ""

# 4. 重新初始化数据库（如果需要）
echo "[4/6] 检查并初始化数据库..."
echo "----------------------------------------"
cd "$BACKEND_DIR"

if [ ! -f "$DB_FILE" ]; then
    echo "数据库不存在，正在初始化..."
    source venv/bin/activate
    python3 -c "
from app.db import Base, engine
from app.models import *
Base.metadata.create_all(bind=engine)
print('数据库初始化完成')
"
    deactivate
    
    # 再次修复权限
    chown -R ubuntu:ubuntu "$DB_DIR"
    chmod -R 755 "$DB_DIR"
    [ -f "$DB_FILE" ] && chmod 664 "$DB_FILE"
    echo "✅ 数据库已初始化"
else
    echo "✅ 数据库已存在"
fi
echo ""

# 5. 重新构建前端（使用新版本的 Node.js）
echo "[5/6] 重新构建前端..."
echo "----------------------------------------"
cd "$FRONTEND_DIR"

# 清理旧的构建
if [ -d ".next" ]; then
    echo "清理旧的构建..."
    rm -rf .next
fi

# 确保权限正确
chown -R ubuntu:ubuntu .

# 重新构建
echo "开始构建（使用 Node.js $(node -v)）..."
if sudo -u ubuntu npm run build; then
    echo "✅ 前端构建成功"
else
    echo "❌ 前端构建失败"
    exit 1
fi

# 验证 standalone 目录
if [ ! -d ".next/standalone" ] || [ ! -f ".next/standalone/server.js" ]; then
    echo "❌ standalone 构建不完整"
    exit 1
fi

echo "✅ standalone 构建验证通过"
echo ""

# 6. 部署服务配置
echo "[6/6] 部署服务配置..."
echo "----------------------------------------"

# 后端服务（确保权限正确）
cat > /etc/systemd/system/$BACKEND_SERVICE.service <<EOF
[Unit]
Description=LuckyRed API Service (FastAPI)
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONPATH=$BACKEND_DIR"
EnvironmentFile=$BACKEND_DIR/.env

ExecStart=$BACKEND_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=luckyred-api

NoNewPrivileges=true
PrivateTmp=true
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# 前端服务
cat > /etc/systemd/system/$FRONTEND_SERVICE.service <<EOF
[Unit]
Description=Liaotian Next.js Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$FRONTEND_DIR/.next/standalone
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=NODE_OPTIONS=--max-old-space-size=1024
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
systemctl enable "$BACKEND_SERVICE"
systemctl enable "$FRONTEND_SERVICE"

echo "✅ 服务配置已部署"
echo ""

# 启动服务
echo "启动服务..."
systemctl start "$BACKEND_SERVICE"
sleep 5

if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    echo "✅ 后端服务已启动"
else
    echo "❌ 后端服务启动失败"
    systemctl status "$BACKEND_SERVICE" --no-pager -l | head -20
    echo ""
    echo "查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
    exit 1
fi

systemctl start "$FRONTEND_SERVICE"
sleep 5

if systemctl is-active --quiet "$FRONTEND_SERVICE"; then
    echo "✅ 前端服务已启动"
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

# 检查服务状态
echo "服务状态:"
BACKEND_STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "inactive")
FRONTEND_STATUS=$(systemctl is-active "$FRONTEND_SERVICE" 2>/dev/null || echo "inactive")
echo "  后端 ($BACKEND_SERVICE): $BACKEND_STATUS"
echo "  前端 ($FRONTEND_SERVICE): $FRONTEND_STATUS"
echo ""

# 检查端口
echo "端口监听:"
PORT_8000=$(lsof -ti:8000 2>/dev/null || true)
PORT_3000=$(lsof -ti:3000 2>/dev/null || true)
if [ -n "$PORT_8000" ]; then
    echo "  端口 8000: ✅ 正在监听 (PID: $PORT_8000)"
else
    echo "  端口 8000: ❌ 未监听"
fi
if [ -n "$PORT_3000" ]; then
    echo "  端口 3000: ✅ 正在监听 (PID: $PORT_3000)"
else
    echo "  端口 3000: ❌ 未监听"
fi
echo ""

# 测试服务
echo "服务响应测试:"
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    echo "  后端健康检查: ✅ HTTP 200"
else
    echo "  后端健康检查: ❌ HTTP $BACKEND_HEALTH"
fi

FRONTEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/login 2>/dev/null || echo "000")
if [ "$FRONTEND_TEST" = "200" ]; then
    echo "  前端登录页面: ✅ HTTP 200"
else
    echo "  前端登录页面: ❌ HTTP $FRONTEND_TEST"
fi
echo ""

echo "=========================================="
echo "✅ 所有修复完成"
echo "=========================================="
echo ""
echo "下一步操作:"
echo "1. 配置 SSL 证书（可选）:"
echo "   sudo certbot --nginx -d aikz.usdt2026.cc --register-unsafely-without-email"
echo ""
echo "2. 编辑环境变量，填入 API 密钥:"
echo "   sudo nano $BACKEND_DIR/.env"
echo ""
echo "3. 重启服务使配置生效:"
echo "   sudo systemctl restart $BACKEND_SERVICE"
echo "   sudo systemctl restart $FRONTEND_SERVICE"
echo ""

