#!/bin/bash
# ============================================================
# 自动配置 HTTPS/SSL 证书（使用 Let's Encrypt）
# ============================================================

echo "=========================================="
echo "🔒 自动配置 HTTPS/SSL 证书"
echo "=========================================="
echo ""

DOMAIN="aikz.usdt2026.cc"
EMAIL="admin@${DOMAIN}"  # Let's Encrypt 需要邮箱用于通知
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 检查是否以 root 或 sudo 运行
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "❌ 此脚本需要 sudo 权限"
    echo "请使用: sudo bash $0"
    exit 1
fi

# 1. 安装 Certbot
echo "[1/6] 安装 Certbot..."
echo "----------------------------------------"
if command -v certbot &> /dev/null; then
    echo "✅ Certbot 已安装"
    certbot --version
else
    echo "正在安装 Certbot..."
    sudo apt-get update -qq
    sudo apt-get install -y certbot python3-certbot-nginx
    if [ $? -eq 0 ]; then
        echo "✅ Certbot 安装成功"
    else
        echo "❌ Certbot 安装失败"
        exit 1
    fi
fi
echo ""

# 2. 检查 Nginx 配置
echo "[2/6] 检查 Nginx 配置..."
echo "----------------------------------------"
if [ ! -f "$NGINX_CONFIG" ]; then
    echo "⚠️  Nginx 配置文件不存在，从项目目录复制..."
    if [ -f "$PROJECT_DIR/deploy/nginx/aikz.conf" ]; then
        sudo cp "$PROJECT_DIR/deploy/nginx/aikz.conf" "$NGINX_CONFIG"
        echo "✅ 配置文件已复制"
    else
        echo "❌ 项目配置文件不存在"
        exit 1
    fi
fi

# 确保配置已启用
if [ ! -L "$NGINX_ENABLED" ] && [ ! -f "$NGINX_ENABLED" ]; then
    sudo ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"
    echo "✅ 符号链接已创建"
fi

# 测试 Nginx 配置
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
    sudo systemctl reload nginx
else
    echo "❌ Nginx 配置语法错误"
    sudo nginx -t
    exit 1
fi
echo ""

# 3. 检查防火墙
echo "[3/6] 检查防火墙..."
echo "----------------------------------------"
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(sudo ufw status | head -1)
    if echo "$UFW_STATUS" | grep -q "inactive"; then
        echo "✅ 防火墙未启用"
    else
        echo "检查端口 80 和 443 是否开放..."
        if sudo ufw status | grep -q "80/tcp"; then
            echo "✅ 端口 80 已开放"
        else
            echo "开放端口 80..."
            sudo ufw allow 80/tcp
        fi
        
        if sudo ufw status | grep -q "443/tcp"; then
            echo "✅ 端口 443 已开放"
        else
            echo "开放端口 443..."
            sudo ufw allow 443/tcp
        fi
    fi
else
    echo "⚠️  ufw 未安装，请确保防火墙允许端口 80 和 443"
fi
echo ""

# 4. 获取 SSL 证书
echo "[4/6] 获取 SSL 证书..."
echo "----------------------------------------"
if [ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
    echo "✅ SSL 证书已存在"
    echo "证书信息:"
    sudo openssl x509 -in /etc/letsencrypt/live/${DOMAIN}/fullchain.pem -noout -dates
else
    echo "正在获取 SSL 证书..."
    echo "域名: $DOMAIN"
    echo "邮箱: $EMAIL"
    echo ""
    echo "⚠️  注意：Let's Encrypt 需要："
    echo "   1. 域名 DNS 已正确解析到服务器 IP"
    echo "   2. 端口 80 可以从外网访问"
    echo "   3. 服务器可以访问外网"
    echo ""
    read -p "确认继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 1
    fi
    
    # 使用 Certbot 获取证书（使用 Nginx 插件自动配置）
    sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL" --redirect
    
    if [ $? -eq 0 ]; then
        echo "✅ SSL 证书获取成功"
    else
        echo "❌ SSL 证书获取失败"
        echo "可能的原因："
        echo "   1. 域名 DNS 未正确解析"
        echo "   2. 端口 80 被防火墙阻止"
        echo "   3. 服务器无法访问外网"
        echo ""
        echo "请检查："
        echo "   - DNS 解析: nslookup $DOMAIN"
        echo "   - 端口访问: curl -I http://$DOMAIN"
        exit 1
    fi
fi
echo ""

# 5. 更新 Nginx 配置（如果 Certbot 没有自动更新）
echo "[5/6] 更新 Nginx 配置..."
echo "----------------------------------------"
# 检查配置是否已包含 SSL
if grep -q "ssl_certificate" "$NGINX_CONFIG"; then
    echo "✅ Nginx 配置已包含 SSL 设置"
else
    echo "更新 Nginx 配置以支持 HTTPS..."
    
    # 备份配置
    sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # 检查是否有 HTTPS 配置文件
    if [ -f "$PROJECT_DIR/deploy/nginx/aikz-https.conf" ]; then
        echo "使用项目中的 HTTPS 配置..."
        sudo cp "$PROJECT_DIR/deploy/nginx/aikz-https.conf" "$NGINX_CONFIG"
    else
        echo "从 HTTP 配置生成 HTTPS 配置..."
        # 创建 HTTPS 配置
        sudo tee "$NGINX_CONFIG" > /dev/null <<EOF
# HTTP 到 HTTPS 重定向
server {
    listen 80;
    server_name ${DOMAIN};
    return 301 https://\$host\$request_uri;
}

# HTTPS 配置
server {
    listen 443 ssl http2;
    server_name ${DOMAIN};

    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 50M;

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

    # Next.js 静态资源 - 带下划线
    location /_next/static {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        expires 365d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Next.js 静态资源 - 兼容没有下划线的路径
    location /next/static {
        rewrite ^/next/static/(.*)\$ /_next/static/\$1 break;
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        expires 365d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # 前端应用
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
EOF
    fi
    
    # 测试配置
    if sudo nginx -t 2>&1 | grep -q "successful"; then
        echo "✅ Nginx 配置语法正确"
    else
        echo "❌ Nginx 配置语法错误"
        sudo nginx -t
        exit 1
    fi
fi
echo ""

# 6. 重新加载 Nginx 并设置自动续期
echo "[6/6] 重新加载 Nginx 并设置自动续期..."
echo "----------------------------------------"
sudo systemctl reload nginx
if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx 已重新加载"
else
    echo "❌ Nginx 重新加载失败"
    sudo systemctl status nginx --no-pager | head -10
    exit 1
fi

# 设置自动续期
if sudo systemctl is-enabled certbot.timer &> /dev/null; then
    echo "✅ Certbot 自动续期已启用"
else
    echo "启用 Certbot 自动续期..."
    sudo systemctl enable certbot.timer
    sudo systemctl start certbot.timer
    echo "✅ Certbot 自动续期已启用"
fi

# 测试续期（干运行）
echo "测试证书续期（干运行）..."
sudo certbot renew --dry-run
if [ $? -eq 0 ]; then
    echo "✅ 证书续期测试通过"
else
    echo "⚠️  证书续期测试失败，但证书仍然有效"
fi
echo ""

# 7. 验证 HTTPS
echo "=========================================="
echo "🧪 验证 HTTPS 配置"
echo "=========================================="
echo ""

echo "测试 HTTPS 连接:"
HTTPS_TEST=$(curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN}" 2>/dev/null || echo "000")
if [ "$HTTPS_TEST" = "200" ] || [ "$HTTPS_TEST" = "301" ] || [ "$HTTPS_TEST" = "302" ]; then
    echo "✅ HTTPS 连接成功 (HTTP $HTTPS_TEST)"
else
    echo "⚠️  HTTPS 连接返回: HTTP $HTTPS_TEST"
fi
echo ""

echo "测试 HTTP 到 HTTPS 重定向:"
HTTP_REDIRECT=$(curl -s -o /dev/null -w "%{http_code}" -L "http://${DOMAIN}" 2>/dev/null || echo "000")
if [ "$HTTP_REDIRECT" = "200" ]; then
    echo "✅ HTTP 到 HTTPS 重定向成功"
else
    echo "⚠️  HTTP 重定向返回: HTTP $HTTP_REDIRECT"
fi
echo ""

echo "证书信息:"
sudo openssl x509 -in /etc/letsencrypt/live/${DOMAIN}/fullchain.pem -noout -subject -dates 2>/dev/null || echo "无法读取证书信息"
echo ""

echo "=========================================="
echo "✅ HTTPS 配置完成！"
echo "=========================================="
echo ""
echo "📋 配置摘要:"
echo "   域名: $DOMAIN"
echo "   SSL 证书: /etc/letsencrypt/live/${DOMAIN}/"
echo "   Nginx 配置: $NGINX_CONFIG"
echo "   自动续期: 已启用"
echo ""
echo "🌐 访问地址:"
echo "   HTTPS: https://${DOMAIN}"
echo "   HTTP: http://${DOMAIN} (自动重定向到 HTTPS)"
echo ""
echo "📝 证书管理命令:"
echo "   查看证书: sudo certbot certificates"
echo "   手动续期: sudo certbot renew"
echo "   删除证书: sudo certbot delete --cert-name ${DOMAIN}"
echo ""

