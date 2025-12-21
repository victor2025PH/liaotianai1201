#!/bin/bash

echo "=========================================="
echo "🔍 Nginx 诊断脚本"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 1. 检查 Nginx 服务状态
echo "1️⃣ 检查 Nginx 服务状态..."
echo "----------------------------------------"
if sudo systemctl is-active --quiet nginx; then
  echo "✅ Nginx 服务正在运行"
  sudo systemctl status nginx --no-pager -l | head -10
else
  echo "❌ Nginx 服务未运行"
  sudo systemctl status nginx --no-pager -l | head -10
fi
echo ""

# 2. 检查端口监听
echo "2️⃣ 检查端口监听..."
echo "----------------------------------------"
echo "端口 80:"
sudo netstat -tlnp 2>/dev/null | grep ":80 " || sudo ss -tlnp 2>/dev/null | grep ":80 " || echo "  未监听"
echo ""
echo "端口 443:"
sudo netstat -tlnp 2>/dev/null | grep ":443 " || sudo ss -tlnp 2>/dev/null | grep ":443 " || echo "  未监听"
echo ""

# 3. 检查前端服务端口
echo "3️⃣ 检查前端服务端口..."
echo "----------------------------------------"
for port in 3001 3002 3003; do
  echo "端口 $port:"
  sudo netstat -tlnp 2>/dev/null | grep ":$port " || sudo ss -tlnp 2>/dev/null | grep ":$port " || echo "  未监听"
done
echo ""

# 4. 检查 PM2 进程
echo "4️⃣ 检查 PM2 进程..."
echo "----------------------------------------"
if command -v pm2 >/dev/null 2>&1; then
  pm2 list
else
  echo "⚠️  PM2 未安装"
fi
echo ""

# 5. 检查 SSL 证书
echo "5️⃣ 检查 SSL 证书..."
echo "----------------------------------------"
DOMAINS=("hongbao.usdt2026.cc" "tgmini.usdt2026.cc" "aikz.usdt2026.cc" "aizkw.usdt2026.cc")
for domain in "${DOMAINS[@]}"; do
  echo "域名: $domain"
  # 标准路径
  CERT_STD="/etc/letsencrypt/live/$domain/fullchain.pem"
  if sudo test -f "$CERT_STD"; then
    echo "  ✅ 证书存在（标准路径）: $CERT_STD"
    sudo ls -lh "$CERT_STD" 2>/dev/null | awk '{print "    大小: " $5 " 修改时间: " $6 " " $7 " " $8}'
  else
    # 查找带后缀的证书
    MATCHING=$(sudo find /etc/letsencrypt/live/ -name "${domain}*" -type d 2>/dev/null | head -1)
    if [ -n "$MATCHING" ]; then
      CERT_PATH="$MATCHING/fullchain.pem"
      if sudo test -f "$CERT_PATH"; then
        echo "  ✅ 证书存在（带后缀）: $CERT_PATH"
        sudo ls -lh "$CERT_PATH" 2>/dev/null | awk '{print "    大小: " $5 " 修改时间: " $6 " " $7 " " $8}'
      else
        echo "  ❌ 证书不存在"
      fi
    else
      echo "  ❌ 证书不存在"
    fi
  fi
  echo ""
done

# 6. 检查 Nginx 配置
echo "6️⃣ 检查 Nginx 配置..."
echo "----------------------------------------"
echo "已启用的配置:"
ls -la /etc/nginx/sites-enabled/ 2>/dev/null || echo "  sites-enabled 目录不存在或无法访问"
echo ""
echo "可用的配置:"
ls -la /etc/nginx/sites-available/ 2>/dev/null | grep -E "(hongbao|tgmini|aikz|aizkw)" || echo "  未找到相关配置"
echo ""

# 7. 测试 Nginx 配置
echo "7️⃣ 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
  echo "✅ Nginx 配置测试通过"
else
  echo "❌ Nginx 配置测试失败"
  sudo nginx -t 2>&1 || true
fi
echo ""

# 8. 检查 Nginx 错误日志
echo "8️⃣ 检查 Nginx 错误日志（最后 20 行）..."
echo "----------------------------------------"
if sudo test -f /var/log/nginx/error.log; then
  sudo tail -20 /var/log/nginx/error.log
else
  echo "⚠️  错误日志文件不存在"
fi
echo ""

# 9. 检查前端服务目录
echo "9️⃣ 检查前端服务目录..."
echo "----------------------------------------"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
SITES=(
  "tgmini20251220:3001"
  "hbwy20251220:3002"
  "aizkw20251219:3003"
)
for site_info in "${SITES[@]}"; do
  IFS=':' read -r dir port <<< "$site_info"
  SITE_DIR="$PROJECT_DIR/$dir"
  echo "目录: $SITE_DIR (端口 $port)"
  if [ -d "$SITE_DIR" ]; then
    echo "  ✅ 目录存在"
    if [ -d "$SITE_DIR/dist" ]; then
      echo "  ✅ dist 目录存在"
      echo "    大小: $(du -sh "$SITE_DIR/dist" 2>/dev/null | cut -f1 || echo '未知')"
    else
      echo "  ❌ dist 目录不存在"
    fi
  else
    echo "  ❌ 目录不存在"
  fi
  echo ""
done

echo "=========================================="
echo "✅ 诊断完成"
echo "时间: $(date)"
echo "=========================================="
