#!/bin/bash
# ============================================================
# 修复 aikz.usdt2026.cc 的 Nginx 配置
# 确保 location / 指向端口 3000，而不是 8000
# ============================================================

set -e

DOMAIN="aikz.usdt2026.cc"
CONFIG_FILE="/etc/nginx/sites-available/$DOMAIN"
BACKUP_FILE="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

echo "=========================================="
echo "🔧 修复 $DOMAIN 的 Nginx 配置"
echo "=========================================="
echo ""

# 备份现有配置
if [ -f "$CONFIG_FILE" ]; then
  sudo cp "$CONFIG_FILE" "$BACKUP_FILE"
  echo "✅ 已备份配置到: $BACKUP_FILE"
else
  echo "⚠️  配置文件不存在，将创建新配置"
fi
echo ""

# 检查 SSL 证书
SSL_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
SSL_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
HAS_SSL=false

if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
  HAS_SSL=true
  echo "✅ 检测到 SSL 证书，将配置 HTTPS"
else
  echo "⚠️  未检测到 SSL 证书，仅配置 HTTP"
fi
echo ""

# 生成正确的配置
if [ "$HAS_SSL" = true ]; then
  # HTTPS 配置
  sudo tee "$CONFIG_FILE" > /dev/null <<EOF
# HTTP 到 HTTPS 重定向
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$host\$request_uri;
}

# HTTPS 配置
server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL 证书配置
    ssl_certificate $SSL_CERT;
    ssl_certificate_key $SSL_KEY;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    # 客户端最大请求体大小
    client_max_body_size 50M;
    
    # WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级更高）
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

    # 后端 API（必须在 location / 之前，优先级更高）
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300;
    }
    
    # 前端应用（location / 必须放在最后，优先级最低）
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
    
    # 禁止缓存 HTML（防止 CDN 缓存问题）
    location ~* \.(html|htm)$ {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
        expires off;
    }
}
EOF
else
  # HTTP only 配置
  sudo tee "$CONFIG_FILE" > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # 客户端最大请求体大小
    client_max_body_size 50M;
    
    # WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级更高）
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

    # 后端 API（必须在 location / 之前，优先级更高）
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300;
    }
    
    # 前端应用（location / 必须放在最后，优先级最低）
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
    
    # 禁止缓存 HTML
    location ~* \.(html|htm)$ {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
        expires off;
    }
}
EOF
fi

# 创建符号链接
sudo ln -sf "$CONFIG_FILE" "/etc/nginx/sites-enabled/$DOMAIN"
echo "✅ 配置文件已更新: $CONFIG_FILE"
echo "✅ 符号链接已创建: /etc/nginx/sites-enabled/$DOMAIN"
echo ""

# 验证配置
echo "=========================================="
echo "🧪 验证 Nginx 配置"
echo "=========================================="
echo "检查 location / 的 proxy_pass:"
sudo grep -A 2 "location / {" "$CONFIG_FILE" | grep "proxy_pass" || echo "⚠️  未找到 location / 配置"
echo ""

# 测试 Nginx 配置语法
if sudo nginx -t 2>&1 | grep -q "successful"; then
  echo "✅ Nginx 配置语法正确"
else
  echo "❌ Nginx 配置语法错误"
  sudo nginx -t
  exit 1
fi
echo ""

# 重新加载 Nginx
echo "=========================================="
echo "🔄 重新加载 Nginx"
echo "=========================================="
sudo systemctl reload nginx || sudo systemctl restart nginx
echo "✅ Nginx 已重新加载"
echo ""

# 验证端口映射
echo "=========================================="
echo "🔍 验证端口映射"
echo "=========================================="
echo "检查 location / 的 proxy_pass 端口:"
LOCATION_ROOT_PORT=$(sudo grep -A 5 "location / {" "$CONFIG_FILE" | grep "proxy_pass" | grep -oP "127.0.0.1:\K[0-9]+" | head -1 || echo "")
if [ "$LOCATION_ROOT_PORT" = "3000" ]; then
  echo "  ✅ location / 指向端口 3000 (正确)"
else
  echo "  ❌ location / 指向端口 $LOCATION_ROOT_PORT (错误，应该是 3000)"
fi

echo ""
echo "检查端口 3000 是否在监听:"
if sudo lsof -i :3000 >/dev/null 2>&1; then
  echo "  ✅ 端口 3000 正在监听"
  sudo lsof -i :3000 | head -2
else
  echo "  ⚠️  端口 3000 未监听"
fi

echo ""
echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "请等待 10-30 秒后访问 https://$DOMAIN 测试。"
echo "如果仍然显示错误内容，请清除浏览器缓存或使用无痕模式。"
