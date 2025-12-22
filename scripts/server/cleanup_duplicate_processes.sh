#!/bin/bash
# ============================================================
# 清理重复和冲突的进程
# 解决端口冲突和重复启动问题
# ============================================================

set -e

echo "=========================================="
echo "🧹 清理重复和冲突的进程"
echo "=========================================="
echo ""

# 1. 停止所有可能占用端口 3000 的进程
echo "[1/5] 停止占用端口 3000 的进程..."
echo "----------------------------------------"
PORT_3000_PIDS=$(sudo lsof -ti :3000 2>/dev/null || echo "")
if [ -n "$PORT_3000_PIDS" ]; then
  echo "发现占用端口 3000 的进程: $PORT_3000_PIDS"
  echo "$PORT_3000_PIDS" | xargs sudo kill -9 2>/dev/null || true
  sleep 2
  echo "✅ 已清理端口 3000"
else
  echo "✅ 端口 3000 未被占用"
fi
echo ""

# 2. 停止所有重复的 saas-demo 相关进程
echo "[2/5] 停止重复的 saas-demo 进程..."
echo "----------------------------------------"
pm2 delete saas-demo 2>/dev/null || true
pm2 delete saas-demo-frontend 2>/dev/null || true
pkill -f 'next.*start|node.*3000|saas-demo' 2>/dev/null || true
sleep 2
echo "✅ 已清理 saas-demo 相关进程"
echo ""

# 3. 检查并清理其他可能的重复进程
echo "[3/5] 检查其他重复进程..."
echo "----------------------------------------"
# 检查是否有多个 frontend 进程
FRONTEND_COUNT=$(pm2 list 2>/dev/null | grep -c "frontend" || echo "0")
# 确保 FRONTEND_COUNT 是数字
if [ -z "$FRONTEND_COUNT" ] || [ "$FRONTEND_COUNT" = "" ]; then
  FRONTEND_COUNT=0
fi
# 使用数值比较（需要确保是数字）
if [ "$FRONTEND_COUNT" -gt 1 ] 2>/dev/null; then
  echo "⚠️  发现多个 frontend 进程，保留最新的..."
  # 保留最新的，删除旧的
  pm2 delete frontend 2>/dev/null || true
fi
echo "✅ 重复进程检查完成"
echo ""

# 4. 验证端口状态
echo "[4/5] 验证端口状态..."
echo "----------------------------------------"
for port in 3000 3001 3002 3003 8000; do
  if sudo lsof -i :$port >/dev/null 2>&1; then
    PROCESS=$(sudo lsof -i :$port | tail -1 | awk '{print $1, $2}')
    echo "  ✅ 端口 $port: $PROCESS"
  else
    echo "  ⚠️  端口 $port: 未监听"
  fi
done
echo ""

# 5. 显示当前 PM2 进程列表
echo "[5/5] 当前 PM2 进程列表..."
echo "----------------------------------------"
pm2 list
echo ""

echo "=========================================="
echo "✅ 清理完成"
echo "=========================================="
echo ""
echo "建议操作："
echo "1. 如果还有端口冲突，请手动检查: sudo lsof -i :3000"
echo "2. 重新部署: bash scripts/deploy_full.sh"
echo "3. 监控资源使用: pm2 monit"
