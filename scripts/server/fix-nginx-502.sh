#!/bin/bash
# ============================================================
# 修复 Nginx 502 Bad Gateway 错误
# ============================================================

set +e  # 不在第一个错误时退出

echo "=========================================="
echo "🔧 修复 Nginx 502 Bad Gateway"
echo "=========================================="
echo ""

# Step 1: 检查后端服务
echo "[1/6] 检查后端服务..."
if curl -s --max-time 5 http://localhost:8000/health >/dev/null 2>&1; then
  echo "  ✅ 后端服务正常运行 (http://localhost:8000)"
else
  echo "  ❌ 后端服务未响应"
  echo "  请先修复后端服务: bash scripts/server/quick-fix-502.sh"
  exit 1
fi

# Step 2: 检查 Nginx 配置
echo ""
echo "[2/6] 检查 Nginx 配置..."
if sudo nginx -t 2>&1 | grep -q "syntax is ok"; then
  echo "  ✅ Nginx 配置语法正确"
else
  echo "  ❌ Nginx 配置有错误:"
  sudo nginx -t
  exit 1
fi

# Step 3: 检查 Nginx upstream 配置
echo ""
echo "[3/6] 检查 Nginx upstream 配置..."
NGINX_CONFIG="/etc/nginx/sites-available/default"
if [ -f "$NGINX_CONFIG" ]; then
  echo "  检查配置文件: $NGINX_CONFIG"
  
  # 检查是否有 upstream 配置
  if grep -q "upstream.*backend" "$NGINX_CONFIG" || grep -q "proxy_pass.*8000" "$NGINX_CONFIG"; then
    echo "  ✅ 找到后端代理配置"
  else
    echo "  ⚠️  未找到后端代理配置，可能需要添加"
  fi
  
  # 显示相关配置
  echo ""
  echo "  相关配置片段:"
  grep -A 5 "proxy_pass\|upstream" "$NGINX_CONFIG" | head -20 || echo "  未找到 proxy_pass 配置"
else
  echo "  ⚠️  配置文件不存在: $NGINX_CONFIG"
fi

# Step 4: 检查 Nginx 错误日志
echo ""
echo "[4/6] 检查 Nginx 错误日志..."
if [ -f "/var/log/nginx/error.log" ]; then
  echo "  最近的错误:"
  sudo tail -20 /var/log/nginx/error.log | grep -i "502\|bad gateway\|upstream\|connect" || echo "  未找到相关错误"
else
  echo "  ⚠️  错误日志文件不存在"
fi

# Step 5: 测试 Nginx 到后端的连接
echo ""
echo "[5/6] 测试 Nginx 到后端的连接..."
# 检查 Nginx 进程的用户
NGINX_USER=$(ps aux | grep nginx | grep -v grep | head -1 | awk '{print $1}' || echo "www-data")
echo "  Nginx 运行用户: $NGINX_USER"

# 测试连接
if sudo -u "$NGINX_USER" curl -s --max-time 5 http://localhost:8000/health >/dev/null 2>&1; then
  echo "  ✅ Nginx 用户可以连接到后端"
else
  echo "  ❌ Nginx 用户无法连接到后端"
  echo "  尝试使用 www-data 用户测试..."
  if sudo -u www-data curl -s --max-time 5 http://localhost:8000/health >/dev/null 2>&1; then
    echo "  ✅ www-data 用户可以连接到后端"
  else
    echo "  ❌ www-data 用户也无法连接"
  fi
fi

# Step 6: 重启 Nginx
echo ""
echo "[6/6] 重启 Nginx..."
sudo systemctl reload nginx 2>/dev/null || sudo systemctl restart nginx

if systemctl is-active nginx >/dev/null 2>&1; then
  echo "  ✅ Nginx 已重启"
else
  echo "  ❌ Nginx 重启失败"
  echo "  查看日志: sudo journalctl -u nginx -n 50 --no-pager"
  exit 1
fi

echo ""
echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果仍有 502 错误，请检查："
echo "  1. Nginx 配置中的 upstream 地址是否正确"
echo "  2. Nginx 配置: sudo cat /etc/nginx/sites-available/default | grep -A 10 proxy_pass"
echo "  3. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo "  4. 后端服务日志: sudo journalctl -u luckyred-api -n 50 --no-pager"
echo ""
echo "测试访问:"
echo "  curl -I http://localhost"
echo "  curl -I https://aikz.usdt2026.cc"
echo ""

