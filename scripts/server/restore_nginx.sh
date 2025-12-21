#!/bin/bash

set -e

echo "=========================================="
echo "🔧 恢复 Nginx 配置"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 项目根目录（根据实际情况调整）
PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/telegram-ai-system}"

# 如果项目目录不存在，尝试从当前脚本位置推断
if [ ! -d "$PROJECT_DIR" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
  echo "⚠️  使用推断的项目目录: $PROJECT_DIR"
fi

# 三个网站的配置
declare -A SITES=(
  ["tgmini"]="tgmini.usdt2026.cc:3001"
  ["hongbao"]="hongbao.usdt2026.cc:3002"
  ["aizkw"]="aikz.usdt2026.cc:3003"
)

echo "📋 需要恢复的网站配置:"
for site in "${!SITES[@]}"; do
  IFS=':' read -r domain port <<< "${SITES[$site]}"
  echo "  - $site: $domain (端口 $port)"
done
echo ""

# 检查 Nginx 是否安装
if ! command -v nginx >/dev/null 2>&1; then
  echo "⚠️  Nginx 未安装，安装 Nginx..."
  sudo apt-get update -qq
  sudo apt-get install -y nginx || {
    echo "❌ Nginx 安装失败"
    exit 1
  }
fi
echo "✅ Nginx 已安装: $(nginx -v 2>&1 | head -1)"
echo ""

# 恢复每个网站的配置
SUCCESS_COUNT=0
FAILED_SITES=()

for site in "${!SITES[@]}"; do
  IFS=':' read -r domain port <<< "${SITES[$site]}"
  
  echo "=========================================="
  echo "📝 处理网站: $site"
  echo "域名: $domain"
  echo "端口: $port"
  echo "=========================================="
  echo ""
  
  # 检查 SSL 证书是否存在（使用 sudo 避免权限问题）
  SSL_CERT="/etc/letsencrypt/live/$domain/fullchain.pem"
  SSL_KEY="/etc/letsencrypt/live/$domain/privkey.pem"
  
  # 首先检查标准路径（使用 sudo）
  if sudo test -f "$SSL_CERT" && sudo test -f "$SSL_KEY"; then
    echo "✅ SSL 证书存在（标准路径）: $SSL_CERT"
    HAS_SSL=true
  else
    # 尝试查找带 -0001 后缀的证书（使用 sudo）
    CERT_DIR="/etc/letsencrypt/live/"
    if sudo test -d "$CERT_DIR"; then
      # 查找匹配的证书目录（使用 sudo find）
      MATCHING_CERT=$(sudo find "$CERT_DIR" -name "${domain}*" -type d 2>/dev/null | head -1)
      if [ -n "$MATCHING_CERT" ]; then
        CERT_FULLCHAIN="$MATCHING_CERT/fullchain.pem"
        CERT_PRIVKEY="$MATCHING_CERT/privkey.pem"
        if sudo test -f "$CERT_FULLCHAIN" && sudo test -f "$CERT_PRIVKEY"; then
          SSL_CERT="$CERT_FULLCHAIN"
          SSL_KEY="$CERT_PRIVKEY"
          echo "✅ 找到证书（带后缀）: $SSL_CERT"
          HAS_SSL=true
        else
          echo "⚠️  证书目录存在但文件不完整: $MATCHING_CERT"
          HAS_SSL=false
        fi
      else
        echo "⚠️  未找到证书目录（域名: $domain）"
        HAS_SSL=false
      fi
    else
      echo "⚠️  证书目录不存在: $CERT_DIR"
      HAS_SSL=false
    fi
  fi
  
  if [ "$HAS_SSL" = "true" ]; then
    echo "✅ SSL 证书存在，配置 HTTPS"
  else
    echo "⚠️  SSL 证书不存在，配置 HTTP only"
  fi
  echo ""
  
  # 生成 Nginx 配置
  NGINX_CONFIG="/tmp/${site}-nginx.conf"
  
  if [ "$HAS_SSL" = "true" ]; then
    # HTTPS 配置
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

    # SSL 证书配置（由 Certbot 自动管理）
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
  else
    # HTTP only 配置
    cat > "$NGINX_CONFIG" <<EOF
# HTTP server (SSL certificate not found)
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
  fi
  
  echo "✅ Nginx 配置已生成: $NGINX_CONFIG"
  echo ""
  
  # 复制配置到 Nginx sites-available
  NGINX_AVAILABLE="/etc/nginx/sites-available/$domain"
  sudo cp "$NGINX_CONFIG" "$NGINX_AVAILABLE"
  echo "✅ 配置已复制到: $NGINX_AVAILABLE"
  
  # 创建符号链接到 sites-enabled
  NGINX_ENABLED="/etc/nginx/sites-enabled/$domain"
  if [ -L "$NGINX_ENABLED" ]; then
    echo "⚠️  符号链接已存在，删除旧链接..."
    sudo rm -f "$NGINX_ENABLED"
  fi
  sudo ln -s "$NGINX_AVAILABLE" "$NGINX_ENABLED"
  echo "✅ 符号链接已创建: $NGINX_ENABLED"
  echo ""
  
  SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
done

echo "=========================================="
echo "📊 配置恢复结果"
echo "=========================================="
echo "成功恢复: $SUCCESS_COUNT / ${#SITES[@]}"
echo ""

# 测试 Nginx 配置
echo "🧪 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
  echo "✅ Nginx 配置测试通过"
else
  echo "❌ Nginx 配置测试失败！"
  echo "查看详细错误："
  sudo nginx -t 2>&1 || true
  echo ""
  echo "⚠️  请检查配置文件并修复错误后再重启 Nginx"
  exit 1
fi
echo ""

# 重启 Nginx
echo "🔄 重启 Nginx..."
echo "----------------------------------------"
if sudo systemctl restart nginx; then
  echo "✅ Nginx 重启成功！"
else
  echo "❌ Nginx 重启失败！"
  echo "查看日志："
  sudo journalctl -u nginx --no-pager -n 50
  exit 1
fi
echo ""

# 验证 Nginx 状态
echo "🔍 验证 Nginx 状态..."
echo "----------------------------------------"
sleep 2
if sudo systemctl is-active --quiet nginx; then
  echo "✅ Nginx 服务正常运行中"
else
  echo "❌ Nginx 服务未运行"
  sudo systemctl status nginx --no-pager -l | head -20 || true
  exit 1
fi
echo ""

# 检查端口监听
echo "🔍 检查端口监听..."
echo "----------------------------------------"
PORT_80=$(sudo netstat -tlnp 2>/dev/null | grep ":80 " || sudo ss -tlnp 2>/dev/null | grep ":80 " || echo "")
PORT_443=$(sudo netstat -tlnp 2>/dev/null | grep ":443 " || sudo ss -tlnp 2>/dev/null | grep ":443 " || echo "")

if [ -n "$PORT_80" ]; then
  echo "✅ 端口 80 正在监听"
  echo "$PORT_80"
else
  echo "❌ 端口 80 未监听"
fi
echo ""

if [ -n "$PORT_443" ]; then
  echo "✅ 端口 443 正在监听"
  echo "$PORT_443"
else
  echo "❌ 端口 443 未监听"
  echo "⚠️  这可能导致 HTTPS 无法访问"
  echo "   可能原因："
  echo "   1. 所有网站都配置为 HTTP only（缺少 SSL 证书）"
  echo "   2. Nginx 配置中没有 HTTPS server 块"
  echo "   3. 证书路径配置错误"
fi
echo ""

# 检查前端服务端口
echo "🔍 检查前端服务端口..."
echo "----------------------------------------"
for site in "${!SITES[@]}"; do
  IFS=':' read -r domain port <<< "${SITES[$site]}"
  PORT_STATUS=$(sudo netstat -tlnp 2>/dev/null | grep ":$port " || sudo ss -tlnp 2>/dev/null | grep ":$port " || echo "")
  if [ -n "$PORT_STATUS" ]; then
    echo "✅ 端口 $port ($domain) 正在监听"
  else
    echo "❌ 端口 $port ($domain) 未监听 - 前端服务可能未启动"
  fi
done
echo ""

# 列出已启用的配置
echo "📋 已启用的 Nginx 配置:"
echo "----------------------------------------"
ls -la /etc/nginx/sites-enabled/ || true
echo ""

echo "=========================================="
echo "✅ Nginx 配置恢复完成！"
echo "时间: $(date)"
echo "=========================================="
