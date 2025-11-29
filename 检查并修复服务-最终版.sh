#!/bin/bash
# 检查并修复服务 - 最终版本

cd ~/liaotian

LOG_DIR="/tmp/service_check_$(date +%s)"
mkdir -p "$LOG_DIR"

echo "========================================"
echo "服务检查和修复"
echo "日志目录: $LOG_DIR"
echo "========================================"
echo ""

# 检查后端
echo "检查后端服务..."
if curl -s --max-time 3 http://localhost:8000/health 2>&1 | grep -q "ok\|status"; then
    echo "✅ 后端服务正常"
else
    echo "启动后端服务..."
    cd admin-backend
    source .venv/bin/activate
    pkill -f "uvicorn.*app.main:app" || true
    sleep 2
    uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
    echo $! > "$LOG_DIR/backend.pid"
    echo "后端已启动 (PID: $(cat $LOG_DIR/backend.pid))"
    sleep 8
    cd ..
fi

# 检查前端
echo ""
echo "检查前端服务..."
if curl -s --max-time 3 http://localhost:3000 2>&1 | head -1 | grep -q "html\|DOCTYPE"; then
    echo "✅ 前端服务正常"
else
    echo "启动前端服务..."
    cd saas-demo
    
    # 检查是否需要构建
    if [ ! -d ".next" ]; then
        echo "构建前端..."
        npm run build > "$LOG_DIR/frontend_build.log" 2>&1
    fi
    
    pkill -f "next.*dev\|node.*3000" || true
    sleep 2
    
    PORT=3000 npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$LOG_DIR/frontend.pid"
    echo "前端已启动 (PID: $(cat $LOG_DIR/frontend.pid))"
    sleep 15
    cd ..
fi

# 验证
echo ""
echo "最终验证..."
sleep 3

BACKEND_OK=false
FRONTEND_OK=false

if curl -s --max-time 3 http://localhost:8000/health 2>&1 | grep -q "ok\|status"; then
    echo "✅ 后端服务正常"
    BACKEND_OK=true
else
    echo "❌ 后端服务异常"
fi

if curl -s --max-time 3 http://localhost:3000 2>&1 | head -1 | grep -q "html\|DOCTYPE"; then
    echo "✅ 前端服务正常"
    FRONTEND_OK=true
else
    echo "❌ 前端服务异常"
fi

echo ""
echo "日志位置: $LOG_DIR"

if [ "$BACKEND_OK" = true ] && [ "$FRONTEND_OK" = true ]; then
    echo "✅ 所有服务正常"
    exit 0
else
    echo "⚠️  部分服务异常，请检查日志"
    exit 1
fi
