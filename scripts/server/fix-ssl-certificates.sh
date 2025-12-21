#!/bin/bash
# ============================================================
# 修复 SSL 证书问题
# ============================================================

set -e

echo "============================================================"
echo "🔧 修复 SSL 证书问题"
echo "============================================================"
echo ""

DOMAINS=(
    "tgmini.usdt2026.cc"
    "hongbao.usdt2026.cc"
    "aikz.usdt2026.cc"
)

# 检查 Certbot
if ! command -v certbot >/dev/null 2>&1; then
    echo "⚠️  Certbot 未安装，安装 Certbot..."
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
fi

echo "✅ Certbot: $(certbot --version 2>/dev/null || echo '已安装')"
echo ""

# 为每个域名获取证书
for DOMAIN in "${DOMAINS[@]}"; do
    echo "============================================================"
    echo "处理域名: $DOMAIN"
    echo "============================================================"
    
    SSL_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    SSL_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
    
    if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
        echo "✅ SSL 证书已存在"
        echo "证书路径: $SSL_CERT"
        echo "证书有效期:"
        sudo openssl x509 -in "$SSL_CERT" -noout -dates 2>/dev/null || true
    else
        echo "⚠️  SSL 证书不存在"
        echo "获取 SSL 证书..."
        
        # 先配置 HTTP Nginx（如果还没有）
        HTTP_CONFIG="/etc/nginx/sites-available/$DOMAIN"
        if [ ! -f "$HTTP_CONFIG" ]; then
            echo "创建临时 HTTP 配置..."
            sudo tee "$HTTP_CONFIG" > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 http://\$server_name\$request_uri;
    }
}
EOF
            sudo ln -sf "$HTTP_CONFIG" "/etc/nginx/sites-enabled/$DOMAIN"
            sudo nginx -t && sudo systemctl reload nginx
        fi
        
        # 使用 Certbot 获取证书
        echo "运行 Certbot..."
        sudo certbot certonly --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@$DOMAIN || {
            echo "⚠️  Certbot 失败，尝试 standalone 模式..."
            sudo certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos --email admin@$DOMAIN || {
                echo "❌ 无法获取 SSL 证书"
                echo "请手动运行: sudo certbot certonly --nginx -d $DOMAIN"
            }
        }
    fi
    
    echo ""
done

echo "============================================================"
echo "✅ SSL 证书检查完成"
echo "============================================================"
echo ""
echo "如果证书已获取，重新运行部署脚本:"
echo "  bash scripts/server/comprehensive-fix.sh"
echo ""
