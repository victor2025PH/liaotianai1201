#!/bin/bash
# ============================================================
# 重启前端服务并验证
# ============================================================

echo "=========================================="
echo "🔄 重启前端服务并验证"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

# 1. 验证构建产物存在
echo "[1/4] 验证构建产物..."
echo "----------------------------------------"
if [ -f "$FRONTEND_DIR/.next/standalone/server.js" ]; then
    echo "✅ server.js 存在"
    ls -lh "$FRONTEND_DIR/.next/standalone/server.js"
else
    echo "❌ server.js 不存在！"
    echo "请先运行: bash scripts/server/fix-frontend-build-missing.sh"
    exit 1
fi
echo ""

# 2. 停止旧的 frontend 进程
echo "[2/4] 停止旧的 frontend 进程..."
echo "----------------------------------------"
sudo -u ubuntu pm2 stop frontend 2>/dev/null || true
sudo -u ubuntu pm2 delete frontend 2>/dev/null || true
echo "✅ 已清理旧的 frontend 进程"
echo ""

# 3. 重启 frontend
echo "[3/4] 重启 frontend 服务..."
echo "----------------------------------------"
cd "$PROJECT_DIR" || exit 1

# 确保端口 3000 空闲
PORT_3000=$(sudo lsof -t -i:3000 2>/dev/null || echo "")
if [ -n "$PORT_3000" ]; then
    echo "⚠️  端口 3000 被占用，清理中..."
    sudo kill -9 $PORT_3000 2>/dev/null || true
    sudo fuser -k -9 3000/tcp 2>/dev/null || true
    sleep 2
fi

# 启动 frontend
echo "启动 frontend..."
sudo -u ubuntu pm2 start ecosystem.config.js --only frontend
sleep 5
echo ""

# 4. 验证服务状态
echo "[4/4] 验证服务状态..."
echo "----------------------------------------"
sudo -u ubuntu pm2 list

FRONTEND_STATUS=$(sudo -u ubuntu pm2 list | grep frontend | awk '{print $10}' || echo "")
if [ "$FRONTEND_STATUS" = "online" ]; then
    echo ""
    echo "✅ Frontend 服务已成功启动！"
    
    # 测试端口
    sleep 2
    PORT_CHECK=$(sudo ss -tlnp 2>/dev/null | grep ":3000 " || echo "")
    if [ -n "$PORT_CHECK" ]; then
        echo "✅ 端口 3000 正在监听"
    else
        echo "⚠️  端口 3000 未监听"
    fi
    
    # 保存配置
    sudo -u ubuntu pm2 save
else
    echo ""
    echo "❌ Frontend 服务启动失败，状态: $FRONTEND_STATUS"
    echo ""
    echo "查看错误日志:"
    sudo -u ubuntu pm2 logs frontend --err --lines 30 --nostream 2>&1 | tail -30
    echo ""
    echo "查看完整日志:"
    sudo -u ubuntu pm2 logs frontend --lines 50 --nostream 2>&1 | tail -50
fi

echo ""
echo "=========================================="
echo "✅ 验证完成"
echo "=========================================="

