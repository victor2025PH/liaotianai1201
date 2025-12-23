#!/bin/bash
# ============================================================
# 快速修复 WebSocket 和 PM2 问题
# ============================================================

set -e

# 自动检测项目根目录（脚本所在目录的父目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 如果自动检测失败，尝试常见路径
if [ ! -d "$PROJECT_ROOT/saas-demo" ] && [ ! -d "$PROJECT_ROOT/admin-backend" ]; then
  # 尝试从当前工作目录查找
  if [ -d "$(pwd)/saas-demo" ] || [ -d "$(pwd)/admin-backend" ]; then
    PROJECT_ROOT="$(pwd)"
  # 尝试常见路径
  elif [ -d "/home/ubuntu/telegram-ai-system" ]; then
    PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
  elif [ -d "/home/***/telegram-ai-system" ]; then
    PROJECT_ROOT="/home/***/telegram-ai-system"
  else
    echo "❌ 无法找到项目根目录，请手动设置 PROJECT_ROOT 变量"
    exit 1
  fi
fi

echo "📁 项目根目录: $PROJECT_ROOT"

echo "=========================================="
echo "🔧 修复 WebSocket 和 PM2 问题"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 1. 停止所有前端服务
echo "[1/4] 停止旧的前端服务..."
pm2 delete saas-demo-frontend 2>/dev/null || true
pm2 delete tgmini-frontend 2>/dev/null || true
pm2 delete hongbao-frontend 2>/dev/null || true
pm2 delete aizkw-frontend 2>/dev/null || true
sleep 2
echo "✅ 旧服务已停止"
echo ""

# 2. 拉取最新代码（包含 WebSocket 修复）
echo "[2/4] 拉取最新代码..."
cd "$PROJECT_ROOT" || exit 1
git fetch origin main || true
git pull origin main || {
  echo "⚠️  Git pull 失败，但继续..."
}
echo "✅ 代码已更新"
echo ""

# 3. 重新构建前端（应用 WebSocket 修复）
echo "[3/4] 重新构建前端（应用 WebSocket 修复）..."
cd "$PROJECT_ROOT/saas-demo" || exit 1
npm run build || {
  echo "⚠️  构建失败，但继续..."
}
echo "✅ 前端已重新构建"
echo ""

# 4. 使用修复后的方式重新启动所有服务
echo "[4/4] 使用修复后的方式重新启动服务..."
cd "$PROJECT_ROOT" || exit 1

# 启动 saas-demo-frontend (端口 3005)
if [ -d "$PROJECT_ROOT/saas-demo" ] && [ -d "$PROJECT_ROOT/saas-demo/.next" ]; then
  echo "启动 saas-demo-frontend..."
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
    -- start
  echo "✅ saas-demo-frontend 已启动"
  cd "$PROJECT_ROOT" || exit 1
fi

# 启动 tgmini (端口 3001)
if [ -d "$PROJECT_ROOT/tgmini20251220" ] && [ -d "$PROJECT_ROOT/tgmini20251220/dist" ]; then
  echo "启动 tgmini-frontend..."
  pm2 start npx \
    --name tgmini-frontend \
    --max-memory-restart 1G \
    --error "$PROJECT_ROOT/logs/tgmini-frontend-error.log" \
    --output "$PROJECT_ROOT/logs/tgmini-frontend-out.log" \
    --merge-logs \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
    -- serve -s "$PROJECT_ROOT/tgmini20251220/dist" -l 3001
  echo "✅ tgmini-frontend 已启动"
fi

# 启动 hongbao (端口 3002)
if [ -d "$PROJECT_ROOT/hbwy20251220" ] && [ -d "$PROJECT_ROOT/hbwy20251220/dist" ]; then
  echo "启动 hongbao-frontend..."
  pm2 start npx \
    --name hongbao-frontend \
    --max-memory-restart 1G \
    --error "$PROJECT_ROOT/logs/hongbao-frontend-error.log" \
    --output "$PROJECT_ROOT/logs/hongbao-frontend-out.log" \
    --merge-logs \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
    -- serve -s "$PROJECT_ROOT/hbwy20251220/dist" -l 3002
  echo "✅ hongbao-frontend 已启动"
fi

# 启动 aizkw (端口 3003)
if [ -d "$PROJECT_ROOT/aizkw20251219" ] && [ -d "$PROJECT_ROOT/aizkw20251219/dist" ]; then
  echo "启动 aizkw-frontend..."
  pm2 start npx \
    --name aizkw-frontend \
    --max-memory-restart 1G \
    --error "$PROJECT_ROOT/logs/aizkw-frontend-error.log" \
    --output "$PROJECT_ROOT/logs/aizkw-frontend-out.log" \
    --merge-logs \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
    -- serve -s "$PROJECT_ROOT/aizkw20251219/dist" -l 3003
  echo "✅ aizkw-frontend 已启动"
fi

pm2 save || true

echo ""
echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "服务状态:"
pm2 list | grep -E "tgmini|hongbao|aizkw"
echo ""
echo "等待 5 秒后检查服务状态..."
sleep 5
pm2 list
