#!/bin/bash
# ============================================================
# 完整修复 Nginx 路由配置（Certbot 后）
# ============================================================

set -e

echo "=========================================="
echo "🔧 完整修复 Nginx 路由配置"
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

# 1. 检查服务状态
echo "[1/6] 检查服务状态..."
echo "----------------------------------------"
# 检查前端服务
if systemctl is-active --quiet liaotian-frontend; then
    echo "✅ 前端服务运行中"
    FRONTEND_RUNNING=true
else
    echo "❌ 前端服务未运行"
    FRONTEND_RUNNING=false
fi

# 检查后端服务
if systemctl is-active --quiet luckyred-api; then
    echo "✅ 后端服务运行中"
    BACKEND_RUNNING=true
else
    echo "❌ 后端服务未运行"
    BACKEND_RUNNING=false
fi

# 检查端口
PORT_3000=$(lsof -ti:3000 2>/dev/null || true)
PORT_8000=$(lsof -ti:8000 2>/dev/null || true)

if [ -n "$PORT_3000" ]; then
    echo "✅ 端口 3000 正在监听"
else
    echo "❌ 端口 3000 未监听"
fi

if [ -n "$PORT_8000" ]; then
    echo "✅ 端口 8000 正在监听"
else
    echo "❌ 端口 8000 未监听"
fi
echo ""

# 2. 备份当前配置
echo "[2/6] 备份当前配置..."
echo "----------------------------------------"
mkdir -p "$BACKUP_DIR"
cp "$NGINX_CONFIG" "$BACKUP_DIR/default.backup.$TIMESTAMP"
echo "✅ 配置已备份到: $BACKUP_DIR/default.backup.$TIMESTAMP"
echo ""

# 3. 检查 SSL 证书
echo "[3/6] 检查 SSL 证书..."
echo "----------------------------------------"
SSL_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
SSL_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"

if [ ! -f "$SSL_CERT" ] || [ ! -f "$SSL_KEY" ]; then
    echo "❌ SSL 证书文件不存在"
    echo "   请先运行: sudo certbot --nginx -d $DOMAIN"
    exit 1
fi

echo "✅ SSL 证书存在"
echo ""

# 4. 生成正确的 Nginx 配置
echo "[4/6] 生成正确的 Nginx 配置..."
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

echo "✅ Nginx 配置已生成"
echo ""

# 5. 测试配置
echo "[5/6] 测试 Nginx 配置..."
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

# 6. 重新加载 Nginx
echo "[6/6] 重新加载 Nginx..."
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

# 测试本地服务
echo "测试本地服务..."
LOCAL_FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/login 2>/dev/null || echo "000")
if [ "$LOCAL_FRONTEND" = "200" ]; then
    echo "✅ 本地前端服务: HTTP 200"
else
    echo "❌ 本地前端服务: HTTP $LOCAL_FRONTEND"
fi

LOCAL_BACKEND=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$LOCAL_BACKEND" = "200" ]; then
    echo "✅ 本地后端服务: HTTP 200"
else
    echo "❌ 本地后端服务: HTTP $LOCAL_BACKEND"
fi
echo ""

# 测试 HTTPS 访问
echo "测试 HTTPS 访问..."
HTTPS_LOGIN=$(curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/login 2>/dev/null || echo "000")
if [ "$HTTPS_LOGIN" = "200" ]; then
    echo "✅ HTTPS /login: HTTP 200"
elif [ "$HTTPS_LOGIN" = "404" ]; then
    echo "❌ HTTPS /login: HTTP 404"
    echo ""
    echo "可能原因:"
    if [ "$LOCAL_FRONTEND" != "200" ]; then
        echo "   1. 前端服务未正常运行（本地测试也失败）"
        echo "   2. 检查: sudo systemctl status liaotian-frontend"
    else
        echo "   1. Nginx 配置可能仍有问题"
        echo "   2. 检查: sudo nginx -T | grep -A 10 'location /'"
    fi
else
    echo "⚠️  HTTPS /login: HTTP $HTTPS_LOGIN"
fi

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
echo "如果仍有 404 错误，请检查:"
echo "1. 前端服务: sudo systemctl status liaotian-frontend"
echo "2. Nginx 配置: sudo nginx -T | grep -A 10 'location /'"
echo "3. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo ""

