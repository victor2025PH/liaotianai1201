#!/bin/bash
# ============================================================
# 完整修复所有问题：端口冲突、Nginx配置、服务启动
# ============================================================

set +e

echo "=========================================="
echo "🔧 完整修复所有问题"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

BACKEND_SERVICE="luckyred-api"
BACKEND_PORT=8000
FRONTEND_PORT=3000
PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 1. 停止 systemd 服务
echo "[1/7] 停止 systemd 服务..."
echo "----------------------------------------"
systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
sleep 2
echo "✅ 服务已停止"
echo ""

# 2. 强制清理端口 8000 的所有进程
echo "[2/7] 强制清理端口 $BACKEND_PORT 的所有进程..."
echo "----------------------------------------"
PORT_PIDS=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
if [ -n "$PORT_PIDS" ]; then
    echo "发现占用端口 $BACKEND_PORT 的进程: $PORT_PIDS"
    for pid in $PORT_PIDS; do
        echo "  终止进程 $pid..."
        kill -9 $pid 2>/dev/null || true
    done
    sleep 2
    
    # 再次检查
    REMAINING=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
    if [ -n "$REMAINING" ]; then
        echo "⚠️  仍有进程占用，强制终止..."
        kill -9 $REMAINING 2>/dev/null || true
        sleep 1
    fi
    echo "✅ 端口 $BACKEND_PORT 已释放"
else
    echo "✅ 端口 $BACKEND_PORT 未被占用"
fi
echo ""

# 3. 清理所有相关的 Python/uvicorn 进程
echo "[3/7] 清理所有相关的 Python/uvicorn 进程..."
echo "----------------------------------------"
# 查找所有 uvicorn 进程
UVICORN_PIDS=$(ps aux | grep "[u]vicorn.*app.main:app" | awk '{print $2}' || true)
if [ -n "$UVICORN_PIDS" ]; then
    echo "发现 uvicorn 进程: $UVICORN_PIDS"
    for pid in $UVICORN_PIDS; do
        echo "  终止进程 $pid..."
        kill -9 $pid 2>/dev/null || true
    done
    sleep 1
    echo "✅ 相关进程已清理"
else
    echo "✅ 未发现相关进程"
fi
echo ""

# 4. 验证端口已完全释放
echo "[4/7] 验证端口已完全释放..."
echo "----------------------------------------"
sleep 2
FINAL_CHECK=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
if [ -n "$FINAL_CHECK" ]; then
    echo "❌ 警告: 端口 $BACKEND_PORT 仍被占用 (PID: $FINAL_CHECK)"
    echo "尝试最后一次强制清理..."
    kill -9 $FINAL_CHECK 2>/dev/null || true
    sleep 2
else
    echo "✅ 端口 $BACKEND_PORT 已完全释放"
fi
echo ""

# 5. 重新加载 systemd 并启动后端服务
echo "[5/7] 重新加载 systemd 并启动后端服务..."
echo "----------------------------------------"
systemctl daemon-reload
sleep 1
systemctl start "$BACKEND_SERVICE"
sleep 5

# 检查服务状态
if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    echo "✅ 后端服务已启动"
    
    # 等待服务完全启动
    echo "等待服务完全启动（最多 15 秒）..."
    for i in {1..15}; do
        PORT_CHECK=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
        if [ -n "$PORT_CHECK" ]; then
            SERVICE_PID=$(systemctl show "$BACKEND_SERVICE" -p MainPID --value 2>/dev/null || echo "")
            if [ -n "$SERVICE_PID" ] && [ "$PORT_CHECK" = "$SERVICE_PID" ]; then
                echo "✅ 端口 $BACKEND_PORT 已由 systemd 服务管理 (PID: $SERVICE_PID)"
                break
            fi
        fi
        sleep 1
        echo -n "."
    done
    echo ""
else
    echo "❌ 后端服务启动失败"
    systemctl status "$BACKEND_SERVICE" --no-pager -l | head -20
    echo ""
    echo "查看错误日志:"
    journalctl -u "$BACKEND_SERVICE" -n 30 --no-pager | tail -20
    exit 1
fi
echo ""

# 6. 重置 Nginx 配置（使用修复后的配置）
echo "[6/7] 重置 Nginx 配置（已修复 /login 路由）..."
echo "----------------------------------------"
if [ -f "$PROJECT_DIR/scripts/server/reset-nginx-config.sh" ]; then
    bash "$PROJECT_DIR/scripts/server/reset-nginx-config.sh"
    if [ $? -ne 0 ]; then
        echo "❌ Nginx 配置重置失败"
        exit 1
    fi
else
    echo "❌ Nginx 重置脚本不存在"
    exit 1
fi
echo ""

# 7. 检查前端服务（可选）
echo "[7/7] 检查前端服务（端口 $FRONTEND_PORT）..."
echo "----------------------------------------"
FRONTEND_PID=$(lsof -ti:$FRONTEND_PORT 2>/dev/null || true)
if [ -n "$FRONTEND_PID" ]; then
    echo "✅ 前端服务正在运行 (PID: $FRONTEND_PID)"
else
    echo "⚠️  前端服务未运行（可选，不影响后端 API）"
    echo ""
    echo "如果需要启动前端服务，可以执行:"
    echo "  cd $PROJECT_DIR/saas-demo"
    echo "  npm run start"
    echo "  或使用 pm2: pm2 start npm --name frontend -- start"
fi
echo ""

# 最终验证
echo "=========================================="
echo "✅ 修复完成，开始验证..."
echo "=========================================="
echo ""

sleep 2

# 测试后端健康检查
echo "测试后端健康检查..."
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$BACKEND_PORT/health 2>/dev/null || echo "000")
if [ "$HEALTH_CODE" = "200" ]; then
    echo "✅ 后端健康检查正常 (HTTP 200)"
else
    echo "⚠️  后端健康检查异常 (HTTP $HEALTH_CODE)"
fi

# 测试后端登录路由
echo "测试后端登录路由..."
LOGIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:$BACKEND_PORT/api/v1/auth/login 2>/dev/null || echo "000")
if [ "$LOGIN_CODE" = "422" ] || [ "$LOGIN_CODE" = "401" ]; then
    echo "✅ 后端登录路由可访问 (HTTP $LOGIN_CODE - 需要认证参数，这是正常的)"
elif [ "$LOGIN_CODE" = "404" ]; then
    echo "❌ 后端登录路由不存在 (HTTP 404)"
else
    echo "⚠️  后端登录路由响应异常 (HTTP $LOGIN_CODE)"
fi

# 测试 HTTPS /login
echo "测试 HTTPS /login..."
HTTPS_LOGIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://aikz.usdt2026.cc/login 2>/dev/null || echo "000")
if [ "$HTTPS_LOGIN_CODE" = "405" ] || [ "$HTTPS_LOGIN_CODE" = "422" ] || [ "$HTTPS_LOGIN_CODE" = "401" ]; then
    echo "✅ HTTPS /login 路由正常 (HTTP $HTTPS_LOGIN_CODE - 需要 POST 请求，这是正常的)"
elif [ "$HTTPS_LOGIN_CODE" = "404" ]; then
    echo "❌ HTTPS /login 路由返回 404"
else
    echo "⚠️  HTTPS /login 响应异常 (HTTP $HTTPS_LOGIN_CODE)"
fi

# 测试 HTTPS /api
echo "测试 HTTPS /api..."
HTTPS_API_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://aikz.usdt2026.cc/api/v1/health 2>/dev/null || echo "000")
if [ "$HTTPS_API_CODE" = "200" ] || [ "$HTTPS_API_CODE" = "404" ] || [ "$HTTPS_API_CODE" = "401" ]; then
    echo "✅ HTTPS /api 路由正常 (HTTP $HTTPS_API_CODE)"
else
    echo "⚠️  HTTPS /api 响应异常 (HTTP $HTTPS_API_CODE)"
fi

echo ""
echo "=========================================="
echo "✅ 所有修复和验证完成"
echo "=========================================="
echo ""
echo "如果仍有问题，请检查:"
echo "1. 后端服务日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager"
echo "2. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo "3. 端口监听: sudo ss -tlnp | grep -E '$BACKEND_PORT|$FRONTEND_PORT'"
echo ""

