#!/bin/bash
# ============================================================
# 修复 PM2 frontend errored 状态
# ============================================================

echo "=========================================="
echo "🔧 修复 PM2 Frontend Errored 状态"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

# 1. 查看前端错误日志
echo "[1/5] 查看 PM2 frontend 错误日志..."
echo "----------------------------------------"
sudo -u ubuntu pm2 logs frontend --err --lines 50 --nostream 2>&1 | tail -30
echo ""

# 2. 停止并删除 errored 的 frontend 进程
echo "[2/5] 停止并删除 errored 的 frontend 进程..."
echo "----------------------------------------"
sudo -u ubuntu pm2 stop frontend 2>/dev/null || true
sudo -u ubuntu pm2 delete frontend 2>/dev/null || true
echo "✅ 已清理旧的 frontend 进程"
echo ""

# 3. 检查是否有独立的 next-server 进程在运行
echo "[3/5] 检查独立的 next-server 进程..."
echo "----------------------------------------"
NEXT_PID=$(pgrep -f "next-server" | head -1 || echo "")
if [ -n "$NEXT_PID" ]; then
    echo "⚠️  发现独立的 next-server 进程 (PID: $NEXT_PID)"
    echo "  这可能是导致 PM2 frontend 失败的原因"
    echo "  正在停止该进程..."
    sudo kill -9 $NEXT_PID 2>/dev/null || true
    sleep 2
    echo "✅ 已停止独立进程"
else
    echo "✅ 未发现独立的 next-server 进程"
fi
echo ""

# 4. 检查前端构建产物
echo "[4/5] 检查前端构建产物..."
echo "----------------------------------------"
cd "$FRONTEND_DIR" || exit 1

STANDALONE_SERVER=""
if [ -f ".next/standalone/server.js" ]; then
    STANDALONE_SERVER=".next/standalone/server.js"
elif [ -d ".next/standalone" ]; then
    STANDALONE_SERVER=$(find .next/standalone -name "server.js" 2>/dev/null | head -1 || echo "")
fi

if [ -z "$STANDALONE_SERVER" ] || [ ! -f "$STANDALONE_SERVER" ]; then
    echo "❌ 前端 standalone 构建产物不存在！"
    echo "  需要重新构建前端"
    echo "  执行: cd $FRONTEND_DIR && npm run build"
    exit 1
fi

echo "✅ 找到 standalone server: $STANDALONE_SERVER"
ls -lh "$STANDALONE_SERVER"
echo ""

# 5. 检查 ecosystem.config.js 并重启 frontend
echo "[5/5] 重启 PM2 frontend 服务..."
echo "----------------------------------------"
cd "$PROJECT_DIR" || exit 1

if [ -f "ecosystem.config.js" ]; then
    echo "使用 ecosystem.config.js 启动服务..."
    sudo -u ubuntu pm2 start ecosystem.config.js --only frontend
    sleep 5
    
    # 检查状态
    FRONTEND_STATUS=$(sudo -u ubuntu pm2 list | grep frontend | awk '{print $10}' || echo "")
    if [ "$FRONTEND_STATUS" = "online" ]; then
        echo "✅ Frontend 服务已成功启动"
    else
        echo "❌ Frontend 服务启动失败，状态: $FRONTEND_STATUS"
        echo ""
        echo "查看最新错误日志:"
        sudo -u ubuntu pm2 logs frontend --err --lines 20 --nostream 2>&1 | tail -20
    fi
else
    echo "❌ ecosystem.config.js 不存在"
    echo "尝试手动启动 frontend..."
    cd "$FRONTEND_DIR" || exit 1
    sudo -u ubuntu pm2 start .next/standalone/server.js --name frontend
    sleep 5
    
    FRONTEND_STATUS=$(sudo -u ubuntu pm2 list | grep frontend | awk '{print $10}' || echo "")
    if [ "$FRONTEND_STATUS" = "online" ]; then
        echo "✅ Frontend 服务已成功启动"
    else
        echo "❌ Frontend 服务启动失败"
    fi
fi

echo ""
echo "=========================================="
echo "📊 当前 PM2 状态"
echo "=========================================="
sudo -u ubuntu pm2 list
echo ""

# 保存 PM2 配置
sudo -u ubuntu pm2 save

echo "✅ 修复完成！"
echo ""
echo "如果问题仍然存在，请检查："
echo "1. 前端构建是否完整: ls -la $FRONTEND_DIR/.next/standalone"
echo "2. 静态资源是否存在: ls -la $FRONTEND_DIR/.next/static"
echo "3. 查看详细日志: sudo -u ubuntu pm2 logs frontend --lines 100"

