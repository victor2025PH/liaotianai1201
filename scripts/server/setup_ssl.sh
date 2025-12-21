#!/bin/bash

set -e

echo "=========================================="
echo "🔐 SSL 证书申请脚本"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 配置
EMAIL="${SSL_EMAIL:-admin@usdt2026.cc}"  # 默认邮箱，可通过环境变量 SSL_EMAIL 覆盖
DOMAINS=(
  "hongbao.usdt2026.cc"
  "tgmini.usdt2026.cc"
  "aikz.usdt2026.cc"
)

echo "📧 Let's Encrypt 邮箱: $EMAIL"
echo "🌐 需要申请证书的域名:"
for domain in "${DOMAINS[@]}"; do
  echo "  - $domain"
done
echo ""

# 1. 检查并安装 Certbot
echo "1️⃣ 检查并安装 Certbot..."
echo "----------------------------------------"

if ! command -v certbot >/dev/null 2>&1; then
  echo "⚠️  Certbot 未安装，正在安装..."
  sudo apt-get update -qq
  sudo apt-get install -y certbot python3-certbot-nginx || {
    echo "❌ Certbot 安装失败"
    exit 1
  }
  echo "✅ Certbot 安装完成"
else
  echo "✅ Certbot 已安装: $(certbot --version 2>&1 | head -1)"
fi
echo ""

# 2. 检查 Nginx 状态（决定使用哪种模式）
echo "2️⃣ 检查 Nginx 状态..."
echo "----------------------------------------"

NGINX_RUNNING=false
if sudo systemctl is-active --quiet nginx 2>/dev/null; then
  NGINX_RUNNING=true
  echo "✅ Nginx 正在运行，将使用 --nginx 模式（自动配置）"
else
  echo "⚠️  Nginx 未运行，将使用 --standalone 模式（需要临时占用 80/443 端口）"
fi
echo ""

# 3. 为每个域名申请证书
echo "3️⃣ 开始申请 SSL 证书..."
echo "----------------------------------------"

SUCCESS_COUNT=0
FAILED_DOMAINS=()

for domain in "${DOMAINS[@]}"; do
  echo ""
  echo "📋 处理域名: $domain"
  echo "----------------------------------------"
  
  # 检查证书是否已存在
  CERT_PATH="/etc/letsencrypt/live/$domain/fullchain.pem"
  if [ -f "$CERT_PATH" ]; then
    echo "✅ 证书已存在: $CERT_PATH"
    echo "证书信息:"
    sudo openssl x509 -in "$CERT_PATH" -noout -subject -dates 2>/dev/null || true
    echo ""
    continue
  fi
  
  # 申请证书
  echo "申请证书中..."
  
  if [ "$NGINX_RUNNING" = "true" ]; then
    # Nginx 正在运行，使用 --nginx 模式（自动配置）
    echo "使用 --nginx 模式（自动配置 Nginx）..."
    if sudo certbot certonly --nginx \
      --non-interactive \
      --agree-tos \
      --email "$EMAIL" \
      -d "$domain" \
      --preferred-challenges http \
      --redirect; then
      echo "✅ $domain 证书申请成功！"
      SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
      echo "❌ $domain 证书申请失败"
      FAILED_DOMAINS+=("$domain")
    fi
  else
    # Nginx 未运行，使用 --standalone 模式
    echo "使用 --standalone 模式（需要临时占用 80/443 端口）..."
    echo "⚠️  确保端口 80 和 443 未被其他服务占用..."
    
    # 检查端口占用
    if sudo lsof -i :80 >/dev/null 2>&1 || sudo lsof -i :443 >/dev/null 2>&1; then
      echo "⚠️  警告: 端口 80 或 443 被占用，尝试停止占用进程..."
      sudo lsof -ti :80 | xargs sudo kill -9 2>/dev/null || true
      sudo lsof -ti :443 | xargs sudo kill -9 2>/dev/null || true
      sleep 2
    fi
    
    if sudo certbot certonly --standalone \
      --non-interactive \
      --agree-tos \
      --email "$EMAIL" \
      -d "$domain" \
      --preferred-challenges http; then
      echo "✅ $domain 证书申请成功！"
      SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
      echo "❌ $domain 证书申请失败"
      FAILED_DOMAINS+=("$domain")
    fi
  fi
done

echo ""
echo "=========================================="
echo "📊 申请结果汇总"
echo "=========================================="
echo "成功: $SUCCESS_COUNT / ${#DOMAINS[@]}"
if [ ${#FAILED_DOMAINS[@]} -gt 0 ]; then
  echo "失败: ${#FAILED_DOMAINS[@]}"
  echo "失败的域名:"
  for domain in "${FAILED_DOMAINS[@]}"; do
    echo "  - $domain"
  done
fi
echo ""

# 4. 验证证书
echo "4️⃣ 验证证书..."
echo "----------------------------------------"
for domain in "${DOMAINS[@]}"; do
  CERT_PATH="/etc/letsencrypt/live/$domain/fullchain.pem"
  if [ -f "$CERT_PATH" ]; then
    echo "✅ $domain: 证书存在"
    echo "   路径: $CERT_PATH"
    echo "   有效期:"
    sudo openssl x509 -in "$CERT_PATH" -noout -dates 2>/dev/null | sed 's/^/   /' || true
  else
    echo "❌ $domain: 证书不存在"
  fi
done
echo ""

# 5. 重启 Nginx（如果正在运行）
if [ "$NGINX_RUNNING" = "true" ] || sudo systemctl is-active --quiet nginx 2>/dev/null; then
  echo "5️⃣ 重启 Nginx..."
  echo "----------------------------------------"
  
  # 测试配置
  if sudo nginx -t 2>&1; then
    echo "✅ Nginx 配置测试通过"
    if sudo systemctl restart nginx 2>&1; then
      echo "✅ Nginx 重启成功"
      sleep 2
      if sudo systemctl is-active --quiet nginx; then
        echo "✅ Nginx 服务正常运行中"
      else
        echo "⚠️  Nginx 重启后状态异常"
        sudo systemctl status nginx --no-pager -l | head -20 || true
      fi
    else
      echo "❌ Nginx 重启失败"
      sudo systemctl status nginx --no-pager -l | head -20 || true
    fi
  else
    echo "❌ Nginx 配置测试失败，跳过重启"
    echo "错误信息:"
    sudo nginx -t 2>&1 || true
  fi
else
  echo "5️⃣ Nginx 未运行，跳过重启"
fi
echo ""

# 6. 设置自动续期
echo "6️⃣ 检查自动续期配置..."
echo "----------------------------------------"

# 检查是否已有续期定时任务
if sudo systemctl list-timers | grep -q "certbot.timer"; then
  echo "✅ Certbot 自动续期定时任务已存在"
  sudo systemctl status certbot.timer --no-pager -l | head -10 || true
else
  echo "⚠️  未找到 Certbot 定时任务，尝试启用..."
  sudo systemctl enable certbot.timer || true
  sudo systemctl start certbot.timer || true
  echo "✅ Certbot 自动续期已启用"
fi
echo ""

echo "=========================================="
echo "✅ SSL 证书申请完成！"
echo "时间: $(date)"
echo "=========================================="

if [ ${#FAILED_DOMAINS[@]} -gt 0 ]; then
  echo ""
  echo "⚠️  部分域名证书申请失败，请检查："
  echo "1. 域名 DNS 是否正确指向此服务器"
  echo "2. 端口 80 和 443 是否可访问"
  echo "3. 防火墙是否开放了这些端口"
  echo ""
  exit 1
fi
