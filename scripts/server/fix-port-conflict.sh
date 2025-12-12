#!/bin/bash
# ============================================================
# 修复端口 8000 冲突问题
# ============================================================

echo "=========================================="
echo "修复端口 8000 冲突"
echo "=========================================="
echo ""

# 1. 检查端口 8000 占用情况
echo "[1/4] 检查端口 8000 占用情况..."
PORT_8000_PID=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || echo "")

if [ -z "$PORT_8000_PID" ]; then
    echo "  ✅ 端口 8000 未被占用"
    echo ""
    echo "  检查后端服务状态..."
    BACKEND_SERVICE=""
    if systemctl cat luckyred-api.service >/dev/null 2>&1; then
        BACKEND_SERVICE="luckyred-api"
    elif systemctl cat telegram-backend.service >/dev/null 2>&1; then
        BACKEND_SERVICE="telegram-backend"
    fi
    
    if [ -n "$BACKEND_SERVICE" ]; then
        STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
        if [ "$STATUS" != "active" ]; then
            echo "  ⚠️  后端服务未运行，正在启动..."
            sudo systemctl start "$BACKEND_SERVICE"
            sleep 5
        else
            echo "  ✅ 后端服务正在运行"
        fi
    fi
    exit 0
fi

echo "  ⚠️  端口 8000 被进程 $PORT_8000_PID 占用"
echo ""

# 2. 检查占用端口的进程信息
echo "[2/4] 检查占用端口的进程..."
PROCESS_INFO=$(ps -p "$PORT_8000_PID" -o pid,user,cmd --no-headers 2>/dev/null || echo "")
if [ -n "$PROCESS_INFO" ]; then
    echo "  进程信息:"
    echo "$PROCESS_INFO" | sed 's/^/    /'
else
    echo "  ⚠️  无法获取进程信息（进程可能已结束）"
fi
echo ""

# 3. 停止后端服务
echo "[3/4] 停止后端服务..."
BACKEND_SERVICE=""
if systemctl cat luckyred-api.service >/dev/null 2>&1; then
    BACKEND_SERVICE="luckyred-api"
elif systemctl cat telegram-backend.service >/dev/null 2>&1; then
    BACKEND_SERVICE="telegram-backend"
fi

if [ -n "$BACKEND_SERVICE" ]; then
    echo "  停止服务: $BACKEND_SERVICE"
    sudo systemctl stop "$BACKEND_SERVICE"
    sleep 3
else
    echo "  ⚠️  后端服务未找到"
fi

# 4. 强制终止占用端口的进程
echo "[4/4] 强制终止占用端口的进程..."
if [ -n "$PORT_8000_PID" ]; then
    # 再次检查进程是否还存在
    if ps -p "$PORT_8000_PID" >/dev/null 2>&1; then
        echo "  终止进程: $PORT_8000_PID"
        sudo kill -9 "$PORT_8000_PID" 2>/dev/null || true
        sleep 2
        
        # 验证端口是否已释放
        PORT_8000_AFTER=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || echo "")
        if [ -z "$PORT_8000_AFTER" ]; then
            echo "  ✅ 端口 8000 已释放"
        else
            echo "  ⚠️  端口 8000 仍被占用 (PID: $PORT_8000_AFTER)"
            echo "  尝试再次终止..."
            sudo kill -9 "$PORT_8000_AFTER" 2>/dev/null || true
            sleep 2
        fi
    else
        echo "  ✅ 进程已自动结束"
    fi
fi

echo ""

# 5. 重启后端服务
echo "[5/5] 重启后端服务..."
if [ -n "$BACKEND_SERVICE" ]; then
    echo "  启动服务: $BACKEND_SERVICE"
    sudo systemctl start "$BACKEND_SERVICE"
    sleep 5
    
    # 检查服务状态
    STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
    if [ "$STATUS" = "active" ]; then
        echo "  ✅ 后端服务已启动"
        
        # 验证端口监听
        sleep 3
        PORT_LISTENING=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
        if [ -n "$PORT_LISTENING" ]; then
            echo "  ✅ 端口 8000 正在监听"
        else
            echo "  ⚠️  端口 8000 未监听，查看日志:"
            echo "    sudo journalctl -u $BACKEND_SERVICE -n 30 --no-pager"
        fi
    else
        echo "  ❌ 后端服务启动失败 (状态: $STATUS)"
        echo "  查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
    fi
else
    echo "  ⚠️  后端服务未找到"
fi

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "验证步骤："
echo "  1. 检查服务状态: sudo systemctl status $BACKEND_SERVICE"
echo "  2. 检查端口监听: sudo ss -tlnp | grep 8000"
echo "  3. 测试 API: curl http://localhost:8000/health"
echo ""

