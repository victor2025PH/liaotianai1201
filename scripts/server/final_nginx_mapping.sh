#!/bin/bash

# 最终 Nginx 映射配置脚本
# 强制重写 Nginx 配置以符合最终映射表
# 使用方法: bash scripts/server/final_nginx_mapping.sh

set -e

echo "=========================================="
echo "🔧 最终 Nginx 映射配置"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 定义映射表
declare -A DOMAIN_MAPPING
DOMAIN_MAPPING["aikz.usdt2026.cc"]="3000"
DOMAIN_MAPPING["tgmini.usdt2026.cc"]="3001"
DOMAIN_MAPPING["hongbao.usdt2026.cc"]="3002"
DOMAIN_MAPPING["aizkw.usdt2026.cc"]="3003"

# 定义目录映射（用于日志和说明）
declare -A DIR_MAPPING
DIR_MAPPING["aikz.usdt2026.cc"]="saas-demo"
DIR_MAPPING["tgmini.usdt2026.cc"]="tgmini20251220"
DIR_MAPPING["hongbao.usdt2026.cc"]="hbwy20251220"
DIR_MAPPING["aizkw.usdt2026.cc"]="aizkw20251219"

SITES_AVAILABLE="/etc/nginx/sites-available"
SITES_ENABLED="/etc/nginx/sites-enabled"

# 1. 备份现有配置
echo "1. 备份现有配置..."
echo "----------------------------------------"
BACKUP_DIR="/tmp/nginx_backup_$(date +%Y%m%d_%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"
sudo cp -r "$SITES_AVAILABLE"/* "$BACKUP_DIR/" 2>/dev/null || true
echo "✅ 配置已备份到: $BACKUP_DIR"
echo ""

# 2. 为每个域名生成配置
echo "2. 生成 Nginx 配置..."
echo "----------------------------------------"

for DOMAIN in "${!DOMAIN_MAPPING[@]}"; do
  PORT="${DOMAIN_MAPPING[$DOMAIN]}"
  DIR="${DIR_MAPPING[$DOMAIN]}"
  CONFIG_FILE="$SITES_AVAILABLE/$DOMAIN"
  
  echo "处理域名: $DOMAIN -> 端口 $PORT ($DIR)"
  
  # 检查 SSL 证书是否存在
  SSL_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
  SSL_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
  HAS_SSL=false
  
  if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
    HAS_SSL=true
    echo "  ✅ 发现 SSL 证书"
  else
    echo "  ⚠️  SSL 证书不存在"
  fi
  
  # 生成 Nginx 配置
  if [ "$HAS_SSL" = true ]; then
    # 有证书：生成 HTTP + HTTPS 配置
    sudo tee "$CONFIG_FILE" > /dev/null << NGINX_EOF
# HTTP -> HTTPS 重定向
server {
    listen 80;
    server_name $DOMAIN;
    
    # 重定向到 HTTPS
    return 301 https://\$server_name\$request_uri;
}

# HTTPS 服务器
server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL 证书
    ssl_certificate $SSL_CERT;
    ssl_certificate_key $SSL_KEY;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 日志
    access_log /var/log/nginx/${DOMAIN}-access.log;
    error_log /var/log/nginx/${DOMAIN}-error.log;
    
    # 禁止缓存 HTML
    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # 禁止缓存 HTML
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
        expires off;
    }
}
NGINX_EOF
  else
    # 无证书：只生成 HTTP 配置
    if [ "$DOMAIN" = "aizkw.usdt2026.cc" ]; then
      # aizkw 特殊处理：先生成 HTTP，然后申请证书
      echo "  📝 为 aizkw 生成 HTTP 配置（稍后将申请证书）"
    fi
    
    sudo tee "$CONFIG_FILE" > /dev/null << NGINX_EOF
# HTTP 服务器
server {
    listen 80;
    server_name $DOMAIN;
    
    # 日志
    access_log /var/log/nginx/${DOMAIN}-access.log;
    error_log /var/log/nginx/${DOMAIN}-error.log;
    
    # 禁止缓存 HTML
    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # 禁止缓存 HTML
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
        expires off;
    }
}
NGINX_EOF
  fi
  
  echo "  ✅ 配置已生成: $CONFIG_FILE"
  echo ""
done

# 3. 为 aizkw 申请 SSL 证书（如果不存在）
echo "3. 处理 aizkw SSL 证书..."
echo "----------------------------------------"
AIZKW_DOMAIN="aizkw.usdt2026.cc"
AIZKW_SSL_CERT="/etc/letsencrypt/live/$AIZKW_DOMAIN/fullchain.pem"
AIZKW_SSL_KEY="/etc/letsencrypt/live/$AIZKW_DOMAIN/privkey.pem"

if [ ! -f "$AIZKW_SSL_CERT" ] || [ ! -f "$AIZKW_SSL_KEY" ]; then
  echo "aizkw SSL 证书不存在，开始申请..."
  
  # 先启用 HTTP 配置
  sudo ln -sf "$SITES_AVAILABLE/$AIZKW_DOMAIN" "$SITES_ENABLED/$AIZKW_DOMAIN"
  
  # 测试并重载 Nginx（确保 HTTP 配置生效）
  if sudo nginx -t 2>&1; then
    sudo systemctl reload nginx
    echo "✅ Nginx 已重载（HTTP 配置）"
  else
    echo "❌ Nginx 配置测试失败"
    exit 1
  fi
  
  # 等待 Nginx 完全启动
  sleep 3
  
  # 检查 certbot 是否安装
  if ! command -v certbot &> /dev/null; then
    echo "安装 certbot..."
    sudo apt-get update -qq
    sudo apt-get install -y certbot python3-certbot-nginx
  fi
  
  # 申请证书
  echo "申请 SSL 证书..."
  if sudo certbot --nginx -d "$AIZKW_DOMAIN" --non-interactive --agree-tos -m admin@usdt2026.cc --redirect 2>&1; then
    echo "✅ SSL 证书申请成功"
    
    # 验证证书文件
    if [ -f "$AIZKW_SSL_CERT" ] && [ -f "$AIZKW_SSL_KEY" ]; then
      echo "✅ 证书文件已创建"
      
      # 重新生成包含 HTTPS 的配置
      sudo tee "$SITES_AVAILABLE/$AIZKW_DOMAIN" > /dev/null << NGINX_EOF
# HTTP -> HTTPS 重定向
server {
    listen 80;
    server_name $AIZKW_DOMAIN;
    
    # 重定向到 HTTPS
    return 301 https://\$server_name\$request_uri;
}

# HTTPS 服务器
server {
    listen 443 ssl http2;
    server_name $AIZKW_DOMAIN;
    
    # SSL 证书
    ssl_certificate $AIZKW_SSL_CERT;
    ssl_certificate_key $AIZKW_SSL_KEY;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 日志
    access_log /var/log/nginx/${AIZKW_DOMAIN}-access.log;
    error_log /var/log/nginx/${AIZKW_DOMAIN}-error.log;
    
    # 禁止缓存 HTML
    location / {
        proxy_pass http://127.0.0.1:3003;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # 禁止缓存 HTML
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
        expires off;
    }
}
NGINX_EOF
    else
      echo "⚠️  证书文件未找到，但 certbot 显示成功，继续..."
    fi
  else
    echo "⚠️  SSL 证书申请失败，使用 HTTP 配置继续"
  fi
else
  echo "✅ aizkw SSL 证书已存在，跳过申请"
fi
echo ""

# 4. 启用所有配置
echo "4. 启用所有配置..."
echo "----------------------------------------"
for DOMAIN in "${!DOMAIN_MAPPING[@]}"; do
  CONFIG_FILE="$SITES_AVAILABLE/$DOMAIN"
  ENABLED_LINK="$SITES_ENABLED/$DOMAIN"
  
  if [ -f "$CONFIG_FILE" ]; then
    # 删除旧链接（如果存在）
    sudo rm -f "$ENABLED_LINK"
    
    # 创建新链接
    sudo ln -sf "$CONFIG_FILE" "$ENABLED_LINK"
    
    if [ -L "$ENABLED_LINK" ]; then
      echo "✅ $DOMAIN 已启用"
    else
      echo "❌ $DOMAIN 启用失败"
    fi
  else
    echo "❌ 配置文件不存在: $CONFIG_FILE"
  fi
done
echo ""

# 5. 删除 default 配置
echo "5. 删除 default 配置..."
echo "----------------------------------------"
if [ -f "$SITES_ENABLED/default" ] || [ -L "$SITES_ENABLED/default" ]; then
  sudo rm -f "$SITES_ENABLED/default"
  echo "✅ default 配置已删除"
else
  echo "✅ default 配置不存在"
fi
echo ""

# 6. 测试 Nginx 配置
echo "6. 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
  echo "✅ Nginx 配置语法正确"
else
  echo "❌ Nginx 配置有错误"
  echo "恢复备份配置..."
  sudo cp -r "$BACKUP_DIR"/* "$SITES_AVAILABLE/" 2>/dev/null || true
  exit 1
fi
echo ""

# 7. 重启 Nginx
echo "7. 重启 Nginx..."
echo "----------------------------------------"
if sudo systemctl restart nginx; then
  echo "✅ Nginx 已重启"
  
  # 等待 Nginx 启动
  sleep 3
  
  # 检查 Nginx 状态
  if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 正在运行"
  else
    echo "❌ Nginx 启动失败"
    sudo systemctl status nginx --no-pager | head -15
    exit 1
  fi
else
  echo "❌ Nginx 重启失败"
  sudo systemctl status nginx --no-pager | head -15
  exit 1
fi
echo ""

# 8. 最终验证
echo "8. 最终验证..."
echo "----------------------------------------"

echo "域名 -> 端口映射关系："
echo "----------------------------------------"
for DOMAIN in "${!DOMAIN_MAPPING[@]}"; do
  PORT="${DOMAIN_MAPPING[$DOMAIN]}"
  DIR="${DIR_MAPPING[$DOMAIN]}"
  
  # 检查配置中的 proxy_pass
  CONFIG_FILE="$SITES_AVAILABLE/$DOMAIN"
  PROXY_PASS=$(grep "proxy_pass" "$CONFIG_FILE" | head -1 | grep -oE "127.0.0.1:[0-9]+" || echo "未找到")
  
  # 检查端口是否监听
  if ss -tlnp 2>/dev/null | grep -q ":$PORT " || netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
    PORT_STATUS="✅ 监听中"
  else
    PORT_STATUS="❌ 未监听"
  fi
  
  # 检查 SSL 证书
  SSL_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
  if [ -f "$SSL_CERT" ]; then
    SSL_STATUS="✅ 有证书"
  else
    SSL_STATUS="⚠️  无证书"
  fi
  
  printf "  %-25s -> 端口 %-4s (%s) | %s | %s\n" "$DOMAIN" "$PORT" "$DIR" "$PORT_STATUS" "$SSL_STATUS"
  echo "    proxy_pass: $PROXY_PASS"
done
echo ""

# 检查 Nginx 监听端口
echo "Nginx 监听端口："
if command -v ss >/dev/null 2>&1; then
  sudo ss -tlnp | grep nginx | grep -E ":80|:443" || echo "⚠️  未找到 Nginx 监听端口"
elif command -v netstat >/dev/null 2>&1; then
  sudo netstat -tlnp | grep nginx | grep -E ":80|:443" || echo "⚠️  未找到 Nginx 监听端口"
fi
echo ""

# 测试 HTTP 响应
echo "测试 HTTP 响应..."
for DOMAIN in "${!DOMAIN_MAPPING[@]}"; do
  PORT="${DOMAIN_MAPPING[$DOMAIN]}"
  
  # 测试本地端口
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:$PORT 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    echo "  ✅ 端口 $PORT ($DOMAIN) HTTP 响应正常 (HTTP $HTTP_CODE)"
  else
    echo "  ⚠️  端口 $PORT ($DOMAIN) HTTP 响应异常 (HTTP $HTTP_CODE)"
  fi
done
echo ""

echo "=========================================="
echo "✅ 最终 Nginx 映射配置完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "配置摘要："
echo "  - aikz.usdt2026.cc  -> 端口 3000 (saas-demo)"
echo "  - tgmini.usdt2026.cc -> 端口 3001 (tgmini20251220)"
echo "  - hongbao.usdt2026.cc -> 端口 3002 (hbwy20251220)"
echo "  - aizkw.usdt2026.cc  -> 端口 3003 (aizkw20251219)"
echo ""
echo "备份位置: $BACKUP_DIR"
echo ""
echo "如果仍有问题，请检查："
echo "  sudo nginx -T"
echo "  sudo tail -50 /var/log/nginx/error.log"
echo "  pm2 list"
