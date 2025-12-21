#!/bin/bash

# 启动 saas-demo (聊天AI后台)
# 使用方法: bash scripts/server/start_saas_demo.sh

set -e

echo "=========================================="
echo "🚀 启动 saas-demo (聊天AI后台)"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
SAAS_DEMO_DIR="$PROJECT_ROOT/saas-demo"
PORT=3000

# 检查项目目录
if [ ! -d "$SAAS_DEMO_DIR" ]; then
  echo "❌ saas-demo 目录不存在: $SAAS_DEMO_DIR"
  exit 1
fi

echo "✅ 项目目录: $SAAS_DEMO_DIR"
echo ""

# 进入项目目录
cd "$SAAS_DEMO_DIR" || {
  echo "❌ 无法进入项目目录"
  exit 1
}

# 检查 package.json
if [ ! -f "package.json" ]; then
  echo "❌ package.json 不存在"
  exit 1
fi

echo "✅ package.json 存在"
echo ""

# 检查 Node.js
if ! command -v node >/dev/null 2>&1; then
  echo "❌ Node.js 未安装"
  exit 1
fi

echo "✅ Node.js 版本: $(node -v)"
echo "✅ npm 版本: $(npm -v)"
echo ""

# 检查 PM2
if ! command -v pm2 >/dev/null 2>&1; then
  echo "⚠️  PM2 未安装，安装 PM2..."
  sudo npm install -g pm2
  pm2 startup systemd -u ubuntu --hp /home/ubuntu || true
fi

echo "✅ PM2 已安装"
echo ""

# 停止可能运行在端口 3000 的进程
if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
  echo "停止占用端口 $PORT 的进程..."
  sudo lsof -ti :$PORT | xargs sudo kill -9 2>/dev/null || true
  sleep 2
fi

# 停止并删除 PM2 旧进程
pm2 delete saas-demo 2>/dev/null || true

# 检查是否需要安装依赖
if [ ! -d "node_modules" ]; then
  echo "安装依赖..."
  npm install || {
    echo "❌ 依赖安装失败"
    exit 1
  }
  echo "✅ 依赖安装完成"
  echo ""
fi

# 检查是否需要构建
if [ ! -d ".next" ]; then
  echo "构建项目..."
  npm run build || {
    echo "❌ 构建失败"
    exit 1
  }
  echo "✅ 构建完成"
  echo ""
fi

# 确保日志目录存在
mkdir -p "$SAAS_DEMO_DIR/logs"

# 使用 PM2 启动（确保在正确的目录下）
echo "使用 PM2 启动 saas-demo..."
pm2 start npm \
  --name saas-demo \
  --cwd "$SAAS_DEMO_DIR" \
  --error "$SAAS_DEMO_DIR/logs/saas-demo-error.log" \
  --output "$SAAS_DEMO_DIR/logs/saas-demo-out.log" \
  --merge-logs \
  --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
  -- start || {
  echo "⚠️  PM2 启动失败，查看错误..."
  pm2 logs saas-demo --lines 10 --nostream 2>/dev/null || true
  exit 1
}

pm2 save || true
echo "✅ PM2 应用已启动"
pm2 list | grep saas-demo || true
echo ""

# 等待启动
echo "等待服务启动..."
sleep 10

# 检查端口是否在监听
echo "检查端口 $PORT..."
sleep 2
if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
  echo "✅ 端口 $PORT 正在监听"
  
  # 测试连接
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    echo "✅ 服务响应正常 (HTTP $HTTP_CODE)"
  else
    echo "⚠️  服务响应异常 (HTTP $HTTP_CODE)"
    pm2 logs saas-demo --lines 20 --nostream 2>/dev/null || true
  fi
else
  echo "❌ 端口 $PORT 未在监听，服务可能未成功启动"
  echo "查看 PM2 日志："
  pm2 logs saas-demo --lines 30 --nostream 2>/dev/null || true
  exit 1
fi

echo ""
echo "=========================================="
echo "✅ saas-demo 启动完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "访问地址："
echo "  本地: http://127.0.0.1:$PORT"
echo "  外部: https://aikz.usdt2026.cc"
echo ""
echo "查看日志："
echo "  pm2 logs saas-demo"
echo "  或: tail -f $SAAS_DEMO_DIR/logs/saas-demo-out.log"
