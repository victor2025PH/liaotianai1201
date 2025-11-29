#!/bin/bash
# 确保服务运行并查看日志

echo "=== 确保服务运行并查看日志 ==="
echo ""

cd ~/liaotian

# 1. 检查后端服务
echo "1. 检查后端服务..."
BACKEND_RUNNING=$(ps aux | grep -E 'uvicorn.*app.main:app' | grep -v grep | wc -l)

if [ "$BACKEND_RUNNING" -eq 0 ]; then
    echo "  ⚠ 后端服务未运行，正在启动..."
    cd admin-backend
    source .venv/bin/activate 2>/dev/null || true
    pkill -f 'uvicorn.*app.main:app' || true
    sleep 2
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 &
    echo "  ✓ 后端服务已启动，PID: $!"
    sleep 5
else
    echo "  ✓ 后端服务正在运行"
fi

# 2. 检查前端服务
echo ""
echo "2. 检查前端服务..."
FRONTEND_RUNNING=$(ps aux | grep -E 'next.*dev|node.*3000' | grep -v grep | wc -l)

if [ "$FRONTEND_RUNNING" -eq 0 ]; then
    echo "  ⚠ 前端服务未运行，正在启动..."
    cd saas-demo
    pkill -f 'next.*dev|node.*3000' || true
    sleep 2
    nohup npm run dev > /tmp/frontend.log 2>&1 &
    echo "  ✓ 前端服务已启动，PID: $!"
    sleep 10
else
    echo "  ✓ 前端服务正在运行"
fi

# 3. 验证服务
echo ""
echo "3. 验证服务..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)

if [ "$BACKEND_STATUS" = "200" ]; then
    echo "  ✓ 后端服务正常 (HTTP $BACKEND_STATUS)"
else
    echo "  ✗ 后端服务异常 (HTTP $BACKEND_STATUS)"
fi

if [ "$FRONTEND_STATUS" = "200" ] || [ "$FRONTEND_STATUS" = "304" ]; then
    echo "  ✓ 前端服务正常 (HTTP $FRONTEND_STATUS)"
else
    echo "  ✗ 前端服务异常 (HTTP $FRONTEND_STATUS)"
fi

# 4. 显示日志文件位置
echo ""
echo "4. 日志文件位置:"
if [ -f "/tmp/backend_final.log" ]; then
    echo "  ✓ /tmp/backend_final.log (存在)"
    echo "    最后20行:"
    tail -20 /tmp/backend_final.log | sed 's/^/    /'
else
    echo "  ⚠ /tmp/backend_final.log (不存在)"
    echo "    检查标准日志:"
    if [ -f "admin-backend/logs/backend.log" ]; then
        tail -20 admin-backend/logs/backend.log | sed 's/^/    /'
    fi
fi

echo ""
echo "=== 完成 ==="
echo ""
echo "查看实时日志:"
echo "  tail -f /tmp/backend_final.log | grep -E 'MIDDLEWARE|UPDATE_ACCOUNT|server_id'"
