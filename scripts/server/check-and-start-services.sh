#!/bin/bash
# ============================================================
# 检查并启动后端服务（端口 3000 和 8000）
# ============================================================

set +e

echo "=========================================="
echo "🔍 检查并启动后端服务"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_SERVICE="luckyred-api"
BACKEND_PORT=8000
FRONTEND_PORT=3000

# 1. 检查端口 8000（后端）
echo "[1/4] 检查端口 $BACKEND_PORT（后端服务）..."
echo "----------------------------------------"
PORT_8000_PID=$(sudo lsof -ti:$BACKEND_PORT 2>/dev/null || true)
if [ -n "$PORT_8000_PID" ]; then
    echo "✅ 端口 $BACKEND_PORT 正在监听"
    echo "进程信息:"
    ps -fp $PORT_8000_PID 2>/dev/null | head -3
    echo ""
    
    # 检查是否是 systemd 服务
    SERVICE_PID=$(systemctl show "$BACKEND_SERVICE" -p MainPID --value 2>/dev/null || echo "")
    if [ -n "$SERVICE_PID" ] && [ "$PORT_8000_PID" = "$SERVICE_PID" ]; then
        echo "✅ 端口由 systemd 服务 ($BACKEND_SERVICE) 管理"
        if systemctl is-active --quiet "$BACKEND_SERVICE"; then
            echo "✅ 服务状态: 运行中"
        else
            echo "⚠️  服务状态: 未运行（但端口被占用）"
        fi
    else
        echo "⚠️  端口被其他进程占用（PID: $PORT_8000_PID）"
    fi
else
    echo "❌ 端口 $BACKEND_PORT 未监听"
    echo "检查 systemd 服务状态..."
    if systemctl is-active --quiet "$BACKEND_SERVICE"; then
        echo "⚠️  服务显示运行中，但端口未监听"
        systemctl status "$BACKEND_SERVICE" --no-pager -l | head -15
    else
        echo "❌ 服务未运行，尝试启动..."
        systemctl start "$BACKEND_SERVICE"
        sleep 5
        if systemctl is-active --quiet "$BACKEND_SERVICE"; then
            echo "✅ 服务已启动"
        else
            echo "❌ 服务启动失败"
            systemctl status "$BACKEND_SERVICE" --no-pager -l | head -20
            echo ""
            echo "查看错误日志:"
            journalctl -u "$BACKEND_SERVICE" -n 50 --no-pager | tail -30
        fi
    fi
fi
echo ""

# 2. 检查端口 3000（前端）
echo "[2/4] 检查端口 $FRONTEND_PORT（前端服务）..."
echo "----------------------------------------"
PORT_3000_PID=$(sudo lsof -ti:$FRONTEND_PORT 2>/dev/null || true)
if [ -n "$PORT_3000_PID" ]; then
    echo "✅ 端口 $FRONTEND_PORT 正在监听"
    echo "进程信息:"
    ps -fp $PORT_3000_PID 2>/dev/null | head -3
    echo ""
    
    # 检查是否是 Next.js
    if ps -fp $PORT_3000_PID 2>/dev/null | grep -q "next\|node"; then
        echo "✅ 检测到 Next.js/Node.js 进程"
    fi
else
    echo "❌ 端口 $FRONTEND_PORT 未监听"
    echo ""
    echo "检查前端服务..."
    
    # 检查是否有 pm2 进程
    if command -v pm2 &> /dev/null; then
        PM2_LIST=$(pm2 list 2>/dev/null | grep -v "┌\|├\|└\|─\|│" | grep -v "^$" | head -5)
        if [ -n "$PM2_LIST" ]; then
            echo "发现 pm2 进程:"
            pm2 list
            echo ""
            echo "尝试启动前端服务..."
            cd "$PROJECT_DIR/saas-demo" 2>/dev/null || cd "$PROJECT_DIR" 2>/dev/null
            pm2 start npm --name "frontend" -- start 2>/dev/null || \
            pm2 start "npm run start" --name "frontend" 2>/dev/null || \
            pm2 restart frontend 2>/dev/null
            sleep 3
        fi
    fi
    
    # 检查是否有 systemd 服务
    FRONTEND_SERVICES=$(systemctl list-units --type=service | grep -E "frontend|next|saas" | awk '{print $1}' | head -3)
    if [ -n "$FRONTEND_SERVICES" ]; then
        for svc in $FRONTEND_SERVICES; do
            if ! systemctl is-active --quiet "$svc"; then
                echo "尝试启动服务: $svc"
                systemctl start "$svc"
                sleep 3
            fi
        done
    fi
    
    # 再次检查端口
    sleep 2
    PORT_3000_PID=$(sudo lsof -ti:$FRONTEND_PORT 2>/dev/null || true)
    if [ -n "$PORT_3000_PID" ]; then
        echo "✅ 前端服务已启动，端口 $FRONTEND_PORT 正在监听"
    else
        echo "⚠️  前端服务可能未运行，但不影响后端 API 访问"
        echo "   提示: 如果只需要后端 API，可以暂时忽略前端服务"
    fi
fi
echo ""

# 3. 验证服务响应
echo "[3/4] 验证服务响应..."
echo "----------------------------------------"
# 测试后端
if [ -n "$PORT_8000_PID" ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$BACKEND_PORT/health 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ] || [ "$HTTP_CODE" = "405" ]; then
        echo "✅ 后端服务响应正常 (HTTP $HTTP_CODE)"
    else
        echo "⚠️  后端服务响应异常 (HTTP $HTTP_CODE)"
    fi
else
    echo "❌ 后端服务未运行，无法测试"
fi

# 测试前端
if [ -n "$PORT_3000_PID" ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$FRONTEND_PORT/ 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
        echo "✅ 前端服务响应正常 (HTTP $HTTP_CODE)"
    else
        echo "⚠️  前端服务响应异常 (HTTP $HTTP_CODE)"
    fi
else
    echo "⚠️  前端服务未运行（可选）"
fi
echo ""

# 4. 总结
echo "[4/4] 服务状态总结..."
echo "----------------------------------------"
echo "端口 $BACKEND_PORT (后端): $([ -n "$PORT_8000_PID" ] && echo "✅ 运行中" || echo "❌ 未运行")"
echo "端口 $FRONTEND_PORT (前端): $([ -n "$PORT_3000_PID" ] && echo "✅ 运行中" || echo "⚠️  未运行（可选）")"
echo ""

echo "=========================================="
echo "✅ 检查完成"
echo "=========================================="
echo ""
echo "如果后端服务未运行，请执行:"
echo "  sudo systemctl start $BACKEND_SERVICE"
echo "  sudo systemctl status $BACKEND_SERVICE"
echo ""

