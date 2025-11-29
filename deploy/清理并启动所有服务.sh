#!/bin/bash
# 清理并启动所有服务

set -e

cd ~/liaotian

echo "========================================="
echo "清理并启动所有服务"
echo "========================================="
echo ""

# 1. 清理所有旧进程
echo "【1】清理所有旧进程..."
echo "  清理后端进程..."
pkill -9 -f 'uvicorn.*app.main:app' 2>/dev/null || true
pkill -9 -f 'python.*uvicorn' 2>/dev/null || true

echo "  清理前端进程..."
pkill -9 -f 'next.*dev|node.*3000' 2>/dev/null || true

echo "  清理端口占用..."
sudo lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sudo lsof -ti:3000 | xargs kill -9 2>/dev/null || true

sleep 3
echo "  ✓ 清理完成"
echo ""

# 2. 启动后端服务
echo "【2】启动后端服务..."
cd admin-backend

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "  ⚠ 虚拟环境不存在，创建中..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 创建日志文件
touch /tmp/backend_final.log
chmod 666 /tmp/backend_final.log

# 启动后端
echo "  启动 uvicorn..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 &
BACKEND_PID=$!

echo "  后端已启动，PID: $BACKEND_PID"

# 等待后端启动
echo "  等待后端启动..."
for i in {1..10}; do
    sleep 2
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✓ 后端服务已就绪"
        curl -s http://localhost:8000/health
        echo ""
        break
    fi
    if [ $i -eq 10 ]; then
        echo "  ⚠ 后端可能未完全启动，查看日志:"
        tail -30 /tmp/backend_final.log
    fi
done
echo ""

# 3. 启动前端服务
echo "【3】启动前端服务..."
cd ../saas-demo

# 创建日志文件
touch /tmp/frontend.log
chmod 666 /tmp/frontend.log

# 启动前端
echo "  启动 Next.js..."
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

echo "  前端已启动，PID: $FRONTEND_PID"

# 等待前端启动
echo "  等待前端启动..."
sleep 15

# 验证前端
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "  ✓ 前端服务已就绪"
else
    echo "  ⚠ 前端可能未完全启动"
fi
echo ""

# 4. 显示最终状态
echo "【4】服务状态:"
BACKEND_COUNT=$(ps aux | grep -E 'uvicorn.*app.main:app' | grep -v grep | wc -l)
FRONTEND_COUNT=$(ps aux | grep -E 'next.*dev|node.*3000' | grep -v grep | wc -l)

echo "  后端进程: $BACKEND_COUNT 个"
echo "  前端进程: $FRONTEND_COUNT 个"
echo ""

# 5. 验证HTTP访问
echo "【5】HTTP访问验证:"
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)

if [ "$BACKEND_STATUS" = "200" ]; then
    echo "  ✓ 后端: HTTP $BACKEND_STATUS"
else
    echo "  ✗ 后端: HTTP $BACKEND_STATUS"
fi

if [ "$FRONTEND_STATUS" = "200" ] || [ "$FRONTEND_STATUS" = "304" ]; then
    echo "  ✓ 前端: HTTP $FRONTEND_STATUS"
else
    echo "  ✗ 前端: HTTP $FRONTEND_STATUS"
fi

echo ""
echo "========================================="
echo "完成！"
echo "========================================="
echo ""
echo "📝 日志文件:"
echo "  后端: /tmp/backend_final.log"
echo "  前端: /tmp/frontend.log"
echo ""
echo "🔍 查看日志:"
echo "  tail -f /tmp/backend_final.log"
echo "  tail -f /tmp/frontend.log"
echo ""
echo "🌐 访问地址:"
echo "  http://aikz.usdt2026.cc/group-ai/accounts"
