#!/bin/bash

# 修复 aikz.usdt2026.cc 的 Nginx 配置
# 将其指向 saas-demo (聊天AI后台) 而不是 aizkw20251219
# 使用方法: sudo bash scripts/server/fix_aikz_nginx.sh

set -e

echo "=========================================="
echo "🔧 修复 aikz.usdt2026.cc 的 Nginx 配置"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 确保以 root 权限运行
if [ "$EUID" -ne 0 ]; then
  echo "⚠️  此脚本需要 sudo 权限，请使用: sudo bash $0"
  exit 1
fi

DOMAIN="aikz.usdt2026.cc"
BACKEND_PORT="3000"  # saas-demo (Next.js) 运行在端口 3000
NGINX_CONFIG="/etc/nginx/sites-available/$DOMAIN"

echo "域名: $DOMAIN"
echo "后端端口: $BACKEND_PORT (saas-demo)"
echo "配置文件: $NGINX_CONFIG"
echo ""

# 检查 SSL 证书
SSL_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
SSL_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
HAS_SSL=false

if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
  HAS_SSL=true
  echo "✅ SSL 证书存在"
else
  # 检查是否有带后缀的证书
  MATCHING=$(find /etc/letsencrypt/live/ -name "${DOMAIN}*" -type d 2>/dev/null | head -1)
  if [ -n "$MATCHING" ] && [ -f "$MATCHING/fullchain.pem" ] && [ -f "$MATCHING/privkey.pem" ]; then
    SSL_CERT="$MATCHING/fullchain.pem"
    SSL_KEY="$MATCHING/privkey.pem"
    HAS_SSL=true
    echo "✅ SSL 证书存在（带后缀）: $SSL_CERT"
  else
    echo "⚠️  SSL 证书不存在，将配置为 HTTP only"
  fi
fi
echo ""

# 检查 saas-demo 是否在运行
echo "检查 saas-demo 服务状态..."
if lsof -i :$BACKEND_PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$BACKEND_PORT "; then
  echo "✅ 端口 $BACKEND_PORT 正在监听"
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$BACKEND_PORT 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    echo "✅ saas-demo 服务响应正常 (HTTP $HTTP_CODE)"
  else
    echo "⚠️  saas-demo 服务响应异常 (HTTP $HTTP_CODE)"
  fi
else
  echo "⚠️  端口 $BACKEND_PORT 未监听"
  echo "   请确保 saas-demo 服务已启动"
  echo "   启动命令: cd /home/ubuntu/telegram-ai-system/saas-demo && npm run build && npm start"
fi
echo ""

# 生成 Nginx 配置
echo "生成 Nginx 配置..."

if [ "$HAS_SSL" = "true" ]; then
  # HTTPS 配置
  cat > "$NGINX_CONFIG" <<EOF
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name $DOMAIN;
    
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
    server_name $DOMAIN;

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

    # Next.js 应用反向代理
    location / {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
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
        
        # Next.js 特殊配置
        proxy_buffering off;
    }
    
    # Next.js 静态文件
    location /_next/static {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_cache_valid 200 60m;
        add_header Cache-Control "public, immutable";
    }
    
    # API 代理（如果需要）
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
else
  # HTTP only 配置
  cat > "$NGINX_CONFIG" <<EOF
# HTTP server (SSL certificate not available)
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 50M;

    # Next.js 应用反向代理
    location / {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
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
        
        # Next.js 特殊配置
        proxy_buffering off;
    }
    
    # Next.js 静态文件
    location /_next/static {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_cache_valid 200 60m;
        add_header Cache-Control "public, immutable";
    }
    
    # API 代理（如果需要）
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
fi

echo "✅ 配置文件已生成: $NGINX_CONFIG"
echo ""

# 创建符号链接
NGINX_ENABLED="/etc/nginx/sites-enabled/$DOMAIN"
rm -f "$NGINX_ENABLED"
ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"
echo "✅ 符号链接已创建: $NGINX_ENABLED"
echo ""

# 测试 Nginx 配置
echo "测试 Nginx 配置..."
if nginx -t 2>&1; then
  echo "✅ Nginx 配置测试通过"
else
  echo "❌ Nginx 配置测试失败！"
  nginx -t 2>&1 || true
  exit 1
fi
echo ""

# 重启 Nginx
echo "重启 Nginx..."
if systemctl restart nginx; then
  echo "✅ Nginx 重启成功！"
else
  echo "❌ Nginx 重启失败！"
  journalctl -u nginx --no-pager -n 50
  exit 1
fi
echo ""

# 验证服务状态
echo "验证服务状态..."
sleep 3

if systemctl is-active --quiet nginx; then
  echo "✅ Nginx 服务正常运行中"
else
  echo "❌ Nginx 服务未运行"
  systemctl status nginx --no-pager -l | head -20
  exit 1
fi

# 检查端口监听
echo ""
echo "检查端口监听..."
PORT_80=$(netstat -tlnp 2>/dev/null | grep ":80 " || ss -tlnp 2>/dev/null | grep ":80 " || echo "")
PORT_443=$(netstat -tlnp 2>/dev/null | grep ":443 " || ss -tlnp 2>/dev/null | grep ":443 " || echo "")

if [ -n "$PORT_80" ]; then
  echo "✅ 端口 80 正在监听"
else
  echo "❌ 端口 80 未监听"
fi

if [ "$HAS_SSL" = "true" ]; then
  if [ -n "$PORT_443" ]; then
    echo "✅ 端口 443 正在监听"
  else
    echo "❌ 端口 443 未监听"
  fi
fi

echo ""
echo "=========================================="
echo "✅ Nginx 配置修复完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "访问地址："
if [ "$HAS_SSL" = "true" ]; then
  echo "  HTTPS: https://$DOMAIN"
else
  echo "  HTTP: http://$DOMAIN"
fi
echo ""
echo "如果 saas-demo 未运行，请执行："
echo "  cd /home/ubuntu/telegram-ai-system/saas-demo"
echo "  npm run build"
echo "  npm start"
echo "  或使用 PM2: pm2 start npm --name saas-demo -- start"
