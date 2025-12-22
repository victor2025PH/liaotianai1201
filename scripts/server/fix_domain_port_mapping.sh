#!/bin/bash
# ============================================================
# 修复域名到端口的映射关系
# 确保每个域名指向正确的端口
# ============================================================

set -e

echo "=========================================="
echo "🔧 修复域名到端口映射关系"
echo "=========================================="
echo ""

# 定义正确的映射关系
declare -A DOMAIN_PORT_MAP=(
  ["aikz.usdt2026.cc"]="3000"   # saas-demo
  ["aizkw.usdt2026.cc"]="3003"  # aizkw20251219
  ["hongbao.usdt2026.cc"]="3002" # hbwy20251220
  ["tgmini.usdt2026.cc"]="3001"  # tgmini20251220
)

# 定义项目目录映射
declare -A PORT_DIR_MAP=(
  ["3000"]="saas-demo"
  ["3001"]="tgmini20251220"
  ["3002"]="hbwy20251220"
  ["3003"]="aizkw20251219"
)

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"

# 备份现有配置
BACKUP_DIR="/var/backups/nginx_configs_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "📦 备份现有配置到: $BACKUP_DIR"
cp -r "$NGINX_AVAILABLE"/* "$BACKUP_DIR/" 2>/dev/null || true
echo "✅ 备份完成"
echo ""

# 为每个域名创建/更新 Nginx 配置
for DOMAIN in "${!DOMAIN_PORT_MAP[@]}"; do
  PORT="${DOMAIN_PORT_MAP[$DOMAIN]}"
  DIR="${PORT_DIR_MAP[$PORT]}"
  
  echo "=========================================="
  echo "📝 配置域名: $DOMAIN -> 端口 $PORT ($DIR)"
  echo "=========================================="
  
  CONFIG_FILE="$NGINX_AVAILABLE/$DOMAIN"
  
  # 检查是否有 SSL 证书
  SSL_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
  SSL_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
  HAS_SSL=false
  
  if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
    HAS_SSL=true
    echo "✅ 检测到 SSL 证书，将配置 HTTPS"
  else
    echo "⚠️  未检测到 SSL 证书，仅配置 HTTP"
  fi
  
  # 生成 Nginx 配置
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
    
    # 后端 API 转发（如果端口是 3000，需要转发到 8000）
EOF
    
    if [ "$PORT" = "3000" ]; then
      # saas-demo 需要 API 转发
      sudo tee -a "$CONFIG_FILE" > /dev/null <<'API_EOF'
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
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300;
    }
API_EOF
    fi
    
    sudo tee -a "$CONFIG_FILE" > /dev/null <<EOF
    
    # 前端应用
    location / {
        proxy_pass http://127.0.0.1:$PORT;
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
        proxy_pass http://127.0.0.1:$PORT;
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
    
    # 后端 API 转发（如果端口是 3000，需要转发到 8000）
EOF
    
    if [ "$PORT" = "3000" ]; then
      # saas-demo 需要 API 转发
      sudo tee -a "$CONFIG_FILE" > /dev/null <<'API_EOF'
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
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300;
    }
API_EOF
    fi
    
    sudo tee -a "$CONFIG_FILE" > /dev/null <<EOF
    
    # 前端应用
    location / {
        proxy_pass http://127.0.0.1:$PORT;
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
        proxy_pass http://127.0.0.1:$PORT;
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
  sudo ln -sf "$CONFIG_FILE" "$NGINX_ENABLED/$DOMAIN"
  echo "✅ 配置文件已创建: $CONFIG_FILE"
  echo "✅ 符号链接已创建: $NGINX_ENABLED/$DOMAIN"
  echo ""
done

# 测试 Nginx 配置
echo "=========================================="
echo "🧪 测试 Nginx 配置"
echo "=========================================="
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
for DOMAIN in "${!DOMAIN_PORT_MAP[@]}"; do
  PORT="${DOMAIN_PORT_MAP[$DOMAIN]}"
  echo "检查 $DOMAIN -> 端口 $PORT:"
  
  # 检查端口是否在监听
  if sudo lsof -i :$PORT >/dev/null 2>&1; then
    echo "  ✅ 端口 $PORT 正在监听"
  else
    echo "  ⚠️  端口 $PORT 未监听"
  fi
  
  # 检查 Nginx 配置中的端口
  CONFIG_PORT=$(sudo grep -oP "proxy_pass http://127.0.0.1:\K[0-9]+" "$NGINX_AVAILABLE/$DOMAIN" | head -1 || echo "")
  if [ "$CONFIG_PORT" = "$PORT" ]; then
    echo "  ✅ Nginx 配置端口正确: $CONFIG_PORT"
  else
    echo "  ❌ Nginx 配置端口错误: 期望 $PORT，实际 $CONFIG_PORT"
  fi
  echo ""
done

echo "=========================================="
echo "✅ 域名到端口映射修复完成"
echo "=========================================="
echo ""
echo "映射关系："
echo "  aikz.usdt2026.cc   -> 端口 3000 (saas-demo)"
echo "  aizkw.usdt2026.cc  -> 端口 3003 (aizkw20251219)"
echo "  hongbao.usdt2026.cc -> 端口 3002 (hbwy20251220)"
echo "  tgmini.usdt2026.cc -> 端口 3001 (tgmini20251220)"
echo ""
echo "请等待 10-30 秒后访问网站测试。"
