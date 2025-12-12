#!/bin/bash
# ============================================================
# 彻底修复 502 Bad Gateway 错误
# ============================================================

set -e

echo "=========================================="
echo "修复 502 Bad Gateway 错误"
echo "=========================================="

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_SERVICE="luckyred-api"

# Step 1: 停止 systemd 服务
echo ""
echo "[1/6] 停止 systemd 服务..."
sudo systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
sleep 3

# Step 2: 彻底清理端口 8000
echo ""
echo "[2/6] 彻底清理端口 8000..."
# 方法1: 使用 ss 查找并杀死进程
PORT_8000_PIDS=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | grep -oP 'pid=\K\d+' || true)
if [ -n "$PORT_8000_PIDS" ]; then
  echo "  找到占用端口 8000 的进程: $PORT_8000_PIDS"
  for PID in $PORT_8000_PIDS; do
    echo "  杀死进程 PID: $PID"
    sudo kill -9 "$PID" 2>/dev/null || true
  done
  sleep 2
fi

# 方法2: 使用 lsof 查找并杀死进程
if command -v lsof >/dev/null 2>&1; then
  LSOF_PIDS=$(sudo lsof -ti:8000 2>/dev/null || true)
  if [ -n "$LSOF_PIDS" ]; then
    echo "  使用 lsof 找到的进程: $LSOF_PIDS"
    for PID in $LSOF_PIDS; do
      echo "  杀死进程 PID: $PID"
      sudo kill -9 "$PID" 2>/dev/null || true
    done
    sleep 2
  fi
fi

# 方法3: 使用 pkill 杀死所有 uvicorn 进程
echo "  清理所有 uvicorn 进程..."
sudo pkill -9 -f "uvicorn.*8000" 2>/dev/null || true
sudo pkill -9 -f "uvicorn.*app.main" 2>/dev/null || true
sleep 2

# 方法4: 使用 fuser 杀死进程（如果可用）
if command -v fuser >/dev/null 2>&1; then
  echo "  使用 fuser 清理端口..."
  sudo fuser -k 8000/tcp 2>/dev/null || true
  sleep 2
fi

# 验证端口是否已释放
PORT_CHECK=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
if [ -n "$PORT_CHECK" ]; then
  echo "  ⚠️  端口 8000 仍然被占用，尝试更激进的方法..."
  # 使用 netstat 查找进程
  if command -v netstat >/dev/null 2>&1; then
    NETSTAT_PIDS=$(sudo netstat -tlnp 2>/dev/null | grep ":8000" | awk '{print $7}' | cut -d'/' -f1 | grep -E '^[0-9]+$' || true)
    for PID in $NETSTAT_PIDS; do
      echo "  杀死进程 PID: $PID"
      sudo kill -9 "$PID" 2>/dev/null || true
    done
    sleep 2
  fi
else
  echo "  ✅ 端口 8000 已释放"
fi

# Step 3: 检查并清理残留进程
echo ""
echo "[3/6] 检查残留进程..."
# 查找所有可能的 Python 进程
PYTHON_PIDS=$(ps aux | grep -E "uvicorn|python.*app.main" | grep -v grep | awk '{print $2}' || true)
if [ -n "$PYTHON_PIDS" ]; then
  echo "  找到残留的 Python 进程: $PYTHON_PIDS"
  for PID in $PYTHON_PIDS; do
    echo "  杀死进程 PID: $PID"
    sudo kill -9 "$PID" 2>/dev/null || true
  done
  sleep 2
fi

# Step 4: 重置 systemd 服务状态
echo ""
echo "[4/6] 重置 systemd 服务状态..."
sudo systemctl reset-failed "$BACKEND_SERVICE" 2>/dev/null || true
sudo systemctl daemon-reload 2>/dev/null || true

# Step 5: 检查服务配置
echo ""
echo "[5/6] 检查服务配置..."
if [ -f "/etc/systemd/system/$BACKEND_SERVICE.service" ]; then
  echo "  ✅ 服务配置文件存在"
  # 检查 WorkingDirectory
  WORK_DIR=$(sudo systemctl show -p WorkingDirectory --value "$BACKEND_SERVICE" 2>/dev/null || echo "")
  if [ -n "$WORK_DIR" ]; then
    echo "  WorkingDirectory: $WORK_DIR"
    if [ ! -d "$WORK_DIR" ]; then
      echo "  ⚠️  WorkingDirectory 不存在，使用默认路径"
      WORK_DIR="$PROJECT_DIR/admin-backend"
    fi
  else
    WORK_DIR="$PROJECT_DIR/admin-backend"
  fi
  
  # 检查 ExecStart
  EXEC_START=$(sudo systemctl show -p ExecStart --value "$BACKEND_SERVICE" 2>/dev/null || echo "")
  if [ -n "$EXEC_START" ]; then
    echo "  ExecStart: $EXEC_START"
  fi
else
  echo "  ❌ 服务配置文件不存在"
  echo "  尝试重新部署 systemd 服务..."
  if [ -f "$PROJECT_DIR/scripts/server/deploy-systemd.sh" ]; then
    cd "$PROJECT_DIR"
    sudo bash scripts/server/deploy-systemd.sh || echo "  ⚠️  部署失败"
  fi
fi

# Step 6: 启动服务
echo ""
echo "[6/6] 启动服务..."
cd "$PROJECT_DIR/admin-backend" 2>/dev/null || cd "$PROJECT_DIR" || true

# 确保虚拟环境存在
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
  echo "  ✅ 虚拟环境存在"
else
  echo "  ⚠️  虚拟环境不存在，创建中..."
  python3 -m venv venv || {
    echo "  ❌ 创建虚拟环境失败"
    exit 1
  }
fi

# 启动服务
echo "  启动 $BACKEND_SERVICE 服务..."
sudo systemctl start "$BACKEND_SERVICE" || {
  echo "  ❌ 启动失败"
  echo "  查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
  exit 1
}

# 等待服务启动
echo "  等待服务启动（最多 30 秒）..."
for i in {1..30}; do
  sleep 1
  STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "inactive")
  if [ "$STATUS" = "active" ]; then
    echo "  ✅ 服务已启动"
    break
  fi
  if [ $((i % 5)) -eq 0 ]; then
    echo "    等待中... ($i/30)"
  fi
done

# 最终验证
echo ""
echo "=========================================="
echo "验证服务状态"
echo "=========================================="

# 检查服务状态
FINAL_STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "inactive")
echo "服务状态: $FINAL_STATUS"

if [ "$FINAL_STATUS" = "active" ]; then
  # 健康检查
  echo "执行健康检查..."
  sleep 2
  if curl -s -f --max-time 5 http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ 健康检查通过"
    echo ""
    echo "服务已成功启动！"
    echo "  - 后端 API: http://localhost:8000"
    echo "  - 健康检查: http://localhost:8000/health"
    echo ""
    echo "如果仍然无法访问，请检查："
    echo "  1. Nginx 配置: sudo nginx -t"
    echo "  2. Nginx 状态: sudo systemctl status nginx"
    echo "  3. 防火墙设置: sudo ufw status"
  else
    echo "⚠️  健康检查失败"
    echo "  查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
  fi
else
  echo "❌ 服务未启动"
  echo "  查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
  echo "  查看状态: sudo systemctl status $BACKEND_SERVICE --no-pager"
  exit 1
fi

