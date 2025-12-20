#!/bin/bash
# ============================================================
# 确保 HTTPS 配置持久化 - 防止配置丢失
# ============================================================

set -e

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
CONFIG_TEMPLATE="$PROJECT_DIR/deploy/nginx/aikz-https.conf"

echo "=========================================="
echo "🔒 确保 HTTPS 配置持久化"
echo "=========================================="
echo ""

# 检查是否以 root 或 sudo 运行
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "❌ 此脚本需要 sudo 权限"
    echo "请使用: sudo bash $0"
    exit 1
fi

# 1. 检查当前配置
echo "[1/6] 检查当前配置..."
echo "----------------------------------------"
HAS_HTTP=$(grep -c "listen 80" "$NGINX_CONFIG" 2>/dev/null || echo "0")
HAS_HTTPS=$(grep -c "listen 443" "$NGINX_CONFIG" 2>/dev/null || echo "0")

echo "HTTP server 块: $HAS_HTTP"
echo "HTTPS server 块: $HAS_HTTPS"
echo ""

# 2. 备份当前配置
echo "[2/6] 备份当前配置..."
echo "----------------------------------------"
BACKUP_DIR="/etc/nginx/backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/aikz.usdt2026.cc.$(date +%Y%m%d_%H%M%S).conf"
if [ -f "$NGINX_CONFIG" ]; then
    sudo cp "$NGINX_CONFIG" "$BACKUP_FILE"
    echo "✅ 配置已备份到: $BACKUP_FILE"
else
    echo "⚠️  配置文件不存在，将创建新配置"
fi
echo ""

# 3. 检查 SSL 证书
echo "[3/6] 检查 SSL 证书..."
echo "----------------------------------------"
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"
if [ -d "$CERT_DIR" ] && [ -f "$CERT_DIR/fullchain.pem" ] && [ -f "$CERT_DIR/privkey.pem" ]; then
    echo "✅ SSL 证书存在"
    CERT_PATH="$CERT_DIR/fullchain.pem"
    KEY_PATH="$CERT_DIR/privkey.pem"
else
    echo "❌ SSL 证书不存在"
    echo "   需要先运行: sudo certbot --nginx -d $DOMAIN"
    exit 1
fi
echo ""

# 4. 创建完整的配置文件（确保 HTTPS 配置存在）
echo "[4/6] 创建完整的配置文件..."
echo "----------------------------------------"

# 读取当前 HTTP server 块的内容（保留所有 location 配置）
HTTP_SERVER_BLOCK=$(sudo awk '/^server {/,/^}$/' "$NGINX_CONFIG" | grep -A 1000 "listen 80" | head -n -1 2>/dev/null || echo "")

# 如果当前配置有 HTTP 块，提取 location 配置
if [ -n "$HTTP_SERVER_BLOCK" ]; then
    echo "✅ 找到现有 HTTP 配置，将保留所有 location 块"
    LOCATION_BLOCKS=$(echo "$HTTP_SERVER_BLOCK" | awk '/location /,/^    }/' 2>/dev/null || echo "")
else
    echo "⚠️  未找到现有 HTTP 配置，将使用模板"
    if [ -f "$CONFIG_TEMPLATE" ]; then
        HTTP_SERVER_BLOCK=$(grep -A 1000 "listen 80" "$CONFIG_TEMPLATE" | head -n -1 2>/dev/null || echo "")
        LOCATION_BLOCKS=$(grep -A 1000 "location /" "$CONFIG_TEMPLATE" | head -n -100 2>/dev/null || echo "")
    fi
fi

# 创建新的配置文件
TEMP_CONFIG=$(mktemp)

# HTTP server 块（重定向到 HTTPS，但保留 ACME 验证）
cat > "$TEMP_CONFIG" << 'HTTP_BLOCK'
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name aikz.usdt2026.cc;
    
    # Let's Encrypt 验证路径（Certbot 需要）
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # 重定向所有其他请求到 HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}
HTTP_BLOCK

# HTTPS server 块
cat >> "$TEMP_CONFIG" << HTTPS_BLOCK_HEADER

# HTTPS server
server {
    listen 443 ssl http2;
    server_name aikz.usdt2026.cc;

    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem;
    
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
    ssl_trusted_certificate /etc/letsencrypt/live/aikz.usdt2026.cc/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    client_max_body_size 50M;
HTTPS_BLOCK_HEADER

# 如果有现有的 location 块，使用它们；否则使用默认配置
if [ -n "$LOCATION_BLOCKS" ] && [ ${#LOCATION_BLOCKS} -gt 100 ]; then
    echo "使用现有的 location 配置..."
    echo "$LOCATION_BLOCKS" >> "$TEMP_CONFIG"
else
    echo "使用默认 location 配置..."
    cat >> "$TEMP_CONFIG" << 'DEFAULT_LOCATIONS'
    # WebSocket 支持 - 通知服务
    location /api/v1/notifications/ws {
        proxy_pass http://127.0.0.1:8000/api/v1/notifications/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_buffering off;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }

    # Next.js 静态资源
    location /_next/static {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        expires 365d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Next.js 静态资源（兼容路径）
    location /next/static {
        rewrite ^/next/static/(.*)$ /_next/static/$1 break;
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        expires 365d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # public 目录资源
    location /public {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        expires 30d;
        access_log off;
    }

    # 前端应用
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
DEFAULT_LOCATIONS
fi

# 关闭 HTTPS server 块
echo "}" >> "$TEMP_CONFIG"

# 测试配置
if sudo nginx -t -c "$TEMP_CONFIG" 2>&1; then
    echo "✅ 新配置语法正确"
    sudo cp "$TEMP_CONFIG" "$NGINX_CONFIG"
    echo "✅ 配置文件已更新"
    rm -f "$TEMP_CONFIG"
else
    echo "❌ 新配置有语法错误"
    echo "保留备份，不更新配置"
    rm -f "$TEMP_CONFIG"
    exit 1
fi
echo ""

# 5. 确保配置文件链接
echo "[5/6] 确保配置文件链接..."
echo "----------------------------------------"
if [ ! -L "$NGINX_ENABLED" ] && [ ! -f "$NGINX_ENABLED" ]; then
    sudo ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"
    echo "✅ 配置文件链接已创建"
elif [ -L "$NGINX_ENABLED" ]; then
    LINK_TARGET=$(readlink -f "$NGINX_ENABLED")
    if [ "$LINK_TARGET" != "$NGINX_CONFIG" ]; then
        sudo rm -f "$NGINX_ENABLED"
        sudo ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"
        echo "✅ 配置文件链接已更新"
    else
        echo "✅ 配置文件链接正确"
    fi
fi
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
    exit 1
fi
echo ""

# 7. 验证端口监听
echo "验证端口监听..."
echo "----------------------------------------"
sleep 2

if sudo ss -tlnp | grep -q ":443 "; then
    echo "✅ 端口 443 正在监听"
    sudo ss -tlnp | grep ":443 "
else
    echo "❌ 端口 443 仍未监听"
    echo "   查看错误日志:"
    sudo tail -20 /var/log/nginx/error.log
fi
echo ""

# 8. 创建配置保护脚本（防止 Certbot 覆盖）
echo "创建配置保护机制..."
echo "----------------------------------------"
cat > /tmp/protect-nginx-config.sh << 'PROTECT_EOF'
#!/bin/bash
# 在 Certbot 执行后自动恢复 HTTPS 配置

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"

# 检查是否有 HTTPS 配置
if ! grep -q "listen 443" "$NGINX_CONFIG"; then
    echo "[AUTO-FIX] 检测到 HTTPS 配置丢失，自动恢复..."
    /home/ubuntu/telegram-ai-system/scripts/server/ensure-https-config-persistent.sh
fi
PROTECT_EOF

sudo mv /tmp/protect-nginx-config.sh /usr/local/bin/protect-nginx-config.sh
sudo chmod +x /usr/local/bin/protect-nginx-config.sh
echo "✅ 配置保护脚本已创建"
echo ""

# 9. 设置 Certbot 后处理钩子
echo "设置 Certbot 后处理钩子..."
echo "----------------------------------------"
CERTBOT_RENEWAL_HOOK="/etc/letsencrypt/renewal-hooks/deploy/ensure-https.sh"
sudo mkdir -p /etc/letsencrypt/renewal-hooks/deploy
sudo cp /usr/local/bin/protect-nginx-config.sh "$CERTBOT_RENEWAL_HOOK"
echo "✅ Certbot 后处理钩子已设置"
echo ""

echo "=========================================="
echo "✅ HTTPS 配置持久化完成"
echo "=========================================="
echo ""
echo "已实施的保护措施："
echo "  1. ✅ 完整的 HTTPS server 块配置"
echo "  2. ✅ 配置文件自动备份"
echo "  3. ✅ Certbot 后处理钩子（自动恢复配置）"
echo "  4. ✅ 配置文件链接验证"
echo ""
echo "验证命令："
echo "  sudo ss -tlnp | grep :443"
echo "  curl -I https://aikz.usdt2026.cc"
echo ""

