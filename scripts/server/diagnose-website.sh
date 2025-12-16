#!/bin/bash
# 网站无法访问诊断脚本

echo "=========================================="
echo "网站访问问题诊断"
echo "=========================================="
echo ""

# 1. 检查服务状态
echo "[1/6] 检查服务状态..."
echo "----------------------------------------"
echo "前端服务 (liaotian-frontend):"
sudo systemctl status liaotian-frontend --no-pager | head -5
echo ""

echo "后端服务 (luckyred-api):"
sudo systemctl status luckyred-api --no-pager | head -5
echo ""

echo "Nginx 服务:"
sudo systemctl status nginx --no-pager | head -5
echo ""

# 2. 检查端口监听
echo "[2/6] 检查端口监听..."
echo "----------------------------------------"
echo "端口 3000 (前端):"
sudo ss -tlnp | grep :3000 || echo "  ❌ 端口 3000 未被监听"
echo ""

echo "端口 8000 (后端):"
sudo ss -tlnp | grep :8000 || echo "  ❌ 端口 8000 未被监听"
echo ""

echo "端口 443 (HTTPS):"
sudo ss -tlnp | grep :443 || echo "  ❌ 端口 443 未被监听"
echo ""

# 3. 检查前端构建文件
echo "[3/6] 检查前端构建文件..."
echo "----------------------------------------"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_DIR" 2>/dev/null || {
  echo "  ❌ 无法进入项目目录: $PROJECT_DIR"
  exit 1
}

if [ -f "saas-demo/.next/standalone/server.js" ]; then
  echo "  ✅ 找到 .next/standalone/server.js"
elif [ -f "saas-demo/.next/standalone/saas-demo/server.js" ]; then
  echo "  ✅ 找到 .next/standalone/saas-demo/server.js"
else
  SERVER_JS=$(find saas-demo/.next -name "server.js" -type f 2>/dev/null | head -1)
  if [ -n "$SERVER_JS" ]; then
    echo "  ✅ 找到 server.js: $SERVER_JS"
  else
    echo "  ❌ 未找到 server.js 文件"
    echo "  检查 .next 目录:"
    ls -la saas-demo/.next 2>/dev/null | head -5 || echo "    .next 目录不存在"
  fi
fi
echo ""

# 4. 检查前端服务日志
echo "[4/6] 检查前端服务日志（最近 20 行）..."
echo "----------------------------------------"
sudo journalctl -u liaotian-frontend -n 20 --no-pager
echo ""

# 5. 检查后端服务日志
echo "[5/6] 检查后端服务日志（最近 10 行）..."
echo "----------------------------------------"
sudo journalctl -u luckyred-api -n 10 --no-pager
echo ""

# 6. 检查 Nginx 错误日志
echo "[6/6] 检查 Nginx 错误日志（最近 10 行）..."
echo "----------------------------------------"
sudo tail -10 /var/log/nginx/error.log 2>/dev/null || echo "  无法读取 Nginx 错误日志"
echo ""

echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "如果服务未运行，请执行："
echo "  sudo systemctl start liaotian-frontend"
echo "  sudo systemctl start luckyred-api"
echo "  sudo systemctl start nginx"
echo ""
echo "如果服务启动失败，查看详细日志："
echo "  sudo journalctl -u liaotian-frontend -n 50 --no-pager"
echo "  sudo journalctl -u luckyred-api -n 50 --no-pager"
