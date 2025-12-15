#!/bin/bash
# ============================================================
# 全新服务器完整部署脚本
# ============================================================

set -e

echo "=========================================="
echo "🚀 全新服务器完整部署"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

# 配置变量
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
GIT_REPO="https://github.com/victor2025PH/liaotianai1201.git"
DOMAIN="aikz.usdt2026.cc"
BACKEND_SERVICE="luckyred-api"
FRONTEND_SERVICE="liaotian-frontend"

# 1. 更新系统
echo "[1/10] 更新系统..."
echo "----------------------------------------"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y
echo "✅ 系统更新完成"
echo ""

# 2. 安装基础依赖
echo "[2/10] 安装基础依赖..."
echo "----------------------------------------"
apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    python3.12 \
    python3.12-venv \
    python3-pip \
    nodejs \
    npm \
    nginx \
    sqlite3 \
    certbot \
    python3-certbot-nginx \
    ufw \
    fail2ban \
    htop \
    net-tools \
    software-properties-common

# 确保 Node.js 版本 >= 18
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "Node.js 版本过低，安装 Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

echo "✅ 基础依赖安装完成"
echo ""

# 3. 配置防火墙
echo "[3/10] 配置防火墙..."
echo "----------------------------------------"
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw status
echo "✅ 防火墙配置完成"
echo ""

# 4. 创建项目目录
echo "[4/10] 创建项目目录..."
echo "----------------------------------------"
mkdir -p "$PROJECT_DIR"
chown -R ubuntu:ubuntu "$PROJECT_DIR"
echo "✅ 项目目录创建完成"
echo ""

# 5. 克隆代码
echo "[5/10] 克隆代码..."
echo "----------------------------------------"
cd /home/ubuntu
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "项目已存在，更新代码..."
    cd "$PROJECT_DIR"
    git pull origin main
else
    echo "克隆新项目..."
    git clone "$GIT_REPO" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    git checkout main
fi
chown -R ubuntu:ubuntu "$PROJECT_DIR"
echo "✅ 代码克隆/更新完成"
echo ""

# 6. 安装后端依赖
echo "[6/10] 安装后端依赖..."
echo "----------------------------------------"
cd "$PROJECT_DIR/admin-backend"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    python3.12 -m venv venv
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

echo "✅ 后端依赖安装完成"
echo ""

# 7. 安装前端依赖
echo "[7/10] 安装前端依赖..."
echo "----------------------------------------"
cd "$PROJECT_DIR/saas-demo"
npm install
echo "✅ 前端依赖安装完成"
echo ""

# 8. 配置环境变量
echo "[8/10] 配置环境变量..."
echo "----------------------------------------"
# 后端环境变量
if [ ! -f "$PROJECT_DIR/admin-backend/.env" ]; then
    cat > "$PROJECT_DIR/admin-backend/.env" <<EOF
# 应用配置
APP_NAME=Smart TG Admin API
DATABASE_URL=sqlite:///./data/app.db
REDIS_URL=redis://localhost:6379/0

# JWT 配置（请修改为安全的密钥）
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# 管理員默認賬號（請修改密碼）
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123

# CORS 配置
CORS_ORIGINS=https://${DOMAIN},http://localhost:3000

# 群組 AI 配置
GROUP_AI_AI_PROVIDER=openai
GROUP_AI_AI_API_KEY=

# Telegram API 配置（可選）
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
EOF
    echo "✅ 后端环境变量已创建（请编辑 $PROJECT_DIR/admin-backend/.env 填入 API 密钥）"
else
    echo "✅ 后端环境变量已存在"
fi

# 前端环境变量
if [ ! -f "$PROJECT_DIR/saas-demo/.env.local" ]; then
    cat > "$PROJECT_DIR/saas-demo/.env.local" <<EOF
NEXT_PUBLIC_API_BASE_URL=https://${DOMAIN}/api/v1
NEXT_PUBLIC_GROUP_AI_API_BASE_URL=https://${DOMAIN}/api/v1/group-ai
NEXT_PUBLIC_WS_URL=wss://${DOMAIN}/api/v1/notifications/ws
NODE_ENV=production
EOF
    echo "✅ 前端环境变量已创建"
else
    echo "✅ 前端环境变量已存在"
fi

chown -R ubuntu:ubuntu "$PROJECT_DIR"
echo ""

# 9. 初始化数据库
echo "[9/10] 初始化数据库..."
echo "----------------------------------------"
cd "$PROJECT_DIR/admin-backend"
source venv/bin/activate

# 创建数据目录
mkdir -p "$PROJECT_DIR/admin-backend/data"
chown -R ubuntu:ubuntu "$PROJECT_DIR/admin-backend/data"

# 初始化数据库（如果不存在）
if [ ! -f "$PROJECT_DIR/admin-backend/data/app.db" ]; then
    python3 -c "
from app.db import Base, engine
from app.models import *
Base.metadata.create_all(bind=engine)
print('数据库初始化完成')
"
    echo "✅ 数据库初始化完成"
else
    echo "✅ 数据库已存在"
fi

deactivate
echo ""

# 10. 部署 Systemd 服务
echo "[10/10] 部署 Systemd 服务..."
echo "----------------------------------------"

# 后端服务
cat > /etc/systemd/system/$BACKEND_SERVICE.service <<EOF
[Unit]
Description=LuckyRed API Service (FastAPI)
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$PROJECT_DIR/admin-backend
Environment="PATH=$PROJECT_DIR/admin-backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONPATH=$PROJECT_DIR/admin-backend"
EnvironmentFile=$PROJECT_DIR/admin-backend/.env

ExecStart=$PROJECT_DIR/admin-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

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

# 前端服务（先构建）
echo "构建前端..."
cd "$PROJECT_DIR/saas-demo"
chown -R ubuntu:ubuntu .
sudo -u ubuntu npm run build

if [ ! -d ".next/standalone" ]; then
    echo "❌ 前端构建失败，standalone 目录不存在"
    exit 1
fi

cat > /etc/systemd/system/$FRONTEND_SERVICE.service <<EOF
[Unit]
Description=Liaotian Next.js Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$PROJECT_DIR/saas-demo/.next/standalone
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=NODE_OPTIONS=--max-old-space-size=1024
ExecStart=/usr/bin/node $PROJECT_DIR/saas-demo/.next/standalone/server.js
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

echo "✅ Systemd 服务已部署"
echo ""

# 11. 配置 Nginx
echo "[11/12] 配置 Nginx..."
echo "----------------------------------------"
cat > /etc/nginx/sites-available/default <<EOF
server {
    listen 443 ssl;
    server_name ${DOMAIN};
    
    # SSL 证书配置（将在下一步配置）
    # ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    # include /etc/letsencrypt/options-ssl-nginx.conf;
    # ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    # 临时自签名证书（仅用于初始配置）
    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;
    
    client_max_body_size 50M;
    
    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # 前端应用
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# HTTP 到 HTTPS 重定向
server {
    listen 80;
    server_name ${DOMAIN};
    return 301 https://\$host\$request_uri;
}
EOF

# 测试 Nginx 配置
if nginx -t; then
    systemctl restart nginx
    echo "✅ Nginx 配置完成"
else
    echo "❌ Nginx 配置错误"
    nginx -t
    exit 1
fi
echo ""

# 12. 启动服务
echo "[12/12] 启动服务..."
echo "----------------------------------------"
systemctl start "$BACKEND_SERVICE"
sleep 5

if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    echo "✅ 后端服务已启动"
else
    echo "❌ 后端服务启动失败"
    systemctl status "$BACKEND_SERVICE" --no-pager -l | head -20
fi

systemctl start "$FRONTEND_SERVICE"
sleep 5

if systemctl is-active --quiet "$FRONTEND_SERVICE"; then
    echo "✅ 前端服务已启动"
else
    echo "❌ 前端服务启动失败"
    systemctl status "$FRONTEND_SERVICE" --no-pager -l | head -20
fi
echo ""

# 最终验证
echo "=========================================="
echo "✅ 部署完成，开始验证..."
echo "=========================================="
echo ""

sleep 3

# 检查服务状态
echo "服务状态:"
systemctl status "$BACKEND_SERVICE" --no-pager -l | head -5
systemctl status "$FRONTEND_SERVICE" --no-pager -l | head -5
echo ""

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
echo ""

# 测试服务
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    echo "✅ 后端健康检查: HTTP 200"
else
    echo "⚠️  后端健康检查: HTTP $BACKEND_HEALTH"
fi

FRONTEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/login 2>/dev/null || echo "000")
if [ "$FRONTEND_TEST" = "200" ]; then
    echo "✅ 前端登录页面: HTTP 200"
else
    echo "⚠️  前端登录页面: HTTP $FRONTEND_TEST"
fi
echo ""

echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "下一步操作:"
echo "1. 配置 SSL 证书:"
echo "   sudo certbot --nginx -d ${DOMAIN}"
echo ""
echo "2. 编辑环境变量文件，填入 API 密钥:"
echo "   nano $PROJECT_DIR/admin-backend/.env"
echo ""
echo "3. 修改默认管理员密码（在 .env 文件中）"
echo ""
echo "4. 重启服务使配置生效:"
echo "   sudo systemctl restart $BACKEND_SERVICE"
echo "   sudo systemctl restart $FRONTEND_SERVICE"
echo ""

