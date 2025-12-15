#!/bin/bash
# ============================================================
# 修复静态资源 500 错误（路径映射问题）
# ============================================================

set -e

echo "=========================================="
echo "🔧 修复静态资源 500 错误"
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

# 1. 检查静态资源目录
echo "[1/5] 检查静态资源目录..."
echo "----------------------------------------"
STATIC_DIR="$FRONTEND_DIR/.next/static"
if [ -d "$STATIC_DIR" ]; then
    echo "✅ 静态资源目录存在: $STATIC_DIR"
    ls -la "$STATIC_DIR" | head -10
else
    echo "❌ 静态资源目录不存在，需要重新构建"
    echo "   运行: cd $FRONTEND_DIR && npm run build"
    exit 1
fi
echo ""

# 2. 备份当前配置
echo "[2/5] 备份当前配置..."
echo "----------------------------------------"
mkdir -p "$BACKUP_DIR"
cp "$NGINX_CONFIG" "$BACKUP_DIR/default.backup.$TIMESTAMP"
echo "✅ 配置已备份"
echo ""

# 3. 更新 Nginx 配置（添加路径重写和静态资源直接提供）
echo "[3/5] 更新 Nginx 配置..."
echo "----------------------------------------"
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
    
    # WebSocket 支持（必须在其他 location 之前）
    location /api/v1/notifications/ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
    
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
    
    # Next.js 静态资源 - 直接提供文件（支持两种路径格式）
    # 处理 /next/static/ 路径（重写到 /_next/static/）
    location ~ ^/next/static/(.*)$ {
        alias /home/ubuntu/telegram-ai-system/saas-demo/.next/static/$1;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
        # 如果文件不存在，返回 404 而不是 500
        try_files $uri =404;
    }
    
    # 处理 /_next/static/ 路径（标准路径）
    location /_next/static/ {
        alias /home/ubuntu/telegram-ai-system/saas-demo/.next/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
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

echo "✅ Nginx 配置已更新（包含静态资源路径映射）"
echo ""

# 4. 测试并重新加载 Nginx
echo "[4/5] 测试并重新加载 Nginx..."
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

# 5. 验证
echo "[5/5] 验证修复..."
echo "----------------------------------------"
sleep 3

# 测试静态资源（两种路径）
echo "测试静态资源访问..."
STATIC_TEST1=$(curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/next/static/chunks/main.js 2>/dev/null || echo "000")
if [ "$STATIC_TEST1" = "200" ]; then
    echo "✅ /next/static/: HTTP 200"
elif [ "$STATIC_TEST1" = "404" ]; then
    echo "⚠️  /next/static/: HTTP 404（文件可能不存在，但路径已正确）"
else
    echo "❌ /next/static/: HTTP $STATIC_TEST1"
fi

STATIC_TEST2=$(curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/_next/static/chunks/main.js 2>/dev/null || echo "000")
if [ "$STATIC_TEST2" = "200" ]; then
    echo "✅ /_next/static/: HTTP 200"
elif [ "$STATIC_TEST2" = "404" ]; then
    echo "⚠️  /_next/static/: HTTP 404（文件可能不存在，但路径已正确）"
else
    echo "❌ /_next/static/: HTTP $STATIC_TEST2"
fi

# 测试页面
HTTPS_LOGIN=$(curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/login 2>/dev/null || echo "000")
if [ "$HTTPS_LOGIN" = "200" ]; then
    echo "✅ HTTPS /login: HTTP 200"
else
    echo "⚠️  HTTPS /login: HTTP $HTTPS_LOGIN"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果静态资源仍然 500 错误，请检查:"
echo "1. 静态资源目录权限:"
echo "   sudo chown -R ubuntu:ubuntu $STATIC_DIR"
echo "   sudo chmod -R 755 $STATIC_DIR"
echo ""
echo "2. 检查文件是否存在:"
echo "   ls -la $STATIC_DIR/chunks/ | head -5"
echo ""
echo "3. 检查 Nginx 错误日志:"
echo "   sudo tail -50 /var/log/nginx/error.log"
echo ""

