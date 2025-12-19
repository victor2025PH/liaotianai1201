#!/bin/bash
# ============================================================
# 强制修复端口 3000 占用问题
# ============================================================

echo "=========================================="
echo "🔧 强制修复端口 3000 占用问题"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 1. 停止所有 PM2 进程
echo "[1/6] 停止所有 PM2 进程..."
echo "----------------------------------------"
sudo -u ubuntu pm2 stop all 2>/dev/null || true
sudo -u ubuntu pm2 delete all 2>/dev/null || true
echo "✅ PM2 进程已全部停止"
echo ""

# 2. 查找并杀掉所有占用端口 3000 的进程
echo "[2/6] 查找并杀掉所有占用端口 3000 的进程..."
echo "----------------------------------------"
PORT_3000_PIDS=$(sudo lsof -t -i:3000 2>/dev/null || echo "")
if [ -n "$PORT_3000_PIDS" ]; then
    echo "发现占用端口 3000 的进程:"
    for PID in $PORT_3000_PIDS; do
        PROCESS_INFO=$(ps -p $PID -o pid,comm,args 2>/dev/null || echo "")
        if [ -n "$PROCESS_INFO" ]; then
            echo "  PID $PID: $PROCESS_INFO"
        fi
    done
    echo ""
    echo "正在强制杀掉这些进程..."
    for PID in $PORT_3000_PIDS; do
        sudo kill -9 $PID 2>/dev/null || true
    done
    sleep 2
    echo "✅ 已强制杀掉占用端口 3000 的进程"
else
    echo "✅ 端口 3000 未被占用"
fi
echo ""

# 3. 杀掉所有 next-server 和 node 进程（与前端相关的）
echo "[3/6] 清理所有 next-server 和相关的 node 进程..."
echo "----------------------------------------"
# 查找所有 next-server 进程
NEXT_PIDS=$(pgrep -f "next-server" 2>/dev/null || echo "")
if [ -n "$NEXT_PIDS" ]; then
    echo "发现 next-server 进程: $NEXT_PIDS"
    sudo pkill -9 -f "next-server" 2>/dev/null || true
    sleep 1
fi

# 查找在项目目录下运行的 node 进程
cd "$PROJECT_DIR/saas-demo" 2>/dev/null || true
NODE_PIDS=$(pgrep -f "standalone/server.js" 2>/dev/null || echo "")
if [ -n "$NODE_PIDS" ]; then
    echo "发现 standalone server 进程: $NODE_PIDS"
    for PID in $NODE_PIDS; do
        sudo kill -9 $PID 2>/dev/null || true
    done
    sleep 1
fi
echo "✅ 已清理相关进程"
echo ""

# 4. 使用 fuser 强制释放端口
echo "[4/6] 使用 fuser 强制释放端口 3000..."
echo "----------------------------------------"
sudo fuser -k -9 3000/tcp 2>/dev/null || true
sleep 2
echo "✅ 端口释放完成"
echo ""

# 5. 验证端口 3000 已释放
echo "[5/6] 验证端口 3000 已释放..."
echo "----------------------------------------"
sleep 2
PORT_CHECK=$(sudo lsof -t -i:3000 2>/dev/null || echo "")
if [ -z "$PORT_CHECK" ]; then
    echo "✅ 端口 3000 已完全释放"
else
    echo "⚠️  端口 3000 仍被占用: $PORT_CHECK"
    echo "再次强制清理..."
    sudo fuser -k -9 3000/tcp 2>/dev/null || true
    for PID in $PORT_CHECK; do
        sudo kill -9 $PID 2>/dev/null || true
    done
    sleep 2
fi
echo ""

# 6. 重新启动服务
echo "[6/6] 重新启动 PM2 服务..."
echo "----------------------------------------"
cd "$PROJECT_DIR" || exit 1

# 等待一下确保端口完全释放
echo "等待端口完全释放..."
sleep 5

# 再次确认端口 3000 已释放
echo "再次确认端口 3000 状态..."
FINAL_CHECK=$(sudo lsof -t -i:3000 2>/dev/null || echo "")
if [ -n "$FINAL_CHECK" ]; then
    echo "⚠️  警告：端口 3000 仍被占用，强制清理..."
    for PID in $FINAL_CHECK; do
        sudo kill -9 $PID 2>/dev/null || true
    done
    sudo fuser -k -9 3000/tcp 2>/dev/null || true
    sleep 3
fi

# 最终验证
FINAL_CHECK2=$(sudo lsof -t -i:3000 2>/dev/null || echo "")
if [ -n "$FINAL_CHECK2" ]; then
    echo "❌ 端口 3000 仍被占用，无法启动服务"
    echo "占用进程: $FINAL_CHECK2"
    exit 1
fi

echo "✅ 端口 3000 已确认释放"
echo ""

# 检查是否有 systemd 服务也在运行前端
echo "检查是否有 systemd 前端服务..."
if systemctl cat liaotian-frontend.service >/dev/null 2>&1; then
    echo "⚠️  发现 systemd 前端服务，先停止它..."
    sudo systemctl stop liaotian-frontend 2>/dev/null || true
    sudo systemctl disable liaotian-frontend 2>/dev/null || true
    sleep 2
fi

# 检查 ecosystem.config.js
if [ -f "ecosystem.config.js" ]; then
    echo "使用 ecosystem.config.js 启动所有服务..."
    # 先启动 backend
    sudo -u ubuntu pm2 start ecosystem.config.js --only backend
    sleep 3
    
    # 再次确认端口 3000 空闲
    sleep 2
    PORT_CHECK_FINAL=$(sudo lsof -t -i:3000 2>/dev/null || echo "")
    if [ -z "$PORT_CHECK_FINAL" ]; then
        echo "启动 frontend 服务..."
        sudo -u ubuntu pm2 start ecosystem.config.js --only frontend
        sleep 5
    else
        echo "❌ 端口 3000 在启动前被占用: $PORT_CHECK_FINAL"
        echo "查看占用进程:"
        ps -p $PORT_CHECK_FINAL -o pid,comm,args 2>/dev/null || true
        exit 1
    fi
    
    # 检查状态
    echo ""
    echo "当前 PM2 状态:"
    sudo -u ubuntu pm2 list
    
    # 检查 frontend 状态
    FRONTEND_STATUS=$(sudo -u ubuntu pm2 list | grep frontend | awk '{print $10}' || echo "")
    if [ "$FRONTEND_STATUS" = "online" ]; then
        echo ""
        echo "✅ Frontend 服务已成功启动！"
    else
        echo ""
        echo "❌ Frontend 服务启动失败，状态: $FRONTEND_STATUS"
        echo "查看错误日志:"
        sudo -u ubuntu pm2 logs frontend --err --lines 20 --nostream 2>&1 | tail -20
    fi
    
    # 保存配置
    sudo -u ubuntu pm2 save
else
    echo "❌ ecosystem.config.js 不存在"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "如果 frontend 仍然失败，请检查："
echo "1. 前端构建是否完整"
echo "2. ecosystem.config.js 配置是否正确"
echo "3. 查看详细日志: sudo -u ubuntu pm2 logs frontend --lines 100"

