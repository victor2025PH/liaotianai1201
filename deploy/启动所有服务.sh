#!/bin/bash
# 启动所有服务

echo "=== 启动所有服务 ==="
echo ""

cd ~/liaotian

# 1. 启动后端服务
echo "1. 启动后端服务..."
cd admin-backend

# 杀掉旧进程
pkill -f 'uvicorn.*app.main:app' || true
sleep 2

# 激活虚拟环境并启动
source .venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 &
BACKEND_PID=$!

echo "  后端已启动，PID: $BACKEND_PID"
sleep 5

# 检查后端
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✓ 后端服务正常"
else
    echo "  ⚠ 后端服务可能未完全启动，请检查日志"
fi

# 2. 启动前端服务
echo ""
echo "2. 启动前端服务..."
cd ../saas-demo

# 杀掉旧进程
pkill -f 'next.*dev|node.*3000' || true
sleep 2

# 启动前端
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

echo "  前端已启动，PID: $FRONTEND_PID"
sleep 10

# 检查前端
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "  ✓ 前端服务正常"
else
    echo "  ⚠ 前端服务可能未完全启动，请检查日志"
fi

echo ""
echo "=== 服务状态 ==="
echo "后端 PID: $BACKEND_PID"
echo "前端 PID: $FRONTEND_PID"
echo ""
echo "后端日志: /tmp/backend_final.log"
echo "前端日志: /tmp/frontend.log"
echo ""
echo "查看后端日志: tail -f /tmp/backend_final.log"
echo "查看前端日志: tail -f /tmp/frontend.log"
