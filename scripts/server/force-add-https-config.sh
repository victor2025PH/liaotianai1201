#!/bin/bash
# ============================================================
# 强制添加 HTTPS 配置到 Nginx
# ============================================================

set -e

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"

echo "=========================================="
echo "🔒 强制添加 HTTPS 配置"
echo "=========================================="
echo ""

# 检查是否以 root 或 sudo 运行
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "❌ 此脚本需要 sudo 权限"
    echo "请使用: sudo bash $0"
    exit 1
fi

# 1. 检查 SSL 证书
echo "[1/4] 检查 SSL 证书..."
echo "----------------------------------------"
if [ -d "$CERT_DIR" ] && [ -f "$CERT_DIR/fullchain.pem" ] && [ -f "$CERT_DIR/privkey.pem" ]; then
    echo "✅ SSL 证书存在"
    echo "   证书: $CERT_DIR/fullchain.pem"
    echo "   密钥: $CERT_DIR/privkey.pem"
else
    echo "❌ SSL 证书不存在"
    echo "   请先运行: sudo certbot certonly --nginx -d $DOMAIN"
    exit 1
fi
echo ""

# 2. 备份当前配置
echo "[2/4] 备份当前配置..."
echo "----------------------------------------"
if [ -f "$NGINX_CONFIG" ]; then
    BACKUP_FILE="${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    sudo cp "$NGINX_CONFIG" "$BACKUP_FILE"
    echo "✅ 配置已备份到: $BACKUP_FILE"
else
    echo "❌ 配置文件不存在: $NGINX_CONFIG"
    exit 1
fi
echo ""

# 3. 检查是否已有 HTTPS 配置
echo "[3/4] 检查当前配置..."
echo "----------------------------------------"
if grep -q "listen 443" "$NGINX_CONFIG"; then
    echo "⚠️  配置中已包含 HTTPS，但可能配置不正确"
    echo "   将添加完整的 HTTPS server 块"
else
    echo "✅ 配置中缺少 HTTPS，将添加"
fi
echo ""

# 4. 添加 HTTPS 配置
echo "[4/4] 添加 HTTPS 配置..."
echo "----------------------------------------"

# 创建临时文件
TEMP_CONFIG=$(mktemp)

# 读取当前配置
sudo cat "$NGINX_CONFIG" > "$TEMP_CONFIG"

# 检查是否已有 HTTPS server 块
if grep -q "listen 443" "$TEMP_CONFIG"; then
    echo "⚠️  检测到已有 HTTPS 配置，将替换"
    # 删除旧的 HTTPS server 块（从 "listen 443" 到对应的 "}"）
    # 这是一个简化的方法，实际应该更精确
    sudo sed -i '/listen 443/,/^}$/d' "$TEMP_CONFIG"
fi

# 在文件末尾添加 HTTPS server 块
cat >> "$TEMP_CONFIG" << 'HTTPS_CONFIG'

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

HTTPS_CONFIG

# 从 HTTP server 块复制所有 location 块（除了第一个 server 声明）
# 提取 HTTP server 块中的内容（从第一个 location 开始到最后一个 }）
HTTP_CONTENT=$(sudo sed -n '/^server {/,/^}$/p' "$TEMP_CONFIG" | sed -n '/location/,/^    }/p' | head -n -1)

# 添加所有 location 块到 HTTPS server 块
if [ -n "$HTTP_CONTENT" ]; then
    # 从原始配置中提取所有 location 块
    sudo awk '/^server {/,/^}$/ {if (/^    location/ || /^        /) print}' "$NGINX_CONFIG" >> "$TEMP_CONFIG"
fi

# 添加 HTTPS server 块的结束
echo "}" >> "$TEMP_CONFIG"

# 测试配置
if sudo nginx -t -c "$TEMP_CONFIG" 2>&1; then
    echo "✅ 新配置语法正确"
    # 应用配置
    sudo cp "$TEMP_CONFIG" "$NGINX_CONFIG"
    echo "✅ HTTPS 配置已添加"
else
    echo "❌ 新配置有语法错误，使用更简单的方法..."
    
    # 使用更简单的方法：直接追加完整的 HTTPS server 块
    # 从 HTTP server 块复制所有内容
    HTTP_SERVER_BLOCK=$(sudo awk '/^server {/,/^}$/' "$NGINX_CONFIG" | head -n -1)
    
    # 创建新的配置文件
    sudo cp "$BACKUP_FILE" "$TEMP_CONFIG"
    
    # 添加 HTTPS server 块（复制 HTTP 的内容但改为 443）
    cat >> "$TEMP_CONFIG" << EOF

# HTTPS server
server {
    listen 443 ssl http2;
    server_name aikz.usdt2026.cc;

    ssl_certificate /etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    client_max_body_size 50M;
EOF

    # 复制所有 location 块
    sudo sed -n '/^    location/,/^    }/p' "$NGINX_CONFIG" >> "$TEMP_CONFIG"
    
    # 添加结束
    echo "}" >> "$TEMP_CONFIG"
    
    # 再次测试
    if sudo nginx -t -c "$TEMP_CONFIG" 2>&1; then
        sudo cp "$TEMP_CONFIG" "$NGINX_CONFIG"
        echo "✅ HTTPS 配置已添加（使用简化方法）"
    else
        echo "❌ 配置仍有错误，请手动检查"
        echo "临时配置文件: $TEMP_CONFIG"
        exit 1
    fi
fi

# 清理临时文件
rm -f "$TEMP_CONFIG"

echo ""

# 5. 测试并重新加载
echo "测试 Nginx 配置..."
if sudo nginx -t 2>&1; then
    echo "✅ 配置测试成功"
    echo "重新加载 Nginx..."
    sudo systemctl reload nginx
    sleep 2
    
    # 检查端口
    if sudo ss -tlnp | grep -q ":443 "; then
        echo "✅ 端口 443 (HTTPS) 正在监听"
    else
        echo "⚠️  端口 443 仍未监听，尝试重启 Nginx..."
        sudo systemctl restart nginx
    fi
else
    echo "❌ 配置测试失败"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ HTTPS 配置已添加"
echo "=========================================="
echo ""

