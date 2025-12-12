#!/bin/bash
# ============================================================
# 彻底清理所有 uvicorn 进程
# ============================================================

set -e

echo "=========================================="
echo "彻底清理所有 uvicorn 进程"
echo "=========================================="

# Step 1: 列出所有 uvicorn 进程
echo ""
echo "[1/4] 查找所有 uvicorn 进程..."
echo "----------------------------------------"
UVICORN_PROCESSES=$(ps aux | grep -E "uvicorn|python.*app.main" | grep -v grep || echo "")
if [ -n "$UVICORN_PROCESSES" ]; then
  echo "找到以下进程:"
  echo "$UVICORN_PROCESSES"
  echo ""
  
  # 提取所有 PID
  UVICORN_PIDS=$(echo "$UVICORN_PROCESSES" | awk '{print $2}')
  echo "进程 PID 列表: $UVICORN_PIDS"
else
  echo "✅ 没有找到 uvicorn 进程"
  exit 0
fi

# Step 2: 停止 systemd 服务
echo ""
echo "[2/4] 停止 systemd 服务..."
echo "----------------------------------------"
BACKEND_SERVICE="luckyred-api"
if systemctl cat "$BACKEND_SERVICE" >/dev/null 2>&1; then
  echo "停止服务: $BACKEND_SERVICE"
  sudo systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
  sleep 3
  echo "✅ 服务已停止"
else
  echo "⚠️  服务不存在"
fi

# Step 3: 杀死所有 uvicorn 进程
echo ""
echo "[3/4] 杀死所有 uvicorn 进程..."
echo "----------------------------------------"

# 方法1: 按 PID 杀死
for PID in $UVICORN_PIDS; do
  if ps -p "$PID" >/dev/null 2>&1; then
    echo "  杀死进程 PID: $PID"
    sudo kill -9 "$PID" 2>/dev/null || true
  fi
done

# 方法2: 使用 pkill
echo "  使用 pkill 清理..."
sudo pkill -9 -f "uvicorn.*8000" 2>/dev/null || true
sudo pkill -9 -f "uvicorn.*app.main" 2>/dev/null || true
sudo pkill -9 -f "python.*app.main" 2>/dev/null || true

# 方法3: 使用 fuser 清理端口
if command -v fuser >/dev/null 2>&1; then
  echo "  使用 fuser 清理端口 8000..."
  sudo fuser -k 8000/tcp 2>/dev/null || true
fi

# 等待进程完全退出
sleep 3

# Step 4: 验证清理结果
echo ""
echo "[4/4] 验证清理结果..."
echo "----------------------------------------"

# 检查是否还有进程
REMAINING_PROCESSES=$(ps aux | grep -E "uvicorn|python.*app.main" | grep -v grep || echo "")
if [ -z "$REMAINING_PROCESSES" ]; then
  echo "✅ 所有 uvicorn 进程已清理"
else
  echo "⚠️  仍有进程在运行:"
  echo "$REMAINING_PROCESSES"
  echo ""
  echo "强制清理..."
  for PID in $(echo "$REMAINING_PROCESSES" | awk '{print $2}'); do
    echo "  强制杀死 PID: $PID"
    sudo kill -9 "$PID" 2>/dev/null || true
  done
  sleep 2
fi

# 检查端口占用
PORT_8000=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
if [ -z "$PORT_8000" ]; then
  echo "✅ 端口 8000 已释放"
else
  echo "⚠️  端口 8000 仍被占用:"
  echo "$PORT_8000"
  echo ""
  echo "提取 PID 并强制清理..."
  PORT_PIDS=$(echo "$PORT_8000" | grep -oP 'pid=\K\d+' || echo "")
  for PID in $PORT_PIDS; do
    echo "  杀死占用端口的进程 PID: $PID"
    sudo kill -9 "$PID" 2>/dev/null || true
  done
  sleep 2
fi

# 最终验证
FINAL_CHECK=$(ps aux | grep -E "uvicorn|python.*app.main" | grep -v grep || echo "")
FINAL_PORT=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")

if [ -z "$FINAL_CHECK" ] && [ -z "$FINAL_PORT" ]; then
  echo ""
  echo "=========================================="
  echo "✅ 清理完成！所有进程和端口已释放"
  echo "=========================================="
  echo ""
  echo "现在可以启动 systemd 服务:"
  echo "  sudo systemctl start luckyred-api"
  echo "  sudo systemctl status luckyred-api"
else
  echo ""
  echo "=========================================="
  echo "⚠️  清理未完全完成"
  echo "=========================================="
  if [ -n "$FINAL_CHECK" ]; then
    echo "仍有进程:"
    echo "$FINAL_CHECK"
  fi
  if [ -n "$FINAL_PORT" ]; then
    echo "端口仍被占用:"
    echo "$FINAL_PORT"
  fi
  exit 1
fi

