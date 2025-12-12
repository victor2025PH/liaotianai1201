#!/bin/bash
# ============================================================
# 修复后端连接问题
# ============================================================

echo "=========================================="
echo "修复后端连接问题"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 1. 检查并清理端口8000
echo "[1/4] 检查端口8000..."
PORT_8000_PID=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || true)
if [ -n "$PORT_8000_PID" ]; then
  echo "  发现端口8000被占用 (PID: $PORT_8000_PID)"
  echo "  清理占用进程..."
  sudo kill -9 "$PORT_8000_PID" 2>/dev/null || true
  sleep 2
  echo "  ✅ 端口已清理"
else
  echo "  ✅ 端口8000空闲"
fi

echo ""

# 2. 确定后端服务名称
echo "[2/4] 确定后端服务..."
BACKEND_SERVICE=""
if systemctl cat luckyred-api.service >/dev/null 2>&1; then
  BACKEND_SERVICE="luckyred-api"
elif systemctl cat telegram-backend.service >/dev/null 2>&1; then
  BACKEND_SERVICE="telegram-backend"
fi

if [ -z "$BACKEND_SERVICE" ]; then
  echo "  ❌ 后端服务未找到，尝试部署systemd服务..."
  if [ -f "$PROJECT_DIR/scripts/server/deploy-systemd.sh" ]; then
    sudo bash "$PROJECT_DIR/scripts/server/deploy-systemd.sh"
    if systemctl cat luckyred-api.service >/dev/null 2>&1; then
      BACKEND_SERVICE="luckyred-api"
    fi
  fi
fi

if [ -z "$BACKEND_SERVICE" ]; then
  echo "  ❌ 无法找到或创建后端服务"
  exit 1
fi

echo "  后端服务: $BACKEND_SERVICE"

echo ""

# 3. 重启后端服务
echo "[3/4] 重启后端服务..."
sudo systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
sleep 2
sudo systemctl start "$BACKEND_SERVICE"
sleep 5

STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
if [ "$STATUS" = "active" ]; then
  echo "  ✅ 后端服务已启动"
else
  echo "  ⚠️  后端服务状态: $STATUS"
  echo "  查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
fi

echo ""

# 4. 验证连接
echo "[4/4] 验证后端连接..."
sleep 3
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
  echo "  ✅ 后端API连接成功"
  echo "  健康检查响应:"
  curl -s http://localhost:8000/health | head -3
else
  echo "  ❌ 后端API连接失败"
  echo "  请检查日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
fi

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="

