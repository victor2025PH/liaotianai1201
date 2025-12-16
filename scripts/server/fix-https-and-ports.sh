#!/bin/bash
# 修复 HTTPS 和端口监听问题

echo "=========================================="
echo "修复 HTTPS 和端口监听问题"
echo "=========================================="
echo ""

# 1. 检查当前配置
echo "[1/6] 检查当前 Nginx 配置..."
echo "----------------------------------------"
NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
if [ -f "$NGINX_CONFIG" ]; then
  echo "✅ 配置文件存在"
  echo "当前监听端口:"
  sudo grep -E "^\s*listen" "$NGINX_CONFIG" | head -5
else
  echo "❌ 配置文件不存在"
  exit 1
fi
echo ""

# 2. 检查 SSL 证书
echo "[2/6] 检查 SSL 证书..."
echo "----------------------------------------"
if [ -d "/etc/letsencrypt/live/aikz.usdt2026.cc" ]; then
  echo "✅ SSL 证书存在"
  sudo ls -la /etc/letsencrypt/live/aikz.usdt2026.cc/
else
  echo "⚠️  SSL 证书不存在"
  echo "需要安装 SSL 证书才能启用 HTTPS"
fi
echo ""

# 3. 检查后端服务
echo "[3/6] 检查后端服务端口 8000..."
echo "----------------------------------------"
if sudo ss -tlnp | grep -q :8000; then
  echo "✅ 端口 8000 正在监听"
else
  echo "⚠️  端口 8000 未监听，检查后端服务..."
  if sudo systemctl is-active --quiet luckyred-api; then
    echo "  后端服务显示为运行中，但端口未监听"
    echo "  查看后端日志:"
    sudo journalctl -u luckyred-api -n 20 --no-pager | tail -10
  else
    echo "  ❌ 后端服务未运行，尝试重启..."
    sudo systemctl restart luckyred-api
    sleep 5
    if sudo ss -tlnp | grep -q :8000; then
      echo "  ✅ 后端服务已启动，端口 8000 现在正在监听"
    else
      echo "  ❌ 后端服务仍然无法监听端口 8000"
      echo "  请查看详细日志: sudo journalctl -u luckyred-api -n 50 --no-pager"
    fi
  fi
fi
echo ""

# 4. 如果证书存在，尝试配置 HTTPS
echo "[4/6] 检查 HTTPS 配置..."
echo "----------------------------------------"
if [ -d "/etc/letsencrypt/live/aikz.usdt2026.cc" ]; then
  if sudo grep -q "listen 443 ssl" "$NGINX_CONFIG" 2>/dev/null; then
    echo "✅ HTTPS 配置已存在"
  else
    echo "⚠️  Nginx 配置中缺少 HTTPS (443) 监听"
    echo "尝试使用 Certbot 自动配置..."
    if command -v certbot &> /dev/null; then
      echo "  执行: sudo certbot --nginx -d aikz.usdt2026.cc --non-interactive --agree-tos --email admin@aikz.usdt2026.cc || true"
      sudo certbot --nginx -d aikz.usdt2026.cc --non-interactive --agree-tos --email admin@aikz.usdt2026.cc 2>&1 | tail -10 || true
    else
      echo "  ❌ Certbot 未安装"
      echo "  安装命令: sudo apt-get install -y certbot python3-certbot-nginx"
    fi
  fi
else
  echo "⚠️  无 SSL 证书，无法配置 HTTPS"
  echo "  安装证书命令: sudo certbot --nginx -d aikz.usdt2026.cc"
fi
echo ""

# 5. 测试 Nginx 配置
echo "[5/6] 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t; then
  echo "✅ Nginx 配置语法正确"
  echo "重新加载 Nginx..."
  sudo systemctl reload nginx || sudo systemctl restart nginx
else
  echo "❌ Nginx 配置有错误，请检查配置文件"
  exit 1
fi
echo ""

# 6. 最终检查
echo "[6/6] 最终端口检查..."
echo "----------------------------------------"
sleep 3
echo "监听端口状态:"
echo "  端口 80 (HTTP):"
sudo ss -tlnp | grep :80 | head -1 || echo "    ❌ 未监听"
echo "  端口 443 (HTTPS):"
sudo ss -tlnp | grep :443 | head -1 || echo "    ⚠️  未监听（如果证书不存在是正常的）"
echo "  端口 3000 (前端):"
sudo ss -tlnp | grep :3000 | head -1 || echo "    ❌ 未监听"
echo "  端口 8000 (后端):"
sudo ss -tlnp | grep :8000 | head -1 || echo "    ❌ 未监听"
echo ""

echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "如果 443 端口仍然未监听："
echo "1. 检查是否有 SSL 证书: sudo ls -la /etc/letsencrypt/live/aikz.usdt2026.cc/"
echo "2. 如果没有证书，先安装: sudo certbot --nginx -d aikz.usdt2026.cc"
echo "3. 或者临时使用 HTTP 访问: http://aikz.usdt2026.cc (不是 https)"
echo ""
echo "如果端口 8000 未监听，检查后端服务："
echo "  sudo journalctl -u luckyred-api -n 50 --no-pager"
