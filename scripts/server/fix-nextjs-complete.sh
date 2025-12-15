#!/bin/bash
# ============================================================
# 完整修复 Next.js 前端服务（包含 standalone 构建和静态资源）
# ============================================================

set -e

echo "=========================================="
echo "🔧 完整修复 Next.js 前端服务"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-enabled/default"
BACKUP_DIR="/var/backups/nginx_configs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"
FRONTEND_SERVICE="liaotian-frontend"

# 1. 停止前端服务
echo "[1/7] 停止前端服务..."
echo "----------------------------------------"
systemctl stop "$FRONTEND_SERVICE" 2>/dev/null || true
sleep 2
echo "✅ 前端服务已停止"
echo ""

# 2. 检查并重新构建前端
echo "[2/7] 检查并重新构建前端..."
echo "----------------------------------------"
cd "$FRONTEND_DIR"

# 检查 standalone 目录
if [ ! -d ".next/standalone" ] || [ ! -f ".next/standalone/server.js" ]; then
    echo "⚠️  standalone 构建不完整，重新构建..."
    npm run build
    
    # 验证构建
    if [ ! -f ".next/standalone/server.js" ]; then
        echo "❌ standalone 构建失败，server.js 不存在"
        exit 1
    fi
    echo "✅ standalone 构建完成"
else
    echo "✅ standalone 构建已存在"
fi

# 检查静态资源目录
if [ ! -d ".next/static" ]; then
    echo "⚠️  静态资源目录不存在，重新构建..."
    npm run build
    echo "✅ 静态资源目录已创建"
else
    echo "✅ 静态资源目录存在"
fi
echo ""

# 3. 检查并修复文件权限
echo "[3/7] 检查并修复文件权限..."
echo "----------------------------------------"
chown -R ubuntu:ubuntu "$FRONTEND_DIR/.next" 2>/dev/null || true
chmod -R 755 "$FRONTEND_DIR/.next" 2>/dev/null || true
echo "✅ 文件权限已修复"
echo ""

# 4. 检查并修复 systemd 服务配置
echo "[4/7] 检查并修复 systemd 服务配置..."
echo "----------------------------------------"
SERVICE_FILE="/etc/systemd/system/${FRONTEND_SERVICE}.service"

# 检查服务文件是否存在
if [ ! -f "$SERVICE_FILE" ]; then
    echo "⚠️  服务文件不存在，创建..."
    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Liaotian Next.js Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$FRONTEND_DIR
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=HOSTNAME=0.0.0.0
ExecStart=/usr/bin/node $FRONTEND_DIR/.next/standalone/server.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    echo "✅ 服务文件已创建"
else
    # 检查 ExecStart 路径是否正确
    if ! grep -q "$FRONTEND_DIR/.next/standalone/server.js" "$SERVICE_FILE"; then
        echo "⚠️  服务配置路径不正确，更新..."
        sed -i "s|ExecStart=.*|ExecStart=/usr/bin/node $FRONTEND_DIR/.next/standalone/server.js|" "$SERVICE_FILE"
        systemctl daemon-reload
        echo "✅ 服务配置已更新"
    else
        echo "✅ 服务配置正确"
    fi
fi
echo ""

# 5. 备份并更新 Nginx 配置
echo "[5/7] 备份并更新 Nginx 配置..."
echo "----------------------------------------"
mkdir -p "$BACKUP_DIR"
cp "$NGINX_CONFIG" "$BACKUP_DIR/default.backup.$TIMESTAMP"

# 生成正确的 Nginx 配置
# 注意：Next.js standalone 模式下，静态资源应该由 Next.js 服务器提供
# 所以不需要 Nginx 直接提供文件，只需要代理到前端服务器
cat > "$NGINX_CONFIG" <<'NGINX_EOF'
server {
    listen 443 ssl;
    server_name aikz.usdt2026.cc;
    
    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    client_max_body_size 50M;
    
    # 后端 API - 转发到后端（必须在根路径之前）
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # 前端应用 - 转发到前端（包括所有路径，Next.js 会处理静态资源）
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# HTTP 到 HTTPS 重定向
server {
    listen 80;
    server_name aikz.usdt2026.cc;
    return 301 https://$host$request_uri;
}
NGINX_EOF

echo "✅ Nginx 配置已更新"
echo ""

# 6. 测试并重新加载 Nginx
echo "[6/7] 测试并重新加载 Nginx..."
echo "----------------------------------------"
if nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
    systemctl reload nginx
    echo "✅ Nginx 已重新加载"
else
    echo "❌ Nginx 配置语法错误"
    nginx -t
    echo ""
    echo "恢复备份..."
    cp "$BACKUP_DIR/default.backup.$TIMESTAMP" "$NGINX_CONFIG"
    exit 1
fi
echo ""

# 7. 启动前端服务
echo "[7/7] 启动前端服务..."
echo "----------------------------------------"
systemctl start "$FRONTEND_SERVICE"
sleep 5

if systemctl is-active --quiet "$FRONTEND_SERVICE"; then
    echo "✅ 前端服务已启动"
else
    echo "❌ 前端服务启动失败"
    systemctl status "$FRONTEND_SERVICE" --no-pager -l | head -30
    exit 1
fi
echo ""

# 验证
echo "=========================================="
echo "✅ 修复完成，开始验证..."
echo "=========================================="
echo ""

sleep 5

# 检查端口
PORT_3000=$(lsof -ti:3000 2>/dev/null || true)
if [ -n "$PORT_3000" ]; then
    echo "✅ 端口 3000 正在监听 (PID: $PORT_3000)"
else
    echo "❌ 端口 3000 未监听"
fi

# 测试本地前端
LOCAL_FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/login 2>/dev/null || echo "000")
if [ "$LOCAL_FRONTEND" = "200" ]; then
    echo "✅ 本地前端服务: HTTP 200"
else
    echo "❌ 本地前端服务: HTTP $LOCAL_FRONTEND"
fi

# 测试本地静态资源（Next.js 应该提供）
STATIC_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/_next/static/chunks/main.js 2>/dev/null || echo "000")
if [ "$STATIC_TEST" = "200" ]; then
    echo "✅ 本地静态资源: HTTP 200"
elif [ "$STATIC_TEST" = "404" ]; then
    echo "⚠️  本地静态资源: HTTP 404（可能需要检查 Next.js 配置）"
else
    echo "⚠️  本地静态资源: HTTP $STATIC_TEST"
fi

# 测试 HTTPS 访问
HTTPS_LOGIN=$(curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/login 2>/dev/null || echo "000")
if [ "$HTTPS_LOGIN" = "200" ]; then
    echo "✅ HTTPS /login: HTTP 200"
else
    echo "⚠️  HTTPS /login: HTTP $HTTPS_LOGIN"
fi

# 测试 HTTPS 静态资源
HTTPS_STATIC=$(curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/_next/static/chunks/main.js 2>/dev/null || echo "000")
if [ "$HTTPS_STATIC" = "200" ]; then
    echo "✅ HTTPS 静态资源: HTTP 200"
else
    echo "⚠️  HTTPS 静态资源: HTTP $HTTPS_STATIC"
fi

# 测试 API
HTTPS_API=$(curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/api/v1/health 2>/dev/null || echo "000")
if [ "$HTTPS_API" = "200" ] || [ "$HTTPS_API" = "404" ] || [ "$HTTPS_API" = "401" ]; then
    echo "✅ HTTPS /api: HTTP $HTTPS_API"
else
    echo "⚠️  HTTPS /api: HTTP $HTTPS_API"
    echo "   检查后端服务: sudo systemctl status luckyred-api"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果仍有问题，请检查:"
echo "1. 前端服务日志: sudo journalctl -u $FRONTEND_SERVICE -n 50 --no-pager"
echo "2. 前端服务状态: sudo systemctl status $FRONTEND_SERVICE"
echo "3. 端口监听: sudo ss -tlnp | grep 3000"
echo "4. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo ""

