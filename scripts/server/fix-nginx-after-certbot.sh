#!/bin/bash
# ============================================================
# 修复 Certbot 配置 SSL 后的 Nginx 配置
# ============================================================

set -e

echo "=========================================="
echo "🔧 修复 Certbot 配置后的 Nginx 路由"
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

# 1. 备份当前配置
echo "[1/5] 备份当前配置..."
echo "----------------------------------------"
mkdir -p "$BACKUP_DIR"
cp "$NGINX_CONFIG" "$BACKUP_DIR/default.backup.$TIMESTAMP"
echo "✅ 配置已备份到: $BACKUP_DIR/default.backup.$TIMESTAMP"
echo ""

# 2. 检查 SSL 证书路径
echo "[2/5] 检查 SSL 证书..."
echo "----------------------------------------"
SSL_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
SSL_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"

if [ ! -f "$SSL_CERT" ] || [ ! -f "$SSL_KEY" ]; then
    echo "❌ SSL 证书文件不存在"
    echo "   请先运行: sudo certbot --nginx -d $DOMAIN"
    exit 1
fi

echo "✅ SSL 证书存在"
echo "   证书: $SSL_CERT"
echo "   密钥: $SSL_KEY"
echo ""

# 3. 生成正确的 Nginx 配置
echo "[3/5] 生成正确的 Nginx 配置..."
echo "----------------------------------------"
cat > "$NGINX_CONFIG" <<EOF
server {
    listen 443 ssl;
    server_name ${DOMAIN};
    
    # SSL 证书配置
    ssl_certificate ${SSL_CERT};
    ssl_certificate_key ${SSL_KEY};
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    client_max_body_size 50M;
    
    # 后端 API - 转发到后端（优先级最高）
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
    
    # 前端应用 - 转发到前端（包括 /login 页面）
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

echo "✅ Nginx 配置已生成"
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

sleep 2

# 测试 HTTPS 访问
HTTPS_LOGIN=$(curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/login 2>/dev/null || echo "000")
if [ "$HTTPS_LOGIN" = "200" ]; then
    echo "✅ HTTPS /login: HTTP 200"
elif [ "$HTTPS_LOGIN" = "404" ]; then
    echo "❌ HTTPS /login: HTTP 404"
    echo ""
    echo "可能原因:"
    echo "1. 前端服务未运行"
    echo "2. 端口 3000 未监听"
    echo ""
    echo "请检查:"
    echo "  sudo systemctl status liaotian-frontend"
    echo "  sudo ss -tlnp | grep 3000"
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
echo "如果仍有 404 错误，请运行诊断脚本:"
echo "  sudo bash scripts/server/diagnose-404-after-ssl.sh"
echo ""

