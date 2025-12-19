#!/bin/bash
# ============================================================
# 终极修复端口 3000 占用问题
# ============================================================

echo "=========================================="
echo "🔧 终极修复端口 3000 占用问题"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 1. 停止所有 PM2 进程
echo "[1/7] 停止所有 PM2 进程..."
echo "----------------------------------------"
sudo -u ubuntu pm2 stop all 2>/dev/null || true
sudo -u ubuntu pm2 delete all 2>/dev/null || true
sleep 2
echo "✅ PM2 进程已全部停止"
echo ""

# 2. 查找并显示所有占用端口 3000 的进程（包括所有用户）
echo "[2/7] 查找所有占用端口 3000 的进程（包括所有用户）..."
echo "----------------------------------------"
PORT_3000_PIDS=$(sudo lsof -t -i:3000 2>/dev/null || echo "")
if [ -n "$PORT_3000_PIDS" ]; then
    echo "发现占用端口 3000 的进程:"
    for PID in $PORT_3000_PIDS; do
        PROCESS_INFO=$(ps -fp $PID -o pid,ppid,user,comm,args 2>/dev/null || echo "")
        if [ -n "$PROCESS_INFO" ]; then
            echo "  PID $PID:"
            echo "$PROCESS_INFO" | tail -1
        fi
    done
else
    echo "✅ 端口 3000 当前未被占用（lsof 检查）"
fi

# 使用 ss 命令也检查一下（可能发现 lsof 没发现的）
SS_PORT_3000=$(sudo ss -tlnp 2>/dev/null | grep ":3000 " || echo "")
if [ -n "$SS_PORT_3000" ]; then
    echo ""
    echo "⚠️  ss 命令发现端口 3000 被占用:"
    echo "$SS_PORT_3000"
    # 从 ss 输出中提取 PID
    SS_PID=$(echo "$SS_PORT_3000" | grep -oP 'pid=\K\d+' | head -1 || echo "")
    if [ -n "$SS_PID" ]; then
        echo "  发现进程 PID: $SS_PID"
        ps -fp $SS_PID -o pid,ppid,user,comm,args 2>/dev/null || true
        PORT_3000_PIDS="$PORT_3000_PIDS $SS_PID"
    fi
fi
echo ""

# 3. 杀掉所有占用端口 3000 的进程（包括所有用户）
echo "[3/7] 强制杀掉所有占用端口 3000 的进程（包括所有用户）..."
echo "----------------------------------------"
if [ -n "$PORT_3000_PIDS" ]; then
    for PID in $PORT_3000_PIDS; do
        # 获取进程用户信息
        PROCESS_USER=$(ps -o user= -p $PID 2>/dev/null | tr -d ' ' || echo "unknown")
        echo "  杀掉 PID $PID (用户: $PROCESS_USER)..."
        sudo kill -9 $PID 2>/dev/null || true
    done
    sleep 2
fi

# 使用多种方法清理（包括所有用户的进程）
echo "  使用 fuser 清理端口 3000..."
sudo fuser -k -9 3000/tcp 2>/dev/null || true

echo "  杀掉所有 next-server 进程（所有用户）..."
sudo pkill -9 -f "next-server" 2>/dev/null || true

echo "  杀掉所有 standalone/server.js 进程（所有用户）..."
sudo pkill -9 -f "standalone/server.js" 2>/dev/null || true

# 额外：杀掉所有在端口 3000 上监听的 node 进程
echo "  查找并杀掉所有在端口 3000 上监听的 node 进程..."
NODE_PIDS=$(sudo lsof -t -i:3000 2>/dev/null | xargs ps -o pid,user,comm -p 2>/dev/null | grep -E "node|next" | awk '{print $1}' || echo "")
if [ -n "$NODE_PIDS" ]; then
    for PID in $NODE_PIDS; do
        echo "    杀掉 node 相关进程 PID $PID..."
        sudo kill -9 $PID 2>/dev/null || true
    done
fi

sleep 3
echo "✅ 已强制清理所有用户的进程"
echo ""

# 4. 再次检查端口状态
echo "[4/7] 再次检查端口 3000 状态..."
echo "----------------------------------------"
sleep 2
REMAINING_PIDS=$(sudo lsof -t -i:3000 2>/dev/null || echo "")
if [ -n "$REMAINING_PIDS" ]; then
    echo "⚠️  仍有进程占用端口 3000: $REMAINING_PIDS"
    echo "  强制清理..."
    for PID in $REMAINING_PIDS; do
        sudo kill -9 $PID 2>/dev/null || true
    done
    sudo fuser -k -9 3000/tcp 2>/dev/null || true
    sleep 3
else
    echo "✅ 端口 3000 已完全释放"
fi
echo ""

# 5. 检查是否有 systemd 服务也在运行
echo "[5/7] 检查 systemd 前端服务..."
echo "----------------------------------------"
if systemctl cat liaotian-frontend.service >/dev/null 2>&1; then
    echo "⚠️  发现 systemd 前端服务，停止它..."
    sudo systemctl stop liaotian-frontend 2>/dev/null || true
    sudo systemctl disable liaotian-frontend 2>/dev/null || true
    sleep 2
    echo "✅ systemd 服务已停止"
else
    echo "✅ 未发现 systemd 前端服务"
fi
echo ""

# 6. 最终验证端口 3000 已释放
echo "[6/7] 最终验证端口 3000 已释放..."
echo "----------------------------------------"
sleep 3
FINAL_CHECK=$(sudo lsof -t -i:3000 2>/dev/null || echo "")
if [ -n "$FINAL_CHECK" ]; then
    echo "❌ 端口 3000 仍被占用，无法继续"
    echo "占用进程: $FINAL_CHECK"
    echo ""
    echo "详细信息:"
    for PID in $FINAL_CHECK; do
        ps -fp $PID -o pid,ppid,user,comm,args 2>/dev/null || true
    done
    exit 1
fi

# 使用 ss 命令再次确认
SS_CHECK=$(sudo ss -tlnp 2>/dev/null | grep ":3000 " || echo "")
if [ -n "$SS_CHECK" ]; then
    echo "❌ ss 命令显示端口 3000 仍被占用"
    echo "$SS_CHECK"
    exit 1
fi

echo "✅ 端口 3000 已确认完全释放"
echo ""

# 7. 重新启动服务
echo "[7/7] 重新启动 PM2 服务..."
echo "----------------------------------------"
cd "$PROJECT_DIR" || exit 1

# 先启动 backend
echo "启动 backend..."
sudo -u ubuntu pm2 start ecosystem.config.js --only backend
sleep 3

# 再次确认端口 3000 空闲（防止 backend 启动过程中有什么变化）
sleep 2
FINAL_CHECK2=$(sudo lsof -t -i:3000 2>/dev/null || echo "")
if [ -n "$FINAL_CHECK2" ]; then
    echo "⚠️  启动 backend 后端口 3000 被占用，清理中..."
    sudo kill -9 $FINAL_CHECK2 2>/dev/null || true
    sudo fuser -k -9 3000/tcp 2>/dev/null || true
    sleep 2
fi

# 启动 frontend
echo "启动 frontend..."
sudo -u ubuntu pm2 start ecosystem.config.js --only frontend
sleep 5

# 检查状态
echo ""
echo "当前 PM2 状态:"
sudo -u ubuntu pm2 list

# 检查 frontend 状态
FRONTEND_STATUS=$(sudo -u ubuntu pm2 list | grep frontend | awk '{print $10}' || echo "")
if [ "$FRONTEND_STATUS" = "online" ]; then
    echo ""
    echo "✅ Frontend 服务已成功启动！"
    
    # 验证端口
    sleep 2
    PORT_CHECK=$(sudo ss -tlnp 2>/dev/null | grep ":3000 " || echo "")
    if [ -n "$PORT_CHECK" ]; then
        echo "✅ 端口 3000 正在监听"
        echo "$PORT_CHECK"
    else
        echo "⚠️  端口 3000 未监听（但服务显示 online）"
    fi
    
    # 保存配置
    sudo -u ubuntu pm2 save
    echo ""
    echo "🎉 修复成功！前端服务已正常运行"
else
    echo ""
    echo "❌ Frontend 服务启动失败，状态: $FRONTEND_STATUS"
    echo ""
    echo "查看错误日志:"
    sudo -u ubuntu pm2 logs frontend --err --lines 20 --nostream 2>&1 | tail -20
    echo ""
    echo "检查端口占用:"
    sudo lsof -i:3000 || echo "端口未被占用"
    sudo ss -tlnp | grep ":3000 " || echo "ss 显示端口未被占用"
fi

echo ""
echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="

