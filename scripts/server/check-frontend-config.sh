#!/bin/bash
# ============================================================
# 检查前端服务配置（systemd 或 PM2）
# ============================================================

set +e

echo "=========================================="
echo "🔍 检查前端服务配置"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

# 1. 检查 systemd 服务
echo "[1/4] 检查 systemd 服务..."
echo "----------------------------------------"
SYSTEMD_SERVICES=("liaotian-frontend" "smart-tg-frontend")
FOUND_SYSTEMD=false

for service in "${SYSTEMD_SERVICES[@]}"; do
    if systemctl list-unit-files | grep -q "^${service}.service"; then
        echo "✅ 发现 systemd 服务: $service"
        FOUND_SYSTEMD=true
        
        # 检查服务状态
        if systemctl is-active --quiet "$service"; then
            echo "   状态: 运行中"
        else
            echo "   状态: 未运行"
        fi
        
        # 显示服务文件路径
        SERVICE_FILE=$(systemctl show "$service" -p FragmentPath --value 2>/dev/null || echo "")
        if [ -n "$SERVICE_FILE" ]; then
            echo "   配置文件: $SERVICE_FILE"
        fi
    fi
done

if [ "$FOUND_SYSTEMD" = false ]; then
    echo "⚠️  未发现 systemd 前端服务"
fi
echo ""

# 2. 检查 PM2 进程
echo "[2/4] 检查 PM2 进程..."
echo "----------------------------------------"
if command -v pm2 &> /dev/null; then
    PM2_FRONTEND=$(pm2 list | grep frontend || true)
    if [ -n "$PM2_FRONTEND" ]; then
        echo "✅ 发现 PM2 frontend 进程:"
        pm2 list | grep -A 1 frontend
        FOUND_PM2=true
    else
        echo "⚠️  未发现 PM2 frontend 进程"
        FOUND_PM2=false
    fi
else
    echo "⚠️  PM2 未安装"
    FOUND_PM2=false
fi
echo ""

# 3. 检查端口占用
echo "[3/4] 检查端口 3000 占用..."
echo "----------------------------------------"
PORT_PID=$(sudo lsof -ti:3000 2>/dev/null || true)
if [ -n "$PORT_PID" ]; then
    echo "✅ 端口 3000 正在监听"
    echo "进程信息:"
    ps -fp $PORT_PID 2>/dev/null | head -5
    echo ""
    
    # 判断是 systemd 还是 PM2
    PROCESS_CMD=$(ps -fp $PORT_PID -o cmd= 2>/dev/null || echo "")
    if echo "$PROCESS_CMD" | grep -q "standalone/server.js"; then
        echo "✅ 使用 Next.js standalone 模式（systemd 服务）"
        CURRENT_METHOD="systemd"
    elif echo "$PROCESS_CMD" | grep -q "npm.*start\|next-server"; then
        echo "✅ 使用 npm start 模式（可能是 PM2 或手动启动）"
        CURRENT_METHOD="npm"
    else
        echo "⚠️  未知的启动方式"
        CURRENT_METHOD="unknown"
    fi
else
    echo "❌ 端口 3000 未监听"
    CURRENT_METHOD="none"
fi
echo ""

# 4. 检查构建文件
echo "[4/4] 检查前端构建文件..."
echo "----------------------------------------"
if [ -d "$FRONTEND_DIR/.next/standalone" ]; then
    echo "✅ 发现 standalone 构建文件（systemd 需要）"
    HAS_STANDALONE=true
else
    echo "⚠️  未发现 standalone 构建文件"
    HAS_STANDALONE=false
fi

if [ -d "$FRONTEND_DIR/.next" ]; then
    echo "✅ 发现 .next 构建目录"
else
    echo "⚠️  未发现 .next 构建目录（需要运行 npm run build）"
fi
echo ""

# 总结和建议
echo "=========================================="
echo "📋 配置总结和建议"
echo "=========================================="
echo ""

if [ "$FOUND_SYSTEMD" = true ] && [ "$CURRENT_METHOD" = "systemd" ]; then
    echo "✅ 当前使用: systemd 服务（推荐）"
    echo ""
    echo "管理命令:"
    echo "  启动: sudo systemctl start liaotian-frontend"
    echo "  停止: sudo systemctl stop liaotian-frontend"
    echo "  重启: sudo systemctl restart liaotian-frontend"
    echo "  状态: sudo systemctl status liaotian-frontend"
    echo "  日志: sudo journalctl -u liaotian-frontend -n 50 --no-pager"
elif [ "$FOUND_PM2" = true ] && [ "$CURRENT_METHOD" = "npm" ]; then
    echo "✅ 当前使用: PM2（临时方案）"
    echo ""
    echo "管理命令:"
    echo "  启动: pm2 start ecosystem.config.js"
    echo "  停止: pm2 stop frontend"
    echo "  重启: pm2 restart frontend"
    echo "  状态: pm2 list"
    echo "  日志: pm2 logs frontend"
    echo ""
    echo "⚠️  建议: 如果 systemd 服务存在，应该使用 systemd 而不是 PM2"
elif [ "$CURRENT_METHOD" = "none" ]; then
    echo "❌ 前端服务未运行"
    echo ""
    if [ "$FOUND_SYSTEMD" = true ]; then
        echo "建议: 使用 systemd 服务启动"
        echo "  1. 确保已构建: cd $FRONTEND_DIR && npm run build"
        echo "  2. 启动服务: sudo systemctl start liaotian-frontend"
    elif [ "$FOUND_PM2" = true ]; then
        echo "建议: 使用 PM2 启动"
        echo "  cd $FRONTEND_DIR"
        echo "  pm2 start ecosystem.config.js"
    else
        echo "建议: 先配置 systemd 服务或使用 PM2"
        echo "  方式 1 (systemd): sudo bash $PROJECT_DIR/scripts/server/deploy-systemd.sh"
        echo "  方式 2 (PM2): cd $FRONTEND_DIR && pm2 start ecosystem.config.js"
    fi
else
    echo "⚠️  配置不一致，需要检查"
    echo ""
    if [ "$FOUND_SYSTEMD" = true ]; then
        echo "发现 systemd 服务但未运行，建议:"
        echo "  sudo systemctl start liaotian-frontend"
    fi
fi
echo ""

