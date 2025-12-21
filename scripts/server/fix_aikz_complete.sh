#!/bin/bash

# 完整修复 aikz.usdt2026.cc 问题
# 使用方法: sudo bash scripts/server/fix_aikz_complete.sh

set -e

echo "=========================================="
echo "🔧 完整修复 aikz.usdt2026.cc"
echo "时间: $(date)"
echo "=========================================="
echo ""

DOMAIN="aikz.usdt2026.cc"
SAAS_DEMO_DIR="/home/ubuntu/telegram-ai-system/saas-demo"
PORT=3000

# 1. 检查并停止可能冲突的服务
echo "1. 检查并停止可能冲突的服务..."
echo "----------------------------------------"

# 停止可能运行在端口 3000 的其他服务
if lsof -i :$PORT >/dev/null 2>&1; then
  echo "停止占用端口 $PORT 的进程..."
  sudo lsof -ti :$PORT | xargs sudo kill -9 2>/dev/null || true
  sleep 2
fi

# 停止 PM2 中的 saas-demo
pm2 delete saas-demo 2>/dev/null || true
echo "✅ 已清理旧进程"
echo ""

# 2. 确保 saas-demo 目录存在
echo "2. 检查 saas-demo 目录..."
echo "----------------------------------------"
if [ ! -d "$SAAS_DEMO_DIR" ]; then
  echo "❌ saas-demo 目录不存在: $SAAS_DEMO_DIR"
  exit 1
fi
echo "✅ saas-demo 目录存在"
echo ""

# 3. 进入 saas-demo 目录并安装依赖
echo "3. 安装依赖..."
echo "----------------------------------------"
cd "$SAAS_DEMO_DIR" || exit 1

if [ ! -f "package.json" ]; then
  echo "❌ package.json 不存在"
  exit 1
fi

if [ ! -d "node_modules" ]; then
  echo "安装依赖..."
  sudo -u ubuntu npm install || {
    echo "❌ 依赖安装失败"
    exit 1
  }
  echo "✅ 依赖安装完成"
else
  echo "✅ node_modules 已存在"
fi
echo ""

# 4. 构建 saas-demo
echo "4. 构建 saas-demo..."
echo "----------------------------------------"
if [ ! -d ".next" ]; then
  echo "构建项目..."
  sudo -u ubuntu npm run build || {
    echo "❌ 构建失败"
    exit 1
  }
  echo "✅ 构建完成"
else
  echo "✅ .next 目录已存在"
  echo "清理旧构建并重新构建..."
  rm -rf .next
  sudo -u ubuntu npm run build || {
    echo "❌ 构建失败"
    exit 1
  }
  echo "✅ 重新构建完成"
fi
echo ""

# 5. 启动 saas-demo
echo "5. 启动 saas-demo..."
echo "----------------------------------------"
mkdir -p "$SAAS_DEMO_DIR/logs"

# 使用 PM2 启动
pm2 start npm \
  --name saas-demo \
  -- start \
  --error "$SAAS_DEMO_DIR/logs/saas-demo-error.log" \
  --output "$SAAS_DEMO_DIR/logs/saas-demo-out.log" \
  --merge-logs \
  --log-date-format "YYYY-MM-DD HH:mm:ss Z" || {
  echo "⚠️  PM2 启动失败，查看错误..."
  pm2 logs saas-demo --lines 10 --nostream 2>/dev/null || true
  exit 1
}

pm2 save || true
echo "✅ saas-demo 已启动"
echo ""

# 6. 等待服务启动
echo "6. 等待服务启动..."
echo "----------------------------------------"
sleep 10

# 检查端口
if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
  echo "✅ 端口 $PORT 正在监听"
  
  # 测试本地访问
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    echo "✅ 本地访问正常 (HTTP $HTTP_CODE)"
    
    # 检查返回的内容
    CONTENT=$(curl -s http://127.0.0.1:$PORT 2>/dev/null | head -c 200)
    if echo "$CONTENT" | grep -qi "智控王\|Smart Control King"; then
      echo "❌ 返回的内容包含 'AI 智控王'，说明返回了错误的页面"
      echo "   这可能是构建问题，检查构建输出..."
      pm2 logs saas-demo --lines 30 --nostream 2>/dev/null || true
    else
      echo "✅ 返回的内容正确（不包含 'AI 智控王'）"
    fi
  else
    echo "⚠️  本地访问异常 (HTTP $HTTP_CODE)"
    pm2 logs saas-demo --lines 20 --nostream 2>/dev/null || true
  fi
else
  echo "❌ 端口 $PORT 未在监听"
  pm2 logs saas-demo --lines 30 --nostream 2>/dev/null || true
  exit 1
fi
echo ""

# 7. 修复 Nginx 配置
echo "7. 修复 Nginx 配置..."
echo "----------------------------------------"
cd /home/ubuntu/telegram-ai-system
sudo bash scripts/server/fix_aikz_nginx.sh
echo ""

# 8. 清除 Nginx 缓存
echo "8. 清除可能的缓存..."
echo "----------------------------------------"
# 重启 Nginx 以清除可能的缓存
sudo systemctl restart nginx
echo "✅ Nginx 已重启"
echo ""

# 9. 最终验证
echo "9. 最终验证..."
echo "----------------------------------------"
sleep 3

# 测试外部访问
EXTERNAL_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN 2>/dev/null || echo "000")
if [ "$EXTERNAL_CODE" = "200" ]; then
  echo "✅ 外部访问正常 (HTTP $EXTERNAL_CODE)"
  
  # 检查返回的内容
  EXTERNAL_CONTENT=$(curl -s https://$DOMAIN 2>/dev/null | head -c 200)
  if echo "$EXTERNAL_CONTENT" | grep -qi "智控王\|Smart Control King"; then
    echo "⚠️  外部访问返回的内容仍包含 'AI 智控王'"
    echo "   可能是浏览器缓存，请尝试："
    echo "   1. 强制刷新 (Ctrl+F5 或 Cmd+Shift+R)"
    echo "   2. 清除浏览器缓存"
    echo "   3. 使用无痕模式访问"
  else
    echo "✅ 外部访问返回的内容正确"
  fi
else
  echo "⚠️  外部访问异常 (HTTP $EXTERNAL_CODE)"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "如果浏览器仍然显示错误页面，请："
echo "1. 强制刷新 (Ctrl+F5)"
echo "2. 清除浏览器缓存"
echo "3. 使用无痕模式访问"
echo "4. 检查 PM2 日志: pm2 logs saas-demo"
