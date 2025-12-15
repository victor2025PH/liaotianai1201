#!/bin/bash
# ============================================================
# 完整修复服务：清理端口、修复配置、重启服务
# ============================================================

set +e

echo "=========================================="
echo "🔧 完整修复服务"
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

# 1. 停止所有服务
echo "[1/7] 停止所有服务..."
echo "----------------------------------------"
systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
systemctl stop "$FRONTEND_SERVICE" 2>/dev/null || true
sleep 3
echo "✅ 服务已停止"
echo ""

# 2. 强制清理端口占用
echo "[2/7] 强制清理端口占用..."
echo "----------------------------------------"
# 清理端口 8000
PORT_8000_PIDS=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$PORT_8000_PIDS" ]; then
    echo "发现端口 8000 被占用，正在清理..."
    for pid in $PORT_8000_PIDS; do
        echo "  终止进程 $pid..."
        kill -9 $pid 2>/dev/null || true
    done
    sleep 2
fi

# 清理端口 3000
PORT_3000_PIDS=$(lsof -ti:3000 2>/dev/null || true)
if [ -n "$PORT_3000_PIDS" ]; then
    echo "发现端口 3000 被占用，正在清理..."
    for pid in $PORT_3000_PIDS; do
        echo "  终止进程 $pid..."
        kill -9 $pid 2>/dev/null || true
    done
    sleep 2
fi

# 验证端口已释放
FINAL_8000=$(lsof -ti:8000 2>/dev/null || true)
FINAL_3000=$(lsof -ti:3000 2>/dev/null || true)

if [ -z "$FINAL_8000" ] && [ -z "$FINAL_3000" ]; then
    echo "✅ 所有端口已释放"
else
    echo "⚠️  仍有端口被占用，再次强制清理..."
    [ -n "$FINAL_8000" ] && kill -9 $FINAL_8000 2>/dev/null || true
    [ -n "$FINAL_3000" ] && kill -9 $FINAL_3000 2>/dev/null || true
    sleep 2
fi
echo ""

# 3. 检查前端 standalone 构建
echo "[3/7] 检查前端 standalone 构建..."
echo "----------------------------------------"
if [ ! -d "$FRONTEND_DIR/.next/standalone" ]; then
    echo "❌ standalone 目录不存在，需要重新构建"
    echo "请先运行: cd $FRONTEND_DIR && npm run build"
    exit 1
fi

# 检查 server.js 是否存在
if [ ! -f "$FRONTEND_DIR/.next/standalone/server.js" ]; then
    echo "❌ standalone/server.js 不存在"
    exit 1
fi

echo "✅ standalone 构建存在"
echo ""

# 4. 修复前端服务配置
echo "[4/7] 修复前端服务配置..."
echo "----------------------------------------"
cat > /etc/systemd/system/$FRONTEND_SERVICE.service <<EOF
[Unit]
Description=Liaotian Next.js Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$FRONTEND_DIR/.next/standalone
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=NODE_OPTIONS=--max-old-space-size=1024
# 使用绝对路径，工作目录设置为 standalone 目录
ExecStart=/usr/bin/node $FRONTEND_DIR/.next/standalone/server.js
Restart=always
RestartSec=5
LimitNOFILE=65535

StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-frontend

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "✅ 前端服务配置已更新"
echo "  工作目录: $FRONTEND_DIR/.next/standalone"
echo "  执行命令: /usr/bin/node $FRONTEND_DIR/.next/standalone/server.js"
echo ""

# 5. 验证后端服务配置
echo "[5/7] 验证后端服务配置..."
echo "----------------------------------------"
if [ ! -f "/etc/systemd/system/$BACKEND_SERVICE.service" ]; then
    echo "❌ 后端服务文件不存在"
    exit 1
fi
echo "✅ 后端服务配置存在"
echo ""

# 6. 启动后端服务
echo "[6/7] 启动后端服务..."
echo "----------------------------------------"
systemctl start "$BACKEND_SERVICE"
sleep 5

# 等待服务启动
for i in {1..10}; do
    if systemctl is-active --quiet "$BACKEND_SERVICE"; then
        PORT_CHECK=$(lsof -ti:8000 2>/dev/null || true)
        if [ -n "$PORT_CHECK" ]; then
            echo "✅ 后端服务已启动并监听端口 8000"
            systemctl enable "$BACKEND_SERVICE" 2>/dev/null || true
            break
        fi
    fi
    sleep 1
done

if ! systemctl is-active --quiet "$BACKEND_SERVICE"; then
    echo "❌ 后端服务启动失败"
    systemctl status "$BACKEND_SERVICE" --no-pager -l | head -20
    echo ""
    echo "查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
    exit 1
fi
echo ""

# 7. 启动前端服务
echo "[7/7] 启动前端服务..."
echo "----------------------------------------"
systemctl start "$FRONTEND_SERVICE"
sleep 5

# 等待服务启动
for i in {1..10}; do
    if systemctl is-active --quiet "$FRONTEND_SERVICE"; then
        PORT_CHECK=$(lsof -ti:3000 2>/dev/null || true)
        if [ -n "$PORT_CHECK" ]; then
            echo "✅ 前端服务已启动并监听端口 3000"
            systemctl enable "$FRONTEND_SERVICE" 2>/dev/null || true
            break
        fi
    fi
    sleep 1
done

if ! systemctl is-active --quiet "$FRONTEND_SERVICE"; then
    echo "❌ 前端服务启动失败"
    systemctl status "$FRONTEND_SERVICE" --no-pager -l | head -20
    echo ""
    echo "查看日志: sudo journalctl -u $FRONTEND_SERVICE -n 50 --no-pager"
    exit 1
fi
echo ""

# 最终验证
echo "=========================================="
echo "✅ 修复完成，开始验证..."
echo "=========================================="
echo ""

sleep 3

# 检查服务状态
echo "服务状态:"
BACKEND_STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "inactive")
FRONTEND_STATUS=$(systemctl is-active "$FRONTEND_SERVICE" 2>/dev/null || echo "inactive")
echo "  后端 ($BACKEND_SERVICE): $BACKEND_STATUS"
echo "  前端 ($FRONTEND_SERVICE): $FRONTEND_STATUS"
echo ""

# 检查端口
echo "端口监听:"
PORT_8000=$(lsof -ti:8000 2>/dev/null || true)
PORT_3000=$(lsof -ti:3000 2>/dev/null || true)
if [ -n "$PORT_8000" ]; then
    echo "  端口 8000: ✅ 正在监听 (PID: $PORT_8000)"
else
    echo "  端口 8000: ❌ 未监听"
fi
if [ -n "$PORT_3000" ]; then
    echo "  端口 3000: ✅ 正在监听 (PID: $PORT_3000)"
else
    echo "  端口 3000: ❌ 未监听"
fi
echo ""

# 测试服务响应
echo "服务响应测试:"
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    echo "  后端健康检查: ✅ HTTP 200"
else
    echo "  后端健康检查: ❌ HTTP $BACKEND_HEALTH"
fi

FRONTEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/login 2>/dev/null || echo "000")
if [ "$FRONTEND_TEST" = "200" ]; then
    echo "  前端登录页面: ✅ HTTP 200"
else
    echo "  前端登录页面: ❌ HTTP $FRONTEND_TEST"
fi
echo ""

echo "=========================================="
echo "✅ 所有修复完成"
echo "=========================================="
echo ""
echo "如果仍有问题，请检查:"
echo "  后端日志: sudo journalctl -u $BACKEND_SERVICE -f"
echo "  前端日志: sudo journalctl -u $FRONTEND_SERVICE -f"
echo ""

