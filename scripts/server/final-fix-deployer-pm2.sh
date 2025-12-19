#!/bin/bash
# ============================================================
# 最终修复：停止 deployer 用户的 PM2，启动 ubuntu 用户的 PM2
# ============================================================

echo "=========================================="
echo "🔧 最终修复：解决 deployer 用户 PM2 冲突"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 1. 确保 deployer 用户的 PM2 已停止
echo "[1/5] 确保 deployer 用户的 PM2 已停止..."
echo "----------------------------------------"
if sudo -u deployer pm2 list 2>/dev/null | grep -q "frontend\|backend"; then
    echo "停止 deployer 用户的 PM2 进程..."
    sudo -u deployer pm2 stop all 2>/dev/null || true
    sudo -u deployer pm2 delete all 2>/dev/null || true
    sudo -u deployer pm2 kill 2>/dev/null || true
    echo "✅ deployer 用户的 PM2 已停止"
else
    echo "✅ deployer 用户的 PM2 已停止或不存在"
fi
echo ""

# 2. 确保端口 3000 和 8000 已释放
echo "[2/5] 确保端口已释放..."
echo "----------------------------------------"
# 杀掉所有占用端口的进程（包括所有用户）
sudo lsof -t -i:3000 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
sudo lsof -t -i:8000 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
sudo fuser -k -9 3000/tcp 2>/dev/null || true
sudo fuser -k -9 8000/tcp 2>/dev/null || true
sudo pkill -9 -f "next-server" 2>/dev/null || true
sleep 3

# 验证端口已释放
PORT_3000=$(sudo lsof -t -i:3000 2>/dev/null || echo "")
PORT_8000=$(sudo lsof -t -i:8000 2>/dev/null || echo "")
if [ -z "$PORT_3000" ] && [ -z "$PORT_8000" ]; then
    echo "✅ 端口 3000 和 8000 已释放"
else
    echo "⚠️  端口仍被占用，强制清理..."
    [ -n "$PORT_3000" ] && sudo kill -9 $PORT_3000 2>/dev/null || true
    [ -n "$PORT_8000" ] && sudo kill -9 $PORT_8000 2>/dev/null || true
    sleep 2
fi
echo ""

# 3. 停止 ubuntu 用户的 PM2（如果有）
echo "[3/5] 清理 ubuntu 用户的 PM2..."
echo "----------------------------------------"
sudo -u ubuntu pm2 stop all 2>/dev/null || true
sudo -u ubuntu pm2 delete all 2>/dev/null || true
echo "✅ ubuntu 用户的 PM2 已清理"
echo ""

# 4. 等待确保所有进程完全停止
echo "[4/5] 等待进程完全停止..."
echo "----------------------------------------"
sleep 5

# 最终验证端口
FINAL_CHECK_3000=$(sudo ss -tlnp 2>/dev/null | grep ":3000 " || echo "")
FINAL_CHECK_8000=$(sudo ss -tlnp 2>/dev/null | grep ":8000 " || echo "")
if [ -n "$FINAL_CHECK_3000" ] || [ -n "$FINAL_CHECK_8000" ]; then
    echo "⚠️  警告：端口仍被占用"
    [ -n "$FINAL_CHECK_3000" ] && echo "端口 3000: $FINAL_CHECK_3000"
    [ -n "$FINAL_CHECK_8000" ] && echo "端口 8000: $FINAL_CHECK_8000"
    echo "继续执行，但可能仍有冲突..."
else
    echo "✅ 端口已确认释放"
fi
echo ""

# 5. 启动 ubuntu 用户的 PM2 服务
echo "[5/5] 启动 ubuntu 用户的 PM2 服务..."
echo "----------------------------------------"
cd "$PROJECT_DIR" || exit 1

if [ -f "ecosystem.config.js" ]; then
    echo "使用 ecosystem.config.js 启动服务..."
    sudo -u ubuntu pm2 start ecosystem.config.js
    sleep 5
    
    echo ""
    echo "当前 PM2 状态:"
    sudo -u ubuntu pm2 list
    
    # 检查服务状态
    BACKEND_STATUS=$(sudo -u ubuntu pm2 list | grep backend | awk '{print $10}' || echo "")
    FRONTEND_STATUS=$(sudo -u ubuntu pm2 list | grep frontend | awk '{print $10}' || echo "")
    
    echo ""
    if [ "$BACKEND_STATUS" = "online" ]; then
        echo "✅ Backend 服务: 运行正常"
    else
        echo "❌ Backend 服务: 状态异常 ($BACKEND_STATUS)"
    fi
    
    if [ "$FRONTEND_STATUS" = "online" ]; then
        echo "✅ Frontend 服务: 运行正常"
        
        # 验证端口
        sleep 2
        PORT_CHECK=$(sudo ss -tlnp 2>/dev/null | grep ":3000 " || echo "")
        if [ -n "$PORT_CHECK" ]; then
            echo "✅ 端口 3000 正在监听"
            echo "$PORT_CHECK"
        fi
    else
        echo "❌ Frontend 服务: 状态异常 ($FRONTEND_STATUS)"
        echo ""
        echo "查看错误日志:"
        sudo -u ubuntu pm2 logs frontend --err --lines 20 --nostream 2>&1 | tail -20
    fi
    
    # 保存配置
    sudo -u ubuntu pm2 save
    echo ""
    echo "✅ PM2 配置已保存"
else
    echo "❌ ecosystem.config.js 不存在"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "重要提示："
echo "1. deployer 用户的 PM2 已停止，但可能设置了开机自启"
echo "2. 如果问题再次出现，检查 deployer 用户的 PM2 开机自启："
echo "   sudo -u deployer pm2 startup"
echo "   sudo -u deployer pm2 unstartup  # 禁用开机自启"
echo ""
echo "3. 当前服务状态："
sudo -u ubuntu pm2 list

