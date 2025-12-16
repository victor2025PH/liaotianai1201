#!/bin/bash
# 检查 Nginx 端口监听问题

echo "=========================================="
echo "Nginx 端口监听诊断"
echo "=========================================="
echo ""

# 1. 检查 Nginx 配置
echo "[1/5] 检查 Nginx 配置文件..."
echo "----------------------------------------"
if [ -f "/etc/nginx/sites-available/aikz.usdt2026.cc" ]; then
  echo "✅ 找到站点配置: /etc/nginx/sites-available/aikz.usdt2026.cc"
  echo "监听端口配置:"
  sudo grep -E "listen\s+(443|80)" /etc/nginx/sites-available/aikz.usdt2026.cc | head -5
else
  echo "⚠️  未找到站点配置文件"
  echo "可用配置文件:"
  ls -la /etc/nginx/sites-available/ 2>/dev/null | head -10
fi
echo ""

# 2. 检查 Nginx 是否启用 HTTPS 站点
echo "[2/5] 检查启用的站点..."
echo "----------------------------------------"
if [ -L "/etc/nginx/sites-enabled/aikz.usdt2026.cc" ]; then
  echo "✅ 站点已启用"
  ls -la /etc/nginx/sites-enabled/aikz.usdt2026.cc
else
  echo "❌ 站点未启用"
  echo "请执行: sudo ln -s /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-enabled/"
fi
echo ""

# 3. 检查 Nginx 配置语法
echo "[3/5] 检查 Nginx 配置语法..."
echo "----------------------------------------"
sudo nginx -t
echo ""

# 4. 检查所有监听端口
echo "[4/5] 检查所有监听端口（完整输出）..."
echo "----------------------------------------"
echo "所有 TCP 监听端口:"
sudo ss -tlnp | grep LISTEN
echo ""

echo "Nginx 进程:"
ps aux | grep nginx | grep -v grep
echo ""

# 5. 检查后端端口
echo "[5/5] 检查后端服务端口..."
echo "----------------------------------------"
echo "端口 8000 监听情况:"
sudo ss -tlnp | grep :8000 || echo "  ❌ 端口 8000 未监听"
echo ""

echo "后端进程:"
ps aux | grep uvicorn | grep -v grep
echo ""

# 6. 检查防火墙
echo "[6/6] 检查防火墙规则..."
echo "----------------------------------------"
if command -v ufw &> /dev/null; then
  echo "UFW 状态:"
  sudo ufw status
elif command -v firewall-cmd &> /dev/null; then
  echo "Firewalld 状态:"
  sudo firewall-cmd --list-ports
else
  echo "未检测到常见的防火墙工具"
fi
echo ""

echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "如果 Nginx 未监听 443 端口，请检查："
echo "1. Nginx 配置文件中是否有 'listen 443 ssl;'"
echo "2. SSL 证书文件是否存在"
echo "3. 站点配置是否已启用（symlink）"
echo "4. 执行: sudo nginx -t && sudo systemctl reload nginx"
