#!/bin/bash

set -e

echo "=========================================="
echo "🔧 一键修复所有 502 问题"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 确保以 root 权限运行
if [ "$EUID" -ne 0 ]; then
  echo "⚠️  此脚本需要 sudo 权限，请使用: sudo bash $0"
  exit 1
fi

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 步骤 1: 修复 Nginx 配置
echo "1️⃣ 修复 Nginx 配置..."
echo "----------------------------------------"
cd "$PROJECT_DIR"

if [ -f "scripts/server/fix_nginx_final.sh" ]; then
  echo "运行 Nginx 配置修复脚本..."
  bash scripts/server/fix_nginx_final.sh
else
  echo "⚠️  fix_nginx_final.sh 不存在，手动创建配置..."
  
  # 网站配置：域名 -> 端口
  declare -A SITES=(
    ["tgmini.usdt2026.cc"]="3001"
    ["hongbao.usdt2026.cc"]="3002"
    ["aikz.usdt2026.cc"]="3000"
  )
  
  for domain in "${!SITES[@]}"; do
    port="${SITES[$domain]}"
    
    # 检查证书
    SSL_CERT="/etc/letsencrypt/live/$domain/fullchain.pem"
    SSL_KEY="/etc/letsencrypt/live/$domain/privkey.pem"
    
    if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
      echo "✅ 为 $domain 创建 HTTPS 配置..."
      
      NGINX_CONFIG="/etc/nginx/sites-available/$domain"
      cat > "$NGINX_CONFIG" <<EOF
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name $domain;
    
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
    server_name $domain;

    ssl_certificate $SSL_CERT;
    ssl_certificate_key $SSL_KEY;
    
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
      
      # 创建符号链接
      rm -f "/etc/nginx/sites-enabled/$domain"
      ln -sf "$NGINX_CONFIG" "/etc/nginx/sites-enabled/$domain"
      echo "✅ $domain 配置已创建"
    else
      echo "⚠️  $domain 证书不存在，创建 HTTP only 配置..."
      
      NGINX_CONFIG="/etc/nginx/sites-available/$domain"
      cat > "$NGINX_CONFIG" <<EOF
server {
    listen 80;
    server_name $domain;

    client_max_body_size 50M;

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
      
      rm -f "/etc/nginx/sites-enabled/$domain"
      ln -sf "$NGINX_CONFIG" "/etc/nginx/sites-enabled/$domain"
      echo "✅ $domain HTTP 配置已创建"
    fi
  done
  
  # 处理 aizkw（可能使用 aikz 的证书）
  AIZKW_DOMAIN="aizkw.usdt2026.cc"
  AIZKW_PORT="3003"
  
  # 检查 aizkw 是否有自己的证书
  if [ -f "/etc/letsencrypt/live/$AIZKW_DOMAIN/fullchain.pem" ]; then
    SSL_CERT="/etc/letsencrypt/live/$AIZKW_DOMAIN/fullchain.pem"
    SSL_KEY="/etc/letsencrypt/live/$AIZKW_DOMAIN/privkey.pem"
    HAS_SSL=true
  elif [ -f "/etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem" ]; then
    # 使用 aikz 的证书
    SSL_CERT="/etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem"
    SSL_KEY="/etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem"
    HAS_SSL=true
  else
    HAS_SSL=false
  fi
  
  NGINX_CONFIG_AIZKW="/etc/nginx/sites-available/$AIZKW_DOMAIN"
  if [ "$HAS_SSL" = "true" ]; then
    cat > "$NGINX_CONFIG_AIZKW" <<EOF
server {
    listen 80;
    server_name $AIZKW_DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $AIZKW_DOMAIN;

    ssl_certificate $SSL_CERT;
    ssl_certificate_key $SSL_KEY;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
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
    cat > "$NGINX_CONFIG_AIZKW" <<EOF
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
  
  rm -f "/etc/nginx/sites-enabled/$AIZKW_DOMAIN"
  ln -sf "$NGINX_CONFIG_AIZKW" "/etc/nginx/sites-enabled/$AIZKW_DOMAIN"
  echo "✅ $AIZKW_DOMAIN 配置已创建"
fi

echo ""

# 步骤 2: 测试并重启 Nginx
echo "2️⃣ 测试并重启 Nginx..."
echo "----------------------------------------"
if nginx -t 2>&1; then
  echo "✅ Nginx 配置测试通过"
  systemctl restart nginx
  sleep 2
  if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 重启成功"
  else
    echo "❌ Nginx 重启失败"
    systemctl status nginx --no-pager -l | head -20
    exit 1
  fi
else
  echo "❌ Nginx 配置测试失败"
  nginx -t 2>&1 || true
  exit 1
fi
echo ""

# 步骤 3: 检查前端服务
echo "3️⃣ 检查前端服务状态..."
echo "----------------------------------------"
for port in 3001 3002 3003; do
  PORT_STATUS=$(netstat -tlnp 2>/dev/null | grep ":$port " || ss -tlnp 2>/dev/null | grep ":$port " || echo "")
  if [ -n "$PORT_STATUS" ]; then
    echo "✅ 端口 $port 正在监听"
  else
    echo "❌ 端口 $port 未监听"
    echo "   需要启动前端服务或上传项目文件"
  fi
done
echo ""

# 步骤 4: 验证配置
echo "4️⃣ 验证 Nginx 配置..."
echo "----------------------------------------"
DOMAINS=("tgmini.usdt2026.cc" "hongbao.usdt2026.cc" "aikz.usdt2026.cc" "aizkw.usdt2026.cc")
for domain in "${DOMAINS[@]}"; do
  CONFIG_FILE="/etc/nginx/sites-enabled/$domain"
  if [ -f "$CONFIG_FILE" ] || [ -L "$CONFIG_FILE" ]; then
    echo "✅ $domain: 配置存在"
  else
    echo "❌ $domain: 配置不存在"
  fi
done
echo ""

echo "=========================================="
echo "✅ 修复完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 如果端口 3002 或 3003 未监听，需要上传项目文件并构建"
echo "2. 运行诊断脚本验证: bash scripts/server/check_502_issues.sh"
echo "3. 测试网站访问: curl -I https://tgmini.usdt2026.cc"
