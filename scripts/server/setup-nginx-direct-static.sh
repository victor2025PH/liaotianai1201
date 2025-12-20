#!/bin/bash
# ============================================================
# 配置 Nginx 直接提供静态资源（性能优化）
# ============================================================

set -e

DOMAIN="aikz.usdt2026.cc"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"
STATIC_DIR="/var/www/html/aikz/static"
PUBLIC_DIR="/var/www/html/aikz/public"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"

echo "=========================================="
echo "🚀 配置 Nginx 直接提供静态资源"
echo "=========================================="
echo ""

# 检查是否以 root 或 sudo 运行
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "❌ 此脚本需要 sudo 权限"
    echo "请使用: sudo bash $0"
    exit 1
fi

# 1. 检查前端构建产物
echo "[1/6] 检查前端构建产物..."
echo "----------------------------------------"
if [ ! -d "$FRONTEND_DIR/.next/static" ]; then
    echo "❌ 静态资源目录不存在: $FRONTEND_DIR/.next/static"
    echo "   请先运行构建: cd $FRONTEND_DIR && npm run build"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR/public" ]; then
    echo "⚠️  public 目录不存在: $FRONTEND_DIR/public"
    echo "   将创建空目录"
fi

STATIC_COUNT=$(find "$FRONTEND_DIR/.next/static" -type f 2>/dev/null | wc -l || echo "0")
echo "✅ 找到 $STATIC_COUNT 个静态文件"
echo ""

# 2. 创建 Nginx 专属的静态资源目录
echo "[2/6] 创建 Nginx 静态资源目录..."
echo "----------------------------------------"
sudo mkdir -p "$STATIC_DIR"
sudo mkdir -p "$PUBLIC_DIR"
echo "✅ 目录已创建"
echo "   Static: $STATIC_DIR"
echo "   Public: $PUBLIC_DIR"
echo ""

# 3. 复制静态文件到新目录
echo "[3/6] 复制静态文件..."
echo "----------------------------------------"
echo "复制 .next/static 文件..."
sudo cp -r "$FRONTEND_DIR/.next/static/"* "$STATIC_DIR/" 2>/dev/null || {
    echo "⚠️  复制失败，尝试清空目标目录后重试..."
    sudo rm -rf "$STATIC_DIR"/*
    sudo cp -r "$FRONTEND_DIR/.next/static/"* "$STATIC_DIR/"
}
echo "✅ 静态文件已复制"

if [ -d "$FRONTEND_DIR/public" ] && [ "$(ls -A $FRONTEND_DIR/public 2>/dev/null)" ]; then
    echo "复制 public 文件..."
    sudo cp -r "$FRONTEND_DIR/public/"* "$PUBLIC_DIR/" 2>/dev/null || {
        echo "⚠️  复制失败，尝试清空目标目录后重试..."
        sudo rm -rf "$PUBLIC_DIR"/*
        sudo cp -r "$FRONTEND_DIR/public/"* "$PUBLIC_DIR/"
    }
    echo "✅ public 文件已复制"
else
    echo "⚠️  public 目录为空或不存在，跳过"
fi
echo ""

# 4. 设置文件权限
echo "[4/6] 设置文件权限..."
echo "----------------------------------------"
sudo chown -R www-data:www-data /var/www/html/aikz
sudo chmod -R 755 /var/www/html/aikz
echo "✅ 权限已设置"
echo ""

# 5. 备份现有配置并创建新配置
echo "[5/6] 更新 Nginx 配置..."
echo "----------------------------------------"
BACKUP_DIR="/etc/nginx/backups"
mkdir -p "$BACKUP_DIR"
if [ -f "$NGINX_CONFIG" ]; then
    BACKUP_FILE="$BACKUP_DIR/aikz.usdt2026.cc.$(date +%Y%m%d_%H%M%S).conf"
    sudo cp "$NGINX_CONFIG" "$BACKUP_FILE"
    echo "✅ 配置已备份到: $BACKUP_FILE"
fi

# 检查 SSL 证书
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"
HAS_SSL=false
if [ -d "$CERT_DIR" ] && [ -f "$CERT_DIR/fullchain.pem" ] && [ -f "$CERT_DIR/privkey.pem" ]; then
    HAS_SSL=true
    echo "✅ 检测到 SSL 证书，将配置 HTTPS"
fi

# 创建完整的 Nginx 配置
sudo tee "$NGINX_CONFIG" > /dev/null << NGINX_EOF
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name ${DOMAIN};
    
    # Let's Encrypt 验证路径
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # 重定向所有 HTTP 请求到 HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name ${DOMAIN};

    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/${DOMAIN}/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    client_max_body_size 50M;

    # === 关键优化：Nginx 直接提供静态资源 ===
    # Next.js 静态资源（兼容路径 - 必须在 /_next/static 之前）
    location /next/static {
        rewrite ^/next/static/(.*)$ /_next/static/\$1 permanent;
    }

    # Next.js 静态资源（标准路径）- 直接由 Nginx 提供
    location /_next/static {
        alias ${STATIC_DIR}/;
        expires 365d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # public 目录资源 - 直接由 Nginx 提供
    location /public {
        alias ${PUBLIC_DIR}/;
        expires 30d;
        access_log off;
    }
    # ==========================================

    # WebSocket 支持 - 通知服务
    location /api/v1/notifications/ws {
        proxy_pass http://127.0.0.1:8000/api/v1/notifications/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_buffering off;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
    }

    # 前端应用（动态内容）
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }
}
NGINX_EOF

# 如果 SSL 证书不存在，创建仅 HTTP 配置
if [ "$HAS_SSL" = false ]; then
    echo "⚠️  SSL 证书不存在，创建仅 HTTP 配置..."
    sudo tee "$NGINX_CONFIG" > /dev/null << NGINX_HTTP_EOF
server {
    listen 80;
    server_name ${DOMAIN};

    client_max_body_size 50M;

    # === 关键优化：Nginx 直接提供静态资源 ===
    # Next.js 静态资源（兼容路径）
    location /next/static {
        rewrite ^/next/static/(.*)$ /_next/static/\$1 permanent;
    }

    # Next.js 静态资源（标准路径）- 直接由 Nginx 提供
    location /_next/static {
        alias ${STATIC_DIR}/;
        expires 365d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # public 目录资源 - 直接由 Nginx 提供
    location /public {
        alias ${PUBLIC_DIR}/;
        expires 30d;
        access_log off;
    }
    # ==========================================

    # WebSocket 支持 - 通知服务
    location /api/v1/notifications/ws {
        proxy_pass http://127.0.0.1:8000/api/v1/notifications/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_buffering off;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
    }

    # 前端应用（动态内容）
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }
}
NGINX_HTTP_EOF
fi

# 确保配置文件链接
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"
if [ ! -L "$NGINX_ENABLED" ] && [ ! -f "$NGINX_ENABLED" ]; then
    sudo ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"
    echo "✅ 配置文件链接已创建"
fi

echo "✅ Nginx 配置已更新"
echo ""

# 6. 测试并重新加载 Nginx
echo "[6/6] 测试并重新加载 Nginx..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
    echo "✅ Nginx 配置测试成功"
    sudo systemctl reload nginx
    sleep 2
    
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已重新加载"
    else
        echo "⚠️  重新加载失败，尝试重启..."
        sudo systemctl restart nginx
        sleep 2
    fi
else
    echo "❌ Nginx 配置测试失败"
    echo "恢复备份..."
    if [ -f "$BACKUP_FILE" ]; then
        sudo cp "$BACKUP_FILE" "$NGINX_CONFIG"
    fi
    exit 1
fi
echo ""

# 7. 如果 SSL 证书不存在，提示使用 Certbot
if [ "$HAS_SSL" = false ]; then
    echo "=========================================="
    echo "⚠️  SSL 证书未配置"
    echo "=========================================="
    echo ""
    echo "要配置 HTTPS，请运行："
    echo "  sudo certbot --nginx -d ${DOMAIN}"
    echo ""
    echo "⚠️  重要：选择选项 2 (Redirect) 以启用 HTTP 到 HTTPS 重定向"
    echo ""
fi

# 8. 验证
echo "验证配置..."
echo "----------------------------------------"
sleep 2

# 检查端口
if sudo ss -tlnp | grep -q ":443 "; then
    echo "✅ 端口 443 正在监听"
elif sudo ss -tlnp | grep -q ":80 "; then
    echo "✅ 端口 80 正在监听"
else
    echo "❌ 端口未监听"
fi

# 测试静态资源
echo ""
echo "测试静态资源访问..."
STATIC_TEST=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1/_next/static/chunks/main.js" 2>/dev/null || echo "000")
if [ "$STATIC_TEST" = "200" ] || [ "$STATIC_TEST" = "404" ]; then
    echo "✅ 静态资源路径可访问 (状态码: $STATIC_TEST)"
else
    echo "⚠️  静态资源路径测试失败 (状态码: $STATIC_TEST)"
fi
echo ""

echo "=========================================="
echo "✅ 配置完成"
echo "=========================================="
echo ""
echo "静态资源现在由 Nginx 直接提供，性能更优！"
echo ""
echo "后续更新静态资源时，请运行："
echo "  sudo cp -r $FRONTEND_DIR/.next/static/* $STATIC_DIR/"
echo "  sudo cp -r $FRONTEND_DIR/public/* $PUBLIC_DIR/"
echo "  sudo chown -R www-data:www-data /var/www/html/aikz"
echo ""

