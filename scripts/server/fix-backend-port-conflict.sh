#!/bin/bash
# ============================================================
# 修复后端端口冲突 - 强制停止旧进程并重启服务
# ============================================================

set -e

echo "=========================================="
echo "修复后端端口冲突"
echo "=========================================="
echo ""

# 1. 检查端口占用
echo "[1/6] 检查端口 8000 占用情况..."
PORT_8000_PID=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || echo "")

if [ -n "$PORT_8000_PID" ]; then
    echo "  ⚠️  端口 8000 被进程 $PORT_8000_PID 占用"
    
    # 检查进程信息
    PROCESS_CMD=$(ps -p "$PORT_8000_PID" -o cmd --no-headers 2>/dev/null | head -1 || echo "")
    if [ -n "$PROCESS_CMD" ]; then
        echo "  进程命令: $PROCESS_CMD"
    fi
    echo ""
else
    echo "  ✅ 端口 8000 未被占用"
    echo ""
fi

# 2. 停止后端服务
echo "[2/6] 停止后端服务..."
BACKEND_SERVICE=""
if systemctl cat luckyred-api.service >/dev/null 2>&1; then
    BACKEND_SERVICE="luckyred-api"
elif systemctl cat telegram-backend.service >/dev/null 2>&1; then
    BACKEND_SERVICE="telegram-backend"
fi

if [ -n "$BACKEND_SERVICE" ]; then
    echo "  停止服务: $BACKEND_SERVICE"
    sudo systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
    sleep 3
    echo "  ✅ 服务已停止"
else
    echo "  ⚠️  后端服务未找到"
fi
echo ""

# 3. 强制终止所有占用端口 8000 的进程
echo "[3/6] 强制终止占用端口 8000 的进程..."
if [ -n "$PORT_8000_PID" ]; then
    # 终止指定进程
    echo "  终止进程: $PORT_8000_PID"
    sudo kill -9 "$PORT_8000_PID" 2>/dev/null || true
    sleep 2
    
    # 终止所有 uvicorn 进程（确保清理干净）
    echo "  清理所有 uvicorn 进程..."
    sudo pkill -9 -f "uvicorn.*8000" 2>/dev/null || true
    sleep 2
    
    # 终止所有可能占用端口的 python 进程
    echo "  清理可能占用端口的 python 进程..."
    for pid in $(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' || echo ""); do
        if [ -n "$pid" ]; then
            echo "    终止进程: $pid"
            sudo kill -9 "$pid" 2>/dev/null || true
        fi
    done
    sleep 2
fi

# 4. 验证端口已释放
echo "[4/6] 验证端口已释放..."
PORT_8000_AFTER=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || echo "")
if [ -z "$PORT_8000_AFTER" ]; then
    echo "  ✅ 端口 8000 已释放"
else
    echo "  ⚠️  端口 8000 仍被占用 (PID: $PORT_8000_AFTER)"
    echo "  强制终止..."
    sudo kill -9 "$PORT_8000_AFTER" 2>/dev/null || true
    sleep 2
fi
echo ""

# 5. 重新加载 systemd
echo "[5/6] 重新加载 systemd..."
sudo systemctl daemon-reload
echo "  ✅ Systemd 已重新加载"
echo ""

# 6. 启动后端服务
echo "[6/6] 启动后端服务..."
if [ -n "$BACKEND_SERVICE" ]; then
    echo "  启动服务: $BACKEND_SERVICE"
    sudo systemctl start "$BACKEND_SERVICE"
    
    # 等待服务启动
    echo "  等待服务启动（10秒）..."
    sleep 10
    
    # 检查服务状态
    STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
    if [ "$STATUS" = "active" ]; then
        echo "  ✅ 后端服务已启动 (状态: $STATUS)"
        
        # 验证端口监听
        sleep 3
        PORT_LISTENING=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
        if [ -n "$PORT_LISTENING" ]; then
            NEW_PID=$(echo "$PORT_LISTENING" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || echo "")
            echo "  ✅ 端口 8000 正在监听 (PID: $NEW_PID)"
            
            # 测试健康检查
            echo "  测试健康检查..."
            if curl -s http://localhost:8000/health >/dev/null 2>&1; then
                echo "  ✅ 健康检查通过"
            else
                echo "  ⚠️  健康检查失败"
            fi
        else
            echo "  ⚠️  端口 8000 未监听"
            echo "  查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
        fi
    else
        echo "  ❌ 后端服务启动失败 (状态: $STATUS)"
        echo "  查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
        exit 1
    fi
else
    echo "  ⚠️  后端服务未找到"
    exit 1
fi

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "验证步骤："
echo "  1. 检查服务状态: sudo systemctl status $BACKEND_SERVICE"
echo "  2. 检查端口监听: sudo ss -tlnp | grep 8000"
echo "  3. 测试健康检查: curl http://localhost:8000/health"
echo "  4. 测试 AI Provider API: curl http://localhost:8000/api/v1/group-ai/ai-provider/providers"
echo ""

