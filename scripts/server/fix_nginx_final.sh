#!/bin/bash

set -e

echo "=========================================="
echo "🔧 强制修复 Nginx HTTPS 配置"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 确保以 root 权限运行
if [ "$EUID" -ne 0 ]; then
  echo "⚠️  此脚本需要 sudo 权限，请使用: sudo bash $0"
  exit 1
fi

# 网站配置：域名 -> 端口
declare -A SITES=(
  ["tgmini.usdt2026.cc"]="3001"
  ["hongbao.usdt2026.cc"]="3002"
  ["aikz.usdt2026.cc"]="3003"
)

# aizkw 特殊处理（如果没有证书，使用 HTTP only）
AIZKW_DOMAIN="aizkw.usdt2026.cc"
AIZKW_PORT="3003"
AIZKW_HAS_CERT=false

# 检查 aizkw 是否有证书
if [ -f "/etc/letsencrypt/live/$AIZKW_DOMAIN/fullchain.pem" ] && [ -f "/etc/letsencrypt/live/$AIZKW_DOMAIN/privkey.pem" ]; then
  AIZKW_HAS_CERT=true
  echo "✅ 检测到 $AIZKW_DOMAIN 的证书"
else
  # 检查是否有带后缀的证书
  MATCHING=$(find /etc/letsencrypt/live/ -name "${AIZKW_DOMAIN}*" -type d 2>/dev/null | head -1)
  if [ -n "$MATCHING" ] && [ -f "$MATCHING/fullchain.pem" ] && [ -f "$MATCHING/privkey.pem" ]; then
    AIZKW_HAS_CERT=true
    AIZKW_CERT_PATH="$MATCHING/fullchain.pem"
    AIZKW_KEY_PATH="$MATCHING/privkey.pem"
    echo "✅ 检测到 $AIZKW_DOMAIN 的证书（带后缀）: $AIZKW_CERT_PATH"
  else
    echo "⚠️  $AIZKW_DOMAIN 没有证书，将配置为 HTTP only"
  fi
fi
echo ""

# 处理每个有证书的网站
for domain in "${!SITES[@]}"; do
  port="${SITES[$domain]}"
  
  echo "=========================================="
  echo "📝 配置网站: $domain (端口 $port)"
  echo "=========================================="
  
  # 硬编码证书路径
  SSL_CERT="/etc/letsencrypt/live/$domain/fullchain.pem"
  SSL_KEY="/etc/letsencrypt/live/$domain/privkey.pem"
  
  # 验证证书是否存在
  if [ ! -f "$SSL_CERT" ] || [ ! -f "$SSL_KEY" ]; then
    echo "❌ 证书不存在: $SSL_CERT"
    echo "   跳过此网站"
    continue
  fi
  
  echo "✅ 证书路径: $SSL_CERT"
  echo "✅ 私钥路径: $SSL_KEY"
  
  # 生成 Nginx 配置
  NGINX_CONFIG="/etc/nginx/sites-available/$domain"
  
  cat > "$NGINX_CONFIG" <<EOF
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name $domain;
    
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
    server_name $domain;

    # SSL 证书配置（硬编码路径）
    ssl_certificate $SSL_CERT;
    ssl_certificate_key $SSL_KEY;
    
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
    ssl_trusted_certificate /etc/letsencrypt/live/$domain/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    client_max_body_size 50M;

    # 前端应用反向代理
    location / {
        proxy_pass http://127.0.0.1:$port;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
    }
}
EOF
  
  echo "✅ 配置文件已生成: $NGINX_CONFIG"
  
  # 强制创建符号链接（删除旧的）
  NGINX_ENABLED="/etc/nginx/sites-enabled/$domain"
  rm -f "$NGINX_ENABLED"
  ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"
  echo "✅ 符号链接已创建: $NGINX_ENABLED"
  echo ""
done

# 处理 aizkw.usdt2026.cc
echo "=========================================="
echo "📝 配置网站: $AIZKW_DOMAIN (端口 $AIZKW_PORT)"
echo "=========================================="

NGINX_CONFIG_AIZKW="/etc/nginx/sites-available/$AIZKW_DOMAIN"

if [ "$AIZKW_HAS_CERT" = "true" ]; then
  # 如果有证书，使用 HTTPS 配置
  if [ -n "$AIZKW_CERT_PATH" ]; then
    SSL_CERT_AIZKW="$AIZKW_CERT_PATH"
    SSL_KEY_AIZKW="$AIZKW_KEY_PATH"
  else
    SSL_CERT_AIZKW="/etc/letsencrypt/live/$AIZKW_DOMAIN/fullchain.pem"
    SSL_KEY_AIZKW="/etc/letsencrypt/live/$AIZKW_DOMAIN/privkey.pem"
  fi
  
  echo "✅ 使用证书: $SSL_CERT_AIZKW"
  
  cat > "$NGINX_CONFIG_AIZKW" <<EOF
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name $AIZKW_DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name $AIZKW_DOMAIN;

    ssl_certificate $SSL_CERT_AIZKW;
    ssl_certificate_key $SSL_KEY_AIZKW;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:$AIZKW_PORT;
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
else
  # 没有证书，使用 HTTP only
  echo "⚠️  没有证书，配置为 HTTP only"
  
  cat > "$NGINX_CONFIG_AIZKW" <<EOF
# HTTP server (SSL certificate not available)
server {
    listen 80;
    server_name $AIZKW_DOMAIN;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:$AIZKW_PORT;
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

echo "✅ 配置文件已生成: $NGINX_CONFIG_AIZKW"

# 强制创建符号链接
NGINX_ENABLED_AIZKW="/etc/nginx/sites-enabled/$AIZKW_DOMAIN"
rm -f "$NGINX_ENABLED_AIZKW"
ln -sf "$NGINX_CONFIG_AIZKW" "$NGINX_ENABLED_AIZKW"
echo "✅ 符号链接已创建: $NGINX_ENABLED_AIZKW"
echo ""

# 测试 Nginx 配置
echo "=========================================="
echo "🧪 测试 Nginx 配置..."
echo "=========================================="
if nginx -t 2>&1; then
  echo "✅ Nginx 配置测试通过"
else
  echo "❌ Nginx 配置测试失败！"
  echo "查看详细错误："
  nginx -t 2>&1 || true
  echo ""
  echo "⚠️  请检查配置文件并修复错误"
  exit 1
fi
echo ""

# 重启 Nginx
echo "=========================================="
echo "🔄 重启 Nginx..."
echo "=========================================="
if systemctl restart nginx; then
  echo "✅ Nginx 重启成功！"
else
  echo "❌ Nginx 重启失败！"
  echo "查看日志："
  journalctl -u nginx --no-pager -n 50
  exit 1
fi
echo ""

# 验证服务状态
echo "=========================================="
echo "🔍 验证服务状态..."
echo "=========================================="
sleep 2

if systemctl is-active --quiet nginx; then
  echo "✅ Nginx 服务正常运行中"
else
  echo "❌ Nginx 服务未运行"
  systemctl status nginx --no-pager -l | head -20
  exit 1
fi
echo ""

# 检查端口监听
echo "检查端口监听..."
PORT_80=$(netstat -tlnp 2>/dev/null | grep ":80 " || ss -tlnp 2>/dev/null | grep ":80 " || echo "")
PORT_443=$(netstat -tlnp 2>/dev/null | grep ":443 " || ss -tlnp 2>/dev/null | grep ":443 " || echo "")

if [ -n "$PORT_80" ]; then
  echo "✅ 端口 80 正在监听"
else
  echo "❌ 端口 80 未监听"
fi

if [ -n "$PORT_443" ]; then
  echo "✅ 端口 443 正在监听"
  echo "$PORT_443"
else
  echo "❌ 端口 443 未监听"
fi
echo ""

# 列出已启用的配置
echo "=========================================="
echo "📋 已启用的 Nginx 配置:"
echo "=========================================="
ls -la /etc/nginx/sites-enabled/ | grep -E "(hongbao|tgmini|aikz|aizkw)" || echo "未找到相关配置"
echo ""

echo "=========================================="
echo "✅ Nginx HTTPS 配置修复完成！"
echo "时间: $(date)"
echo "=========================================="
