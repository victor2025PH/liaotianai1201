#!/bin/bash
# ============================================================
# 完整迁移到 Systemd：停止 PM2，部署 Systemd，重启服务
# ============================================================

set +e

echo "=========================================="
echo "🚀 完整迁移到 Systemd 服务"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"
BACKEND_SERVICE="luckyred-api"
FRONTEND_SERVICE="liaotian-frontend"

# 1. 停止并删除 PM2 进程
echo "[1/8] 停止并删除 PM2 进程..."
echo "----------------------------------------"
if command -v pm2 &> /dev/null; then
    # 检查是否有 frontend 进程
    PM2_FRONTEND=$(pm2 list | grep frontend || true)
    if [ -n "$PM2_FRONTEND" ]; then
        echo "发现 PM2 frontend 进程，正在停止..."
        pm2 stop frontend 2>/dev/null || true
        pm2 delete frontend 2>/dev/null || true
        echo "✅ PM2 frontend 已停止并删除"
    else
        echo "✅ 未发现 PM2 frontend 进程"
    fi
    
    # 检查是否有 backend 进程（虽然应该没有）
    PM2_BACKEND=$(pm2 list | grep backend || true)
    if [ -n "$PM2_BACKEND" ]; then
        echo "发现 PM2 backend 进程，正在停止..."
        pm2 stop backend 2>/dev/null || true
        pm2 delete backend 2>/dev/null || true
        echo "✅ PM2 backend 已停止并删除"
    fi
    
    # 清除 PM2 开机自启配置
    pm2 unstartup 2>/dev/null || true
    pm2 save --force 2>/dev/null || true
    echo "✅ PM2 配置已清除"
else
    echo "⚠️  PM2 未安装，跳过"
fi
echo ""

# 2. 停止现有的 systemd 服务
echo "[2/8] 停止现有的 systemd 服务..."
echo "----------------------------------------"
if systemctl is-active --quiet "$BACKEND_SERVICE" 2>/dev/null; then
    echo "停止 $BACKEND_SERVICE..."
    systemctl stop "$BACKEND_SERVICE"
    echo "✅ $BACKEND_SERVICE 已停止"
else
    echo "✅ $BACKEND_SERVICE 未运行"
fi

if systemctl is-active --quiet "$FRONTEND_SERVICE" 2>/dev/null; then
    echo "停止 $FRONTEND_SERVICE..."
    systemctl stop "$FRONTEND_SERVICE"
    echo "✅ $FRONTEND_SERVICE 已停止"
else
    echo "✅ $FRONTEND_SERVICE 未运行"
fi
echo ""

# 3. 清理端口占用
echo "[3/8] 清理端口占用..."
echo "----------------------------------------"
# 清理端口 8000
PORT_8000_PID=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$PORT_8000_PID" ]; then
    echo "发现端口 8000 被占用 (PID: $PORT_8000_PID)，正在清理..."
    kill -9 $PORT_8000_PID 2>/dev/null || true
    sleep 1
    echo "✅ 端口 8000 已释放"
else
    echo "✅ 端口 8000 未被占用"
fi

# 清理端口 3000
PORT_3000_PID=$(lsof -ti:3000 2>/dev/null || true)
if [ -n "$PORT_3000_PID" ]; then
    echo "发现端口 3000 被占用 (PID: $PORT_3000_PID)，正在清理..."
    kill -9 $PORT_3000_PID 2>/dev/null || true
    sleep 1
    echo "✅ 端口 3000 已释放"
else
    echo "✅ 端口 3000 未被占用"
fi
echo ""

# 4. 检查并构建前端（如果需要）
echo "[4/8] 检查并构建前端..."
echo "----------------------------------------"
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ 前端目录不存在: $FRONTEND_DIR"
    exit 1
fi

cd "$FRONTEND_DIR" || exit 1

# 检查是否需要构建
if [ ! -d ".next/standalone" ]; then
    echo "未发现 standalone 构建，开始构建..."
    echo "这可能需要几分钟，请耐心等待..."
    
    # 检查 node_modules
    if [ ! -d "node_modules" ]; then
        echo "安装依赖..."
        npm install
    fi
    
    # 构建
    npm run build
    
    if [ ! -d ".next/standalone" ]; then
        echo "❌ 构建失败，standalone 目录不存在"
        echo "请检查构建日志"
        exit 1
    fi
    echo "✅ 前端构建完成"
else
    echo "✅ standalone 构建已存在"
fi
cd "$PROJECT_DIR"
echo ""

# 5. 部署 systemd 服务配置
echo "[5/8] 部署 systemd 服务配置..."
echo "----------------------------------------"
# 检查服务文件是否存在
if [ ! -f "$PROJECT_DIR/deploy/systemd/liaotian-frontend.service" ]; then
    echo "❌ 前端服务文件不存在: $PROJECT_DIR/deploy/systemd/liaotian-frontend.service"
    exit 1
fi

# 复制前端服务文件
cp "$PROJECT_DIR/deploy/systemd/liaotian-frontend.service" "/etc/systemd/system/$FRONTEND_SERVICE.service"
echo "✅ 前端服务文件已部署"

# 检查后端服务文件（应该已存在）
if [ ! -f "/etc/systemd/system/$BACKEND_SERVICE.service" ]; then
    if [ -f "$PROJECT_DIR/deploy/systemd/$BACKEND_SERVICE.service" ]; then
        cp "$PROJECT_DIR/deploy/systemd/$BACKEND_SERVICE.service" "/etc/systemd/system/$BACKEND_SERVICE.service"
        echo "✅ 后端服务文件已部署"
    else
        echo "⚠️  后端服务文件不存在，但可能已配置"
    fi
else
    echo "✅ 后端服务文件已存在"
fi

# 重新加载 systemd
systemctl daemon-reload
echo "✅ systemd 配置已重新加载"
echo ""

# 6. 启动后端服务
echo "[6/8] 启动后端服务..."
echo "----------------------------------------"
systemctl start "$BACKEND_SERVICE"
sleep 3

if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    echo "✅ 后端服务已启动"
    systemctl enable "$BACKEND_SERVICE" 2>/dev/null || true
    echo "✅ 后端服务已设置开机自启"
else
    echo "❌ 后端服务启动失败"
    systemctl status "$BACKEND_SERVICE" --no-pager -l | head -20
    exit 1
fi
echo ""

# 7. 启动前端服务
echo "[7/8] 启动前端服务..."
echo "----------------------------------------"
systemctl start "$FRONTEND_SERVICE"
sleep 5

if systemctl is-active --quiet "$FRONTEND_SERVICE"; then
    echo "✅ 前端服务已启动"
    systemctl enable "$FRONTEND_SERVICE" 2>/dev/null || true
    echo "✅ 前端服务已设置开机自启"
else
    echo "❌ 前端服务启动失败"
    systemctl status "$FRONTEND_SERVICE" --no-pager -l | head -20
    echo ""
    echo "查看详细日志:"
    journalctl -u "$FRONTEND_SERVICE" -n 50 --no-pager | tail -30
    exit 1
fi
echo ""

# 8. 验证服务状态
echo "[8/8] 验证服务状态..."
echo "----------------------------------------"
sleep 3

# 检查端口监听
echo "检查端口监听..."
PORT_8000=$(lsof -ti:8000 2>/dev/null || true)
PORT_3000=$(lsof -ti:3000 2>/dev/null || true)

if [ -n "$PORT_8000" ]; then
    echo "✅ 端口 8000 正在监听 (PID: $PORT_8000)"
else
    echo "❌ 端口 8000 未监听"
fi

if [ -n "$PORT_3000" ]; then
    echo "✅ 端口 3000 正在监听 (PID: $PORT_3000)"
else
    echo "❌ 端口 3000 未监听"
fi
echo ""

# 检查服务状态
echo "检查服务状态..."
BACKEND_STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "inactive")
FRONTEND_STATUS=$(systemctl is-active "$FRONTEND_SERVICE" 2>/dev/null || echo "inactive")

echo "后端服务 ($BACKEND_SERVICE): $BACKEND_STATUS"
echo "前端服务 ($FRONTEND_SERVICE): $FRONTEND_STATUS"
echo ""

# 测试服务响应
echo "测试服务响应..."
# 后端健康检查
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    echo "✅ 后端健康检查正常 (HTTP 200)"
else
    echo "⚠️  后端健康检查异常 (HTTP $BACKEND_HEALTH)"
fi

# 前端测试
FRONTEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/ 2>/dev/null || echo "000")
if [ "$FRONTEND_TEST" = "200" ] || [ "$FRONTEND_TEST" = "404" ]; then
    echo "✅ 前端服务响应正常 (HTTP $FRONTEND_TEST)"
else
    echo "⚠️  前端服务响应异常 (HTTP $FRONTEND_TEST)"
fi

# 前端登录页面测试
FRONTEND_LOGIN=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/login 2>/dev/null || echo "000")
if [ "$FRONTEND_LOGIN" = "200" ]; then
    echo "✅ 前端登录页面正常 (HTTP 200)"
else
    echo "⚠️  前端登录页面异常 (HTTP $FRONTEND_LOGIN)"
fi
echo ""

# 最终总结
echo "=========================================="
echo "✅ 迁移完成"
echo "=========================================="
echo ""
echo "服务状态:"
echo "  后端: $BACKEND_STATUS"
echo "  前端: $FRONTEND_STATUS"
echo ""
echo "管理命令:"
echo "  查看后端状态: sudo systemctl status $BACKEND_SERVICE"
echo "  查看前端状态: sudo systemctl status $FRONTEND_SERVICE"
echo "  查看后端日志: sudo journalctl -u $BACKEND_SERVICE -f"
echo "  查看前端日志: sudo journalctl -u $FRONTEND_SERVICE -f"
echo ""
echo "重启服务:"
echo "  sudo systemctl restart $BACKEND_SERVICE"
echo "  sudo systemctl restart $FRONTEND_SERVICE"
echo ""

