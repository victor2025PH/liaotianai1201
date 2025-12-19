#!/bin/bash
# ============================================================
# 综合修复：解决所有问题（端口冲突 + 虚拟环境）
# ============================================================

echo "=========================================="
echo "🔧 综合修复：解决所有问题"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

# 1. 彻底停止所有相关进程
echo "[1/6] 彻底停止所有相关进程..."
echo "----------------------------------------"
# 停止所有用户的 PM2
sudo -u deployer pm2 kill 2>/dev/null || true
sudo -u ubuntu pm2 kill 2>/dev/null || true
sudo -u deployer pm2 stop all 2>/dev/null || true
sudo -u ubuntu pm2 stop all 2>/dev/null || true
sudo -u deployer pm2 delete all 2>/dev/null || true
sudo -u ubuntu pm2 delete all 2>/dev/null || true

# 杀掉所有占用端口的进程
echo "清理端口 3000 和 8000..."
sudo lsof -t -i:3000 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
sudo lsof -t -i:8000 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
sudo fuser -k -9 3000/tcp 2>/dev/null || true
sudo fuser -k -9 8000/tcp 2>/dev/null || true
sudo pkill -9 -f "next-server" 2>/dev/null || true
sudo pkill -9 -f "uvicorn" 2>/dev/null || true

sleep 5
echo "✅ 所有进程已停止"
echo ""

# 2. 验证端口已释放（使用强力清理脚本）
echo "[2/6] 验证端口已释放..."
echo "----------------------------------------"
# 使用专门的脚本来彻底清理
if [ -f "$PROJECT_DIR/scripts/server/kill-next-server-completely.sh" ]; then
    echo "使用强力清理脚本..."
    bash "$PROJECT_DIR/scripts/server/kill-next-server-completely.sh"
    CLEANUP_RESULT=$?
    if [ $CLEANUP_RESULT -ne 0 ]; then
        echo "⚠️  清理脚本执行失败，但继续尝试..."
    fi
else
    # 备用清理方法
    PORT_3000=$(sudo ss -tlnp 2>/dev/null | grep ":3000 " || echo "")
    PORT_8000=$(sudo ss -tlnp 2>/dev/null | grep ":8000 " || echo "")
    if [ -n "$PORT_3000" ] || [ -n "$PORT_8000" ]; then
        echo "⚠️  警告：端口仍被占用"
        [ -n "$PORT_3000" ] && echo "端口 3000: $PORT_3000"
        [ -n "$PORT_8000" ] && echo "端口 8000: $PORT_8000"
        echo "再次强制清理..."
        sudo lsof -t -i:3000 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
        sudo lsof -t -i:8000 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
        sleep 3
    else
        echo "✅ 端口已确认释放"
    fi
fi
echo ""

# 3. 检查并修复后端虚拟环境
echo "[3/6] 检查并修复后端虚拟环境..."
echo "----------------------------------------"
cd "$BACKEND_DIR" || exit 1

if [ ! -f "venv/bin/uvicorn" ]; then
    echo "⚠️  虚拟环境不存在或 uvicorn 缺失，正在重建..."
    rm -rf venv
    python3 -m venv venv
    . venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    echo "✅ 虚拟环境已重建"
else
    echo "✅ 虚拟环境存在"
    . venv/bin/activate
    # 验证 uvicorn 存在
    if ! command -v uvicorn >/dev/null 2>&1; then
        echo "⚠️  uvicorn 未安装，正在安装..."
        pip install uvicorn --quiet
    fi
fi
cd "$PROJECT_DIR"
echo ""

# 4. 检查前端构建产物
echo "[4/6] 检查前端构建产物..."
echo "----------------------------------------"
cd "$FRONTEND_DIR" || exit 1

if [ ! -f ".next/standalone/server.js" ]; then
    echo "⚠️  前端构建产物不存在，需要重新构建"
    echo "   这可能需要几分钟，请耐心等待..."
    rm -rf .next
    rm -f .next/lock
    export NODE_OPTIONS="--max-old-space-size=1536"
    npm install --prefer-offline --no-audit
    npm run build
    
    # 处理静态资源
    if [ -d ".next/standalone" ]; then
        mkdir -p .next/standalone/.next/static
        mkdir -p .next/standalone/.next/server
        cp -r .next/static/* .next/standalone/.next/static/ 2>/dev/null || true
        if [ -d "public" ]; then cp -r public .next/standalone/ 2>/dev/null || true; fi
        cp -r .next/server/* .next/standalone/.next/server/ 2>/dev/null || true
    fi
    echo "✅ 前端已重新构建"
else
    echo "✅ 前端构建产物存在"
fi
cd "$PROJECT_DIR"
echo ""

# 5. 禁用 deployer 用户的 PM2 开机自启
echo "[5/6] 禁用 deployer 用户的 PM2 开机自启..."
echo "----------------------------------------"
# 执行 PM2 提供的卸载命令
UNSTARTUP_CMD=$(sudo -u deployer pm2 unstartup 2>/dev/null | grep "sudo env" || echo "")
if [ -n "$UNSTARTUP_CMD" ]; then
    echo "执行卸载命令..."
    eval "$UNSTARTUP_CMD" 2>/dev/null || true
    echo "✅ deployer 用户的 PM2 开机自启已禁用"
else
    echo "✅ deployer 用户的 PM2 开机自启未设置或已禁用"
fi
echo ""

# 6. 启动 ubuntu 用户的 PM2 服务
echo "[6/6] 启动 ubuntu 用户的 PM2 服务..."
echo "----------------------------------------"
cd "$PROJECT_DIR" || exit 1

# 再次确认端口空闲
sleep 2
FINAL_PORT_CHECK=$(sudo ss -tlnp 2>/dev/null | grep -E ":(3000|8000) " || echo "")
if [ -n "$FINAL_PORT_CHECK" ]; then
    echo "❌ 端口仍被占用，无法启动服务"
    echo "$FINAL_PORT_CHECK"
    exit 1
fi

if [ -f "ecosystem.config.js" ]; then
    echo "启动所有服务..."
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
        echo "查看错误日志:"
        sudo -u ubuntu pm2 logs backend --err --lines 10 --nostream 2>&1 | tail -10
    fi
    
    if [ "$FRONTEND_STATUS" = "online" ]; then
        echo "✅ Frontend 服务: 运行正常"
        
        # 验证端口
        sleep 2
        PORT_CHECK=$(sudo ss -tlnp 2>/dev/null | grep ":3000 " || echo "")
        if [ -n "$PORT_CHECK" ]; then
            echo "✅ 端口 3000 正在监听"
        else
            echo "⚠️  端口 3000 未监听"
        fi
    else
        echo "❌ Frontend 服务: 状态异常 ($FRONTEND_STATUS)"
        echo "查看错误日志:"
        sudo -u ubuntu pm2 logs frontend --err --lines 10 --nostream 2>&1 | tail -10
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
echo "服务状态："
sudo -u ubuntu pm2 list
echo ""
echo "端口监听状态："
sudo ss -tlnp | grep -E ":(3000|8000) " || echo "端口未监听"

