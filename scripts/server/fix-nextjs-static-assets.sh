#!/bin/bash
# ============================================================
# 修复 Next.js standalone 模式的静态资源路径
# ============================================================

set -e

echo "=========================================="
echo "🔧 修复 Next.js 静态资源路径"
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

# 1. 检查 standalone 构建
echo "[1/5] 检查 standalone 构建..."
echo "----------------------------------------"
if [ ! -d "$FRONTEND_DIR/.next/standalone" ]; then
    echo "❌ standalone 目录不存在"
    exit 1
fi

# 检查静态资源目录
if [ -d "$FRONTEND_DIR/.next/static" ]; then
    echo "✅ 静态资源目录存在: $FRONTEND_DIR/.next/static"
    STATIC_DIR="$FRONTEND_DIR/.next/static"
elif [ -d "$FRONTEND_DIR/.next/standalone/.next/static" ]; then
    echo "✅ 静态资源目录存在: $FRONTEND_DIR/.next/standalone/.next/static"
    STATIC_DIR="$FRONTEND_DIR/.next/standalone/.next/static"
else
    echo "⚠️  静态资源目录不存在，可能需要重新构建"
    STATIC_DIR=""
fi
echo ""

# 2. 备份当前配置
echo "[2/5] 备份当前配置..."
echo "----------------------------------------"
mkdir -p "$BACKUP_DIR"
cp "$NGINX_CONFIG" "$BACKUP_DIR/default.backup.$TIMESTAMP"
echo "✅ 配置已备份"
echo ""

# 3. 生成正确的 Nginx 配置（包含静态资源路径）
echo "[3/5] 生成正确的 Nginx 配置..."
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
    
    # Next.js 静态资源 - 直接提供文件（优先级最高）
    location /_next/static/ {
        alias /home/ubuntu/telegram-ai-system/saas-demo/.next/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Next.js 静态资源（备用路径）
    location /next/static/ {
        alias /home/ubuntu/telegram-ai-system/saas-demo/.next/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # 后端 API - 转发到后端
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
    
    # 前端应用 - 转发到前端（包括 /login 页面）
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

echo "✅ Nginx 配置已生成（包含静态资源路径）"
echo ""

# 4. 测试配置
echo "[4/5] 测试 Nginx 配置..."
echo "----------------------------------------"
if nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
else
    echo "❌ Nginx 配置语法错误"
    nginx -t
    echo ""
    echo "恢复备份..."
    cp "$BACKUP_DIR/default.backup.$TIMESTAMP" "$NGINX_CONFIG"
    exit 1
fi
echo ""

# 5. 重新加载 Nginx
echo "[5/5] 重新加载 Nginx..."
echo "----------------------------------------"
systemctl reload nginx
sleep 2

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 已重新加载"
else
    echo "❌ Nginx 重新加载失败"
    systemctl status nginx --no-pager -l | head -20
    exit 1
fi
echo ""

# 验证
echo "=========================================="
echo "✅ 修复完成，开始验证..."
echo "=========================================="
echo ""

sleep 3

# 测试静态资源
echo "测试静态资源访问..."
STATIC_TEST=$(curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/_next/static/chunks/main.js 2>/dev/null || echo "000")
if [ "$STATIC_TEST" = "200" ] || [ "$STATIC_TEST" = "404" ]; then
    echo "✅ 静态资源路径 /_next/static/: HTTP $STATIC_TEST"
else
    echo "⚠️  静态资源路径 /_next/static/: HTTP $STATIC_TEST"
fi

# 测试页面
HTTPS_LOGIN=$(curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/login 2>/dev/null || echo "000")
if [ "$HTTPS_LOGIN" = "200" ]; then
    echo "✅ HTTPS /login: HTTP 200"
else
    echo "⚠️  HTTPS /login: HTTP $HTTPS_LOGIN"
fi

# 测试 API
HTTPS_API=$(curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/api/v1/health 2>/dev/null || echo "000")
if [ "$HTTPS_API" = "200" ] || [ "$HTTPS_API" = "404" ] || [ "$HTTPS_API" = "401" ]; then
    echo "✅ HTTPS /api: HTTP $HTTPS_API"
else
    echo "⚠️  HTTPS /api: HTTP $HTTPS_API"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果静态资源仍然 404，请检查:"
echo "1. 静态资源目录是否存在:"
echo "   ls -la $FRONTEND_DIR/.next/static/"
echo ""
echo "2. 如果目录不存在，重新构建前端:"
echo "   cd $FRONTEND_DIR"
echo "   npm run build"
echo ""
echo "3. 检查 Nginx 配置:"
echo "   sudo nginx -T | grep -A 5 '_next/static'"
echo ""

