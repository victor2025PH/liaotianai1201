#!/bin/bash
# 直接在服务器上创建完整的 Nginx 和 Systemd 配置
# 如果 Git 拉取失败，可以直接在服务器上执行此脚本内容

set -e

echo "========================================="
echo "直接在服务器上创建配置"
echo "========================================="
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then 
    echo "错误: 请使用 sudo 运行此脚本"
    echo "Usage: sudo bash <(curl -s https://raw.githubusercontent.com/victor2025PH/liaotianai1201/main/scripts/直接在服务器上创建配置脚本.sh)"
    exit 1
fi

# 项目路径
PROJECT_DIR="/home/ubuntu/liaotian"
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
SYSTEMD_DIR="/etc/systemd/system"

echo "=== 步骤 1: 安装 Nginx ==="
if ! command -v nginx &> /dev/null; then
    apt-get update
    apt-get install -y nginx
fi

echo "=== 步骤 2: 配置 Nginx ==="
cat > "$NGINX_CONF_DIR/liaotian" << 'EOFNGINX'
upstream frontend {
    server localhost:3000;
    keepalive 64;
}

upstream backend {
    server localhost:8000;
    keepalive 64;
}

server {
    listen 80;
    server_name 165.154.233.55;
    client_max_body_size 50M;

    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }

    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }

    location /docs {
        proxy_pass http://backend/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    access_log /var/log/nginx/liaotian-access.log;
    error_log /var/log/nginx/liaotian-error.log;
}
EOFNGINX

ln -sf "$NGINX_CONF_DIR/liaotian" "$NGINX_ENABLED_DIR/liaotian"
nginx -t && systemctl reload nginx
echo "✅ Nginx 配置完成"

echo "=== 步骤 3: 配置 Systemd 服务 ==="
cat > "$SYSTEMD_DIR/liaotian-frontend.service" << 'EOFFRONTEND'
[Unit]
Description=Liaotian Frontend Service (Next.js)
After=network.target liaotian-backend.service
Wants=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/liaotian/saas-demo
Environment="PATH=/usr/bin:/bin"
Environment="NODE_ENV=production"
Environment="PORT=3000"
ExecStart=/bin/bash -c 'if [ -d "/home/ubuntu/liaotian/saas-demo/.next/standalone" ]; then cd /home/ubuntu/liaotian/saas-demo/.next/standalone && PORT=3000 /usr/bin/node server.js; else cd /home/ubuntu/liaotian/saas-demo && /usr/bin/npm start; fi'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOFFRONTEND

cat > "$SYSTEMD_DIR/liaotian-backend.service" << 'EOFBACKEND'
[Unit]
Description=Liaotian Backend API Service (FastAPI)
After=network.target
Wants=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/liaotian/admin-backend
Environment="PATH=/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 120
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOFBACKEND

systemctl daemon-reload
echo "✅ Systemd 服务文件已创建"

echo "=== 步骤 4: 启用并启动服务 ==="
systemctl stop liaotian-frontend 2>/dev/null || true
systemctl stop liaotian-backend 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
sleep 3

systemctl enable liaotian-backend
systemctl enable liaotian-frontend
systemctl start liaotian-backend
sleep 5
systemctl start liaotian-frontend
sleep 5

echo "=== 步骤 5: 验证 ==="
systemctl status liaotian-backend --no-pager -l | head -10
systemctl status liaotian-frontend --no-pager -l | head -10

echo ""
echo "✅ 配置完成！"
echo "访问: http://165.154.233.55/"
