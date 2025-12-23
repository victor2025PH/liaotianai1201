#!/bin/bash
# ============================================================
# 快速修复 502 错误
# ============================================================

set -e

# 自动检测项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ ! -d "$PROJECT_ROOT/saas-demo" ] && [ ! -d "$PROJECT_ROOT/admin-backend" ]; then
  if [ -d "/home/ubuntu/telegram-ai-system" ]; then
    PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
  else
    echo "❌ 无法找到项目根目录"
    exit 1
  fi
fi

echo "=========================================="
echo "🔧 快速修复 502 错误"
echo "时间: $(date)"
echo "项目根目录: $PROJECT_ROOT"
echo "=========================================="
echo ""

# 1. 检查并重启后端服务
echo "[1/5] 检查并重启后端服务..."
if pm2 list | grep -q "backend.*online"; then
  echo "  后端服务正在运行，重启中..."
  pm2 restart backend
else
  echo "  后端服务未运行，启动中..."
  cd "$PROJECT_ROOT/admin-backend" || exit 1
  pm2 start start.sh --name backend || {
    echo "  ❌ 后端启动失败"
    pm2 logs backend --lines 20 --nostream
  }
fi
sleep 3

# 检查后端是否响应
if curl -f http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
  echo "  ✅ 后端服务已启动并响应"
else
  echo "  ⚠️  后端服务可能未完全启动，继续..."
fi
echo ""

# 2. 检查并重启前端服务
echo "[2/5] 检查并重启前端服务..."
if pm2 list | grep -q "saas-demo-frontend.*online"; then
  echo "  前端服务正在运行，重启中..."
  pm2 restart saas-demo-frontend
else
  echo "  前端服务未运行，启动中..."
  cd "$PROJECT_ROOT/saas-demo" || exit 1
  export PORT=3005
  export NEXT_STANDALONE=false
  pm2 start npm \
    --name saas-demo-frontend \
    --max-memory-restart 1G \
    --update-env \
    --error "$PROJECT_ROOT/logs/saas-demo-frontend-error.log" \
    --output "$PROJECT_ROOT/logs/saas-demo-frontend-out.log" \
    --merge-logs \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
    -- start || {
    echo "  ❌ 前端启动失败"
    pm2 logs saas-demo-frontend --lines 20 --nostream
  }
fi
sleep 3

# 检查前端是否响应
if curl -f http://127.0.0.1:3005 >/dev/null 2>&1; then
  echo "  ✅ 前端服务已启动并响应"
else
  echo "  ⚠️  前端服务可能未完全启动，继续..."
fi
echo ""

# 3. 检查并重启其他三个服务
echo "[3/5] 检查并重启其他三个服务..."

# tgmini (3001)
if [ -d "$PROJECT_ROOT/tgmini20251220" ] && [ -d "$PROJECT_ROOT/tgmini20251220/dist" ]; then
  if pm2 list | grep -q "tgmini-frontend.*online"; then
    pm2 restart tgmini-frontend
  else
    pm2 start npx --name tgmini-frontend --max-memory-restart 1G -- serve -s "$PROJECT_ROOT/tgmini20251220/dist" -l 3001
  fi
  echo "  ✅ tgmini-frontend 已处理"
fi

# hongbao (3002)
if [ -d "$PROJECT_ROOT/hbwy20251220" ] && [ -d "$PROJECT_ROOT/hbwy20251220/dist" ]; then
  if pm2 list | grep -q "hongbao-frontend.*online"; then
    pm2 restart hongbao-frontend
  else
    pm2 start npx --name hongbao-frontend --max-memory-restart 1G -- serve -s "$PROJECT_ROOT/hbwy20251220/dist" -l 3002
  fi
  echo "  ✅ hongbao-frontend 已处理"
fi

# aizkw (3003)
if [ -d "$PROJECT_ROOT/aizkw20251219" ] && [ -d "$PROJECT_ROOT/aizkw20251219/dist" ]; then
  if pm2 list | grep -q "aizkw-frontend.*online"; then
    pm2 restart aizkw-frontend
  else
    pm2 start npx --name aizkw-frontend --max-memory-restart 1G -- serve -s "$PROJECT_ROOT/aizkw20251219/dist" -l 3003
  fi
  echo "  ✅ aizkw-frontend 已处理"
fi

pm2 save || true
echo ""

# 4. 重启 Nginx
echo "[4/5] 重启 Nginx..."
sudo systemctl restart nginx
sleep 2
if sudo systemctl is-active --quiet nginx; then
  echo "  ✅ Nginx 已重启"
else
  echo "  ❌ Nginx 启动失败"
  sudo systemctl status nginx --no-pager | head -10
fi
echo ""

# 5. 验证所有服务
echo "[5/5] 验证所有服务..."
echo "等待 5 秒后检查..."
sleep 5

echo ""
echo "PM2 进程状态:"
pm2 list
echo ""

echo "端口监听状态:"
netstat -tlnp 2>/dev/null | grep -E "8000|3005|3001|3002|3003" || echo "没有服务在监听"
echo ""

echo "服务健康检查:"
for port in 8000 3005 3001 3002 3003; do
  if curl -f http://127.0.0.1:$port >/dev/null 2>&1; then
    echo "  ✅ 端口 $port 响应正常"
  else
    echo "  ❌ 端口 $port 无响应"
  fi
done

echo ""
echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
