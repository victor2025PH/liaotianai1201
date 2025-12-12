#!/bin/bash
# ============================================================
# 诊断并修复 502 错误 - 完整版
# ============================================================

set -e

echo "=========================================="
echo "诊断并修复 502 Bad Gateway 错误"
echo "=========================================="

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_SERVICE="luckyred-api"

# Step 1: 检查所有占用端口 8000 的进程
echo ""
echo "[1/8] 检查端口 8000 占用情况..."
echo "----------------------------------------"
PORT_8000_INFO=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
if [ -n "$PORT_8000_INFO" ]; then
  echo "端口 8000 被占用:"
  echo "$PORT_8000_INFO"
  
  # 提取所有 PID
  PORT_8000_PIDS=$(echo "$PORT_8000_INFO" | grep -oP 'pid=\K\d+' || echo "")
  if [ -n "$PORT_8000_PIDS" ]; then
    echo ""
    echo "占用端口的进程:"
    for PID in $PORT_8000_PIDS; do
      echo "  PID $PID:"
      ps -p "$PID" -o pid,user,cmd --no-headers 2>/dev/null || echo "    (进程不存在)"
    done
  fi
else
  echo "✅ 端口 8000 未被占用"
fi

# Step 2: 检查所有 uvicorn 进程
echo ""
echo "[2/8] 检查所有 uvicorn 进程..."
echo "----------------------------------------"
UVICORN_PROCESSES=$(ps aux | grep -E "uvicorn|python.*app.main" | grep -v grep || echo "")
if [ -n "$UVICORN_PROCESSES" ]; then
  echo "找到 uvicorn 相关进程:"
  echo "$UVICORN_PROCESSES"
else
  echo "✅ 没有找到 uvicorn 进程"
fi

# Step 3: 停止 systemd 服务
echo ""
echo "[3/8] 停止 systemd 服务..."
echo "----------------------------------------"
sudo systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
sleep 3

# Step 4: 彻底清理所有相关进程
echo ""
echo "[4/8] 彻底清理所有相关进程..."
echo "----------------------------------------"

# 清理端口 8000
if [ -n "$PORT_8000_PIDS" ]; then
  for PID in $PORT_8000_PIDS; do
    echo "  杀死进程 PID: $PID"
    sudo kill -9 "$PID" 2>/dev/null || true
  done
fi

# 清理所有 uvicorn 进程
echo "  清理所有 uvicorn 进程..."
sudo pkill -9 -f "uvicorn.*8000" 2>/dev/null || true
sudo pkill -9 -f "uvicorn.*app.main" 2>/dev/null || true
sudo pkill -9 -f "python.*app.main" 2>/dev/null || true

# 使用 fuser
if command -v fuser >/dev/null 2>&1; then
  echo "  使用 fuser 清理端口..."
  sudo fuser -k 8000/tcp 2>/dev/null || true
fi

# 等待进程完全退出
sleep 3

# 验证清理结果
REMAINING=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
if [ -z "$REMAINING" ]; then
  echo "  ✅ 端口 8000 已完全清理"
else
  echo "  ⚠️  端口 8000 仍有进程占用:"
  echo "$REMAINING"
fi

# Step 5: 检查服务配置
echo ""
echo "[5/8] 检查服务配置..."
echo "----------------------------------------"
if [ -f "/etc/systemd/system/$BACKEND_SERVICE.service" ]; then
  echo "✅ 服务配置文件存在"
  echo ""
  echo "服务配置内容:"
  sudo systemctl cat "$BACKEND_SERVICE" | head -30
else
  echo "❌ 服务配置文件不存在"
  echo "  尝试重新部署..."
  if [ -f "$PROJECT_DIR/scripts/server/deploy-systemd.sh" ]; then
    cd "$PROJECT_DIR"
    sudo bash scripts/server/deploy-systemd.sh || echo "  ⚠️  部署失败"
  fi
fi

# Step 6: 检查工作目录和文件
echo ""
echo "[6/8] 检查工作目录和关键文件..."
echo "----------------------------------------"
WORK_DIR="$PROJECT_DIR/admin-backend"
if [ -d "$WORK_DIR" ]; then
  echo "✅ 工作目录存在: $WORK_DIR"
  
  # 检查虚拟环境
  if [ -d "$WORK_DIR/venv" ] && [ -f "$WORK_DIR/venv/bin/uvicorn" ]; then
    echo "✅ 虚拟环境存在"
    echo "  uvicorn 路径: $WORK_DIR/venv/bin/uvicorn"
  else
    echo "❌ 虚拟环境不存在或损坏"
    echo "  需要重新创建虚拟环境"
  fi
  
  # 检查主应用文件
  if [ -f "$WORK_DIR/app/main.py" ]; then
    echo "✅ 主应用文件存在"
  else
    echo "❌ 主应用文件不存在: $WORK_DIR/app/main.py"
  fi
  
  # 检查 .env 文件
  if [ -f "$WORK_DIR/.env" ]; then
    echo "✅ .env 文件存在"
  else
    echo "⚠️  .env 文件不存在（可能使用环境变量）"
  fi
else
  echo "❌ 工作目录不存在: $WORK_DIR"
fi

# Step 7: 检查最近的日志
echo ""
echo "[7/8] 检查最近的错误日志..."
echo "----------------------------------------"
echo "最后 30 行日志:"
sudo journalctl -u "$BACKEND_SERVICE" -n 30 --no-pager | tail -30

# Step 8: 重置并启动服务
echo ""
echo "[8/8] 重置并启动服务..."
echo "----------------------------------------"

# 重置失败状态
sudo systemctl reset-failed "$BACKEND_SERVICE" 2>/dev/null || true
sudo systemctl daemon-reload 2>/dev/null || true

# 启动服务
echo "启动服务..."
sudo systemctl start "$BACKEND_SERVICE" || {
  echo "❌ 启动失败"
  echo ""
  echo "查看详细错误:"
  sudo journalctl -u "$BACKEND_SERVICE" -n 50 --no-pager | grep -i "error\|fail\|exception" | tail -20
  exit 1
}

# 等待服务启动
echo "等待服务启动（最多 30 秒）..."
for i in {1..30}; do
  sleep 1
  STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "inactive")
  if [ "$STATUS" = "active" ]; then
    echo "✅ 服务已启动"
    break
  fi
  if [ $((i % 5)) -eq 0 ]; then
    echo "  等待中... ($i/30) - 状态: $STATUS"
  fi
done

# 最终验证
echo ""
echo "=========================================="
echo "最终验证"
echo "=========================================="

# 检查服务状态
FINAL_STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "inactive")
echo "服务状态: $FINAL_STATUS"

if [ "$FINAL_STATUS" = "active" ]; then
  # 检查端口监听
  sleep 2
  PORT_LISTENING=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
  if [ -n "$PORT_LISTENING" ]; then
    echo "✅ 端口 8000 正在监听"
    echo "$PORT_LISTENING"
  else
    echo "⚠️  端口 8000 未监听"
  fi
  
  # 健康检查
  echo ""
  echo "执行健康检查..."
  sleep 2
  HEALTH_RESPONSE=$(curl -s --max-time 5 http://localhost:8000/health 2>/dev/null || echo "ERROR")
  if [ "$HEALTH_RESPONSE" = '{"status":"ok"}' ] || [ "$HEALTH_RESPONSE" = '{"status": "ok"}' ]; then
    echo "✅ 健康检查通过: $HEALTH_RESPONSE"
    echo ""
    echo "=========================================="
    echo "✅ 修复成功！服务已正常运行"
    echo "=========================================="
  else
    echo "⚠️  健康检查失败: $HEALTH_RESPONSE"
    echo "  查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
  fi
else
  echo "❌ 服务未启动"
  echo ""
  echo "查看详细错误日志:"
  sudo journalctl -u "$BACKEND_SERVICE" -n 50 --no-pager | tail -30
  echo ""
  echo "查看服务状态:"
  sudo systemctl status "$BACKEND_SERVICE" --no-pager | head -30
  exit 1
fi

