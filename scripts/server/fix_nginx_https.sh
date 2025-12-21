#!/bin/bash

set -e

echo "=========================================="
echo "🔧 修复 Nginx HTTPS 配置"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 三个网站的配置
declare -A SITES=(
  ["tgmini"]="tgmini.usdt2026.cc:3001"
  ["hongbao"]="hongbao.usdt2026.cc:3002"
  ["aizkw"]="aikz.usdt2026.cc:3003"
)

FIXED_COUNT=0

for site in "${!SITES[@]}"; do
  IFS=':' read -r domain port <<< "${SITES[$site]}"
  
  echo "=========================================="
  echo "📝 检查网站: $site ($domain)"
  echo "=========================================="
  echo ""
  
  # 检查 SSL 证书（使用 sudo）
  SSL_CERT=""
  SSL_KEY=""
  
  # 标准路径
  CERT_STD="/etc/letsencrypt/live/$domain/fullchain.pem"
  KEY_STD="/etc/letsencrypt/live/$domain/privkey.pem"
  
  if sudo test -f "$CERT_STD" && sudo test -f "$KEY_STD"; then
    SSL_CERT="$CERT_STD"
    SSL_KEY="$KEY_STD"
    echo "✅ 找到证书（标准路径）: $SSL_CERT"
  else
    # 查找带后缀的证书
    MATCHING=$(sudo find /etc/letsencrypt/live/ -name "${domain}*" -type d 2>/dev/null | head -1)
    if [ -n "$MATCHING" ]; then
      CERT_PATH="$MATCHING/fullchain.pem"
      KEY_PATH="$MATCHING/privkey.pem"
      if sudo test -f "$CERT_PATH" && sudo test -f "$KEY_PATH"; then
        SSL_CERT="$CERT_PATH"
        SSL_KEY="$KEY_PATH"
        echo "✅ 找到证书（带后缀）: $SSL_CERT"
      fi
    fi
  fi
  
  if [ -z "$SSL_CERT" ]; then
    echo "⚠️  未找到 SSL 证书，跳过此网站"
    echo ""
    continue
  fi
  
  # 检查当前配置
  NGINX_CONFIG="/etc/nginx/sites-available/$domain"
  if [ ! -f "$NGINX_CONFIG" ]; then
    echo "⚠️  配置文件不存在: $NGINX_CONFIG"
    echo ""
    continue
  fi
  
  # 检查配置是否包含 HTTPS
  if sudo grep -q "listen 443" "$NGINX_CONFIG"; then
    echo "✅ 配置已包含 HTTPS"
    # 检查证书路径是否正确
    if sudo grep -q "$SSL_CERT" "$NGINX_CONFIG"; then
      echo "✅ 证书路径正确"
    else
      echo "⚠️  证书路径不匹配，需要更新"
      NEED_UPDATE=true
    fi
  else
    echo "❌ 配置缺少 HTTPS，需要添加"
    NEED_UPDATE=true
  fi
  
  if [ "$NEED_UPDATE" = "true" ]; then
    echo ""
    echo "🔄 更新配置为 HTTPS..."
    
    # 生成新的 HTTPS 配置
    NGINX_CONFIG_TMP="/tmp/${site}-nginx-https.conf"
    cat > "$NGINX_CONFIG_TMP" <<EOF
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

    # SSL 证书配置
    ssl_certificate $SSL_CERT;
    ssl_certificate_key $SSL_KEY;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    client_max_body_size 50M;

    # 前端应用
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
    }
}
EOF
    
    # 备份旧配置
    sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ 已备份旧配置"
    
    # 复制新配置
    sudo cp "$NGINX_CONFIG_TMP" "$NGINX_CONFIG"
    echo "✅ 已更新配置: $NGINX_CONFIG"
    
    FIXED_COUNT=$((FIXED_COUNT + 1))
    NEED_UPDATE=false
  fi
  
  echo ""
done

if [ $FIXED_COUNT -gt 0 ]; then
  echo "=========================================="
  echo "🧪 测试 Nginx 配置..."
  echo "----------------------------------------"
  if sudo nginx -t 2>&1; then
    echo "✅ Nginx 配置测试通过"
  else
    echo "❌ Nginx 配置测试失败！"
    sudo nginx -t 2>&1 || true
    echo ""
    echo "⚠️  请手动检查并修复配置错误"
    exit 1
  fi
  echo ""
  
  echo "🔄 重启 Nginx..."
  echo "----------------------------------------"
  if sudo systemctl restart nginx; then
    echo "✅ Nginx 重启成功！"
  else
    echo "❌ Nginx 重启失败！"
    sudo journalctl -u nginx --no-pager -n 50
    exit 1
  fi
  echo ""
  
  echo "🔍 验证端口监听..."
  echo "----------------------------------------"
  sleep 2
  PORT_443=$(sudo netstat -tlnp 2>/dev/null | grep ":443 " || sudo ss -tlnp 2>/dev/null | grep ":443 " || echo "")
  if [ -n "$PORT_443" ]; then
    echo "✅ 端口 443 正在监听"
    echo "$PORT_443"
  else
    echo "⚠️  端口 443 仍未监听，请检查 Nginx 日志"
    sudo tail -20 /var/log/nginx/error.log 2>/dev/null || true
  fi
  echo ""
fi

echo "=========================================="
echo "✅ 修复完成！"
echo "修复了 $FIXED_COUNT 个网站的配置"
echo "时间: $(date)"
echo "=========================================="
