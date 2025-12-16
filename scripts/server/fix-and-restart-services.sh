#!/bin/bash
# 快速修复并重启服务

echo "=========================================="
echo "快速修复并重启服务"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 1. 进入项目目录
cd "$PROJECT_DIR" || {
  echo "❌ 无法进入项目目录: $PROJECT_DIR"
  exit 1
}

# 2. 停止所有服务
echo "[1/5] 停止所有服务..."
sudo systemctl stop liaotian-frontend 2>/dev/null || true
sudo systemctl stop luckyred-api 2>/dev/null || true
sudo systemctl stop nginx 2>/dev/null || true
echo "✅ 服务已停止"
echo ""

# 3. 修复文件权限
echo "[2/5] 修复文件权限..."
sudo chown -R ubuntu:ubuntu "$PROJECT_DIR"
echo "✅ 文件权限已修复"
echo ""

# 4. 验证前端构建文件
echo "[3/5] 验证前端构建文件..."
if [ -f "saas-demo/.next/standalone/server.js" ] || [ -f "saas-demo/.next/standalone/saas-demo/server.js" ]; then
  echo "✅ 前端构建文件存在"
else
  SERVER_JS=$(find saas-demo/.next -name "server.js" -type f 2>/dev/null | head -1)
  if [ -n "$SERVER_JS" ]; then
    echo "✅ 找到 server.js: $SERVER_JS"
  else
    echo "⚠️  前端构建文件不存在，需要重新构建"
    echo "   执行: cd saas-demo && npm run build"
  fi
fi
echo ""

# 5. 重启服务
echo "[4/5] 重启服务..."
sudo systemctl restart luckyred-api
if [ $? -eq 0 ]; then
  echo "✅ luckyred-api 已重启"
else
  echo "❌ luckyred-api 重启失败"
fi

sudo systemctl restart liaotian-frontend
if [ $? -eq 0 ]; then
  echo "✅ liaotian-frontend 已重启"
else
  echo "❌ liaotian-frontend 重启失败"
  echo "   查看日志: sudo journalctl -u liaotian-frontend -n 50 --no-pager"
fi

sudo systemctl restart nginx
if [ $? -eq 0 ]; then
  echo "✅ nginx 已重启"
else
  echo "❌ nginx 重启失败"
fi
echo ""

# 6. 等待服务启动
echo "[5/5] 等待服务启动 (15秒)..."
sleep 15

# 7. 检查服务状态
echo ""
echo "=========================================="
echo "服务状态检查"
echo "=========================================="
echo ""

echo "前端服务状态:"
if sudo systemctl is-active --quiet liaotian-frontend; then
  echo "  ✅ liaotian-frontend 正在运行"
else
  echo "  ❌ liaotian-frontend 未运行"
  echo "  查看日志: sudo journalctl -u liaotian-frontend -n 30 --no-pager"
fi

echo ""
echo "后端服务状态:"
if sudo systemctl is-active --quiet luckyred-api; then
  echo "  ✅ luckyred-api 正在运行"
else
  echo "  ❌ luckyred-api 未运行"
  echo "  查看日志: sudo journalctl -u luckyred-api -n 30 --no-pager"
fi

echo ""
echo "Nginx 状态:"
if sudo systemctl is-active --quiet nginx; then
  echo "  ✅ nginx 正在运行"
else
  echo "  ❌ nginx 未运行"
fi

echo ""
echo "端口监听:"
if sudo ss -tlnp | grep -q :3000; then
  echo "  ✅ 端口 3000 正在监听"
else
  echo "  ❌ 端口 3000 未监听"
fi

if sudo ss -tlnp | grep -q :8000; then
  echo "  ✅ 端口 8000 正在监听"
else
  echo "  ❌ 端口 8000 未监听"
fi

if sudo ss -tlnp | grep -q :443; then
  echo "  ✅ 端口 443 正在监听"
else
  echo "  ❌ 端口 443 未监听"
fi

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
