#!/bin/bash
# 修复 Next.js standalone 模式启动问题

set -e

echo "=========================================="
echo "修复 Next.js standalone 模式启动"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/aizkw20251219"

# 进入项目目录
cd "$PROJECT_DIR" || {
  echo "❌ 无法进入项目目录: $PROJECT_DIR"
  exit 1
}

echo "当前目录: $(pwd)"
echo ""

# 1. 停止旧进程
echo "[1/6] 停止旧进程..."
echo "----------------------------------------"
pm2 delete frontend 2>/dev/null || true
sudo lsof -ti :3000 | xargs sudo kill -9 2>/dev/null || true
sleep 2
echo "✅ 旧进程已停止"
echo ""

# 2. 检查构建输出
echo "[2/6] 检查构建输出..."
echo "----------------------------------------"
if [ ! -d ".next" ]; then
  echo "❌ .next 目录不存在，需要重新构建"
  echo "执行构建..."
  export NODE_OPTIONS="--max-old-space-size=3072"
  npm run build || {
    echo "❌ 构建失败"
    exit 1
  }
fi

if [ -f ".next/standalone/server.js" ]; then
  echo "✅ standalone/server.js 存在"
  USE_STANDALONE=true
else
  echo "⚠️  standalone/server.js 不存在"
  USE_STANDALONE=false
fi
echo ""

# 3. 创建日志目录
echo "[3/6] 准备日志目录..."
echo "----------------------------------------"
mkdir -p "$PROJECT_DIR/logs"
echo "✅ 日志目录已准备"
echo ""

# 4. 启动应用（使用 PM2）
echo "[4/6] 启动应用..."
echo "----------------------------------------"

if [ "$USE_STANDALONE" = "true" ]; then
  echo "使用 standalone 模式启动..."
  pm2 start "node .next/standalone/server.js" \
    --name frontend \
    --interpreter node \
    --env NODE_ENV=production \
    --env PORT=3000 \
    --env HOSTNAME=0.0.0.0 \
    --env NODE_OPTIONS="--max-old-space-size=3072" \
    --error "$PROJECT_DIR/logs/frontend-error.log" \
    --output "$PROJECT_DIR/logs/frontend-out.log" \
    --merge-logs \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z" || {
    echo "❌ PM2 启动失败"
    echo "查看错误:"
    pm2 logs frontend --lines 20 --nostream 2>/dev/null || true
    exit 1
  }
else
  echo "使用标准模式启动..."
  pm2 start npm \
    --name frontend \
    -- start \
    --env NODE_ENV=production \
    --env PORT=3000 \
    --env NODE_OPTIONS="--max-old-space-size=3072" \
    --error "$PROJECT_DIR/logs/frontend-error.log" \
    --output "$PROJECT_DIR/logs/frontend-out.log" \
    --merge-logs \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z" || {
    echo "❌ PM2 启动失败"
    echo "查看错误:"
    pm2 logs frontend --lines 20 --nostream 2>/dev/null || true
    exit 1
  }
fi

pm2 save
echo "✅ 应用已启动"
pm2 list | grep frontend || true
echo ""

# 5. 等待并验证
echo "[5/6] 等待应用启动并验证..."
echo "----------------------------------------"
sleep 8

# 检查 PM2 状态
pm2 describe frontend | grep -E "status|pid|uptime" || true
echo ""

# 检查端口
if sudo lsof -i :3000 >/dev/null 2>&1; then
  echo "✅ 端口 3000 正在监听"
  
  # 测试连接
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000 || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✅ 应用响应正常 (HTTP $HTTP_CODE)"
  else
    echo "⚠️  应用响应异常 (HTTP $HTTP_CODE)"
    echo "查看日志:"
    pm2 logs frontend --lines 10 --nostream
  fi
else
  echo "❌ 端口 3000 未在监听"
  echo "查看错误日志:"
  pm2 logs frontend --lines 30 --nostream
  exit 1
fi
echo ""

# 6. 重载 Nginx
echo "[6/6] 重载 Nginx..."
echo "----------------------------------------"
sudo systemctl reload nginx || {
  echo "⚠️  Nginx reload 失败，尝试 restart..."
  sudo systemctl restart nginx || {
    echo "❌ Nginx restart 失败"
    exit 1
  }
}
echo "✅ Nginx 已重载"
echo ""

echo "=========================================="
echo "✅ 修复完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "应用状态:"
pm2 list | grep frontend
echo ""
echo "测试访问:"
echo "  curl -I http://127.0.0.1:3000"
echo "  或访问: https://aikz.usdt2026.cc"
