#!/bin/bash
# ============================================================
# 快速修复 502 Bad Gateway 错误
# ============================================================

set +e  # 不在第一个错误时退出

echo "=========================================="
echo "🚨 快速修复 502 Bad Gateway"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/api"
BACKEND_SERVICE="luckyred-api"

# Step 1: 检查服务状态
echo "[1/5] 检查后端服务状态..."
if systemctl is-active "$BACKEND_SERVICE" >/dev/null 2>&1; then
  echo "  ✅ 服务正在运行"
else
  echo "  ❌ 服务未运行"
fi

# Step 2: 检查端口
echo ""
echo "[2/5] 检查端口 8000..."
PORT_8000_PID=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || echo "")
if [ -n "$PORT_8000_PID" ]; then
  echo "  ✅ 端口 8000 正在监听 (PID: $PORT_8000_PID)"
else
  echo "  ❌ 端口 8000 未监听"
fi

# Step 3: 停止服务并清理端口
echo ""
echo "[3/5] 停止服务并清理端口..."
sudo systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
sleep 2

if [ -n "$PORT_8000_PID" ]; then
  echo "  清理端口 8000 (PID: $PORT_8000_PID)..."
  sudo kill -9 "$PORT_8000_PID" 2>/dev/null || true
  sleep 2
fi

# 清理所有相关进程
sudo pkill -9 -f "uvicorn.*8000" 2>/dev/null || true
sudo pkill -9 -f "uvicorn.*app.main" 2>/dev/null || true
sudo pkill -9 -f "gunicorn.*8000" 2>/dev/null || true
sleep 2

# Step 4: 重启服务
echo ""
echo "[4/5] 重启后端服务..."
sudo systemctl daemon-reload
sudo systemctl start "$BACKEND_SERVICE"
sleep 10

# Step 5: 验证服务
echo ""
echo "[5/5] 验证服务..."
STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
if [ "$STATUS" = "active" ]; then
  echo "  ✅ 服务已启动"
else
  echo "  ❌ 服务启动失败"
  echo ""
  echo "  查看日志:"
  sudo journalctl -u "$BACKEND_SERVICE" -n 50 --no-pager | tail -30
  exit 1
fi

# 检查端口
sleep 3
if sudo ss -tlnp 2>/dev/null | grep -q ":8000"; then
  echo "  ✅ 端口 8000 正在监听"
else
  echo "  ❌ 端口 8000 未监听"
  exit 1
fi

# 测试健康检查
if curl -s --max-time 5 http://localhost:8000/health >/dev/null 2>&1; then
  echo "  ✅ 健康检查通过"
else
  echo "  ⚠️  健康检查失败，但服务可能正在启动中"
fi

echo ""
echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果仍有问题，请检查："
echo "  1. 后端日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager"
echo "  2. Nginx 日志: sudo tail -50 /var/log/nginx/error.log"
echo "  3. Nginx 配置: sudo nginx -t"
echo ""

