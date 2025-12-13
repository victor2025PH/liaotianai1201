#!/bin/bash
# ============================================================
# 彻底清理端口 8000 的所有进程
# ============================================================

set -e

echo "=========================================="
echo "彻底清理端口 8000"
echo "=========================================="

BACKEND_SERVICE="luckyred-api"

# Step 1: 停止 systemd 服务
echo ""
echo "[1/5] 停止 systemd 服务..."
echo "----------------------------------------"
if systemctl cat "$BACKEND_SERVICE" >/dev/null 2>&1; then
  echo "停止 $BACKEND_SERVICE..."
  sudo systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
  sleep 3
  echo "✅ 服务已停止"
else
  echo "⚠️  服务配置文件不存在"
fi

# Step 2: 查找所有占用端口 8000 的进程
echo ""
echo "[2/5] 查找所有占用端口 8000 的进程..."
echo "----------------------------------------"

# 使用多种方法查找进程
PIDS_TO_KILL=""

# 方法1: 使用 ss
SS_PIDS=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | sort -u || echo "")
if [ -n "$SS_PIDS" ]; then
  echo "通过 ss 找到的进程: $SS_PIDS"
  PIDS_TO_KILL="$PIDS_TO_KILL $SS_PIDS"
fi

# 方法2: 使用 lsof
LSOF_PIDS=$(sudo lsof -ti:8000 2>/dev/null | sort -u || echo "")
if [ -n "$LSOF_PIDS" ]; then
  echo "通过 lsof 找到的进程: $LSOF_PIDS"
  PIDS_TO_KILL="$PIDS_TO_KILL $LSOF_PIDS"
fi

# 方法3: 使用 fuser
FUSER_PIDS=$(sudo fuser 8000/tcp 2>/dev/null | awk '{print $1}' | sort -u || echo "")
if [ -n "$FUSER_PIDS" ]; then
  echo "通过 fuser 找到的进程: $FUSER_PIDS"
  PIDS_TO_KILL="$PIDS_TO_KILL $FUSER_PIDS"
fi

# 合并并去重
ALL_PIDS=$(echo "$PIDS_TO_KILL" | tr ' ' '\n' | sort -u | tr '\n' ' ')

if [ -z "$ALL_PIDS" ]; then
  echo "✅ 未找到占用端口 8000 的进程"
else
  echo "所有需要终止的进程: $ALL_PIDS"
fi

# Step 3: 终止所有相关进程
echo ""
echo "[3/5] 终止所有相关进程..."
echo "----------------------------------------"

# 终止找到的进程
for pid in $ALL_PIDS; do
  if [ -n "$pid" ] && [ "$pid" != "0" ]; then
    echo "终止进程 $pid..."
    sudo kill -9 "$pid" 2>/dev/null || true
  fi
done

# 强制终止所有 uvicorn 进程
echo "清理所有 uvicorn 进程..."
sudo pkill -9 -f "uvicorn.*8000" 2>/dev/null || true
sudo pkill -9 -f "uvicorn.*app.main" 2>/dev/null || true

# 强制终止所有可能占用端口的 Python 进程
echo "清理可能占用端口的 Python 进程..."
for pid in $(ps aux | grep -E "python.*app.main|python.*uvicorn" | grep -v grep | awk '{print $2}' || echo ""); do
  if [ -n "$pid" ]; then
    echo "终止 Python 进程 $pid..."
    sudo kill -9 "$pid" 2>/dev/null || true
  fi
done

# 使用 fuser 强制清理
echo "使用 fuser 强制清理端口..."
sudo fuser -k 8000/tcp 2>/dev/null || true

sleep 3

# Step 4: 验证端口已释放
echo ""
echo "[4/5] 验证端口已释放..."
echo "----------------------------------------"

PORT_8000_CHECK=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
if [ -z "$PORT_8000_CHECK" ]; then
  echo "✅ 端口 8000 已完全释放"
else
  echo "⚠️  端口 8000 仍被占用:"
  echo "$PORT_8000_CHECK"
  echo ""
  echo "尝试更激进的清理..."
  # 再次尝试清理
  sudo fuser -k 8000/tcp 2>/dev/null || true
  sleep 2
  PORT_8000_CHECK2=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
  if [ -z "$PORT_8000_CHECK2" ]; then
    echo "✅ 端口 8000 已释放（第二次尝试）"
  else
    echo "❌ 端口 8000 仍被占用，请手动检查"
    exit 1
  fi
fi

# Step 5: 重新加载 systemd 并启动服务
echo ""
echo "[5/5] 重新加载 systemd 并启动服务..."
echo "----------------------------------------"

sudo systemctl daemon-reload
sudo systemctl reset-failed "$BACKEND_SERVICE" 2>/dev/null || true

echo "启动 $BACKEND_SERVICE..."
sudo systemctl start "$BACKEND_SERVICE"

# 等待服务启动
echo "等待服务启动（15秒）..."
sleep 15

# 检查服务状态
STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
if [ "$STATUS" = "active" ]; then
  echo "✅ 后端服务已启动 (状态: $STATUS)"
  
  # 检查端口
  sleep 3
  PORT_8000_AFTER=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
  if [ -n "$PORT_8000_AFTER" ]; then
    NEW_PID=$(echo "$PORT_8000_AFTER" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || echo "")
    echo "✅ 端口 8000 正在监听 (PID: $NEW_PID)"
    
    # 测试健康检查
    echo "测试健康检查..."
    if curl -s --max-time 5 http://localhost:8000/health >/dev/null 2>&1; then
      echo "✅ 健康检查通过"
    else
      echo "⚠️  健康检查失败"
    fi
  else
    echo "❌ 端口 8000 未监听"
    echo "查看日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager | tail -50"
    exit 1
  fi
else
  echo "❌ 后端服务启动失败 (状态: $STATUS)"
  echo "查看日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager | tail -50"
  exit 1
fi

echo ""
echo "=========================================="
echo "清理完成，服务已启动"
echo "=========================================="

