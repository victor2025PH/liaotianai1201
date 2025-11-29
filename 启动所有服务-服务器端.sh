#!/bin/bash
# 启动所有服务（后端、前端）

set -e

cd ~/liaotian

echo "========================================"
echo "启动所有服务"
echo "========================================"
echo ""

# 1. 启动后端服务
echo "[1] 启动后端服务..."
cd admin-backend

if [ ! -d ".venv" ]; then
    echo "错误: 虚拟环境不存在"
    exit 1
fi

source .venv/bin/activate

# 停止现有进程
pkill -f "uvicorn.*app.main:app" || true
sleep 2

# 启动后端
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务已启动 (PID: $BACKEND_PID)"
sleep 5

# 验证后端
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端服务正常"
else
    echo "⚠️  后端服务可能还在启动中"
fi

echo ""

# 2. 启动前端服务
echo "[2] 启动前端服务..."
cd ../saas-demo

# 停止现有进程
pkill -f "next.*dev\|node.*3000" || true
sleep 2

# 启动前端
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端服务已启动 (PID: $FRONTEND_PID)"
sleep 10

# 验证前端
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务正常"
else
    echo "⚠️  前端服务可能还在启动中"
fi

echo ""

echo "========================================"
echo "服务启动完成"
echo "========================================"
echo "后端 PID: $BACKEND_PID"
echo "前端 PID: $FRONTEND_PID"
echo ""
echo "查看日志:"
echo "  tail -f /tmp/backend.log"
echo "  tail -f /tmp/frontend.log"
