#!/bin/bash
# 启动所有服务并检查状态

cd ~/liaotian

echo "========================================="
echo "启动所有服务并检查状态"
echo "========================================="
echo ""

# 1. 检查后端服务
echo "【1】检查后端服务..."
BACKEND_RUNNING=$(ps aux | grep -E 'uvicorn.*app.main:app' | grep -v grep | wc -l)

if [ "$BACKEND_RUNNING" -eq 0 ]; then
    echo "  启动后端服务..."
    cd admin-backend
    source .venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 &
    sleep 5
else
    echo "  ✓ 后端服务已在运行"
fi

# 验证后端
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$BACKEND_STATUS" = "200" ]; then
    echo "  ✓ 后端健康检查: HTTP $BACKEND_STATUS"
else
    echo "  ✗ 后端健康检查: HTTP $BACKEND_STATUS"
fi

# 2. 检查前端服务
echo ""
echo "【2】检查前端服务..."
FRONTEND_RUNNING=$(ps aux | grep -E 'next.*dev|node.*3000' | grep -v grep | wc -l)

if [ "$FRONTEND_RUNNING" -eq 0 ]; then
    echo "  启动前端服务..."
    cd saas-demo
    pkill -f 'next.*dev|node.*3000' 2>/dev/null || true
    nohup npm run dev > /tmp/frontend.log 2>&1 &
    echo "  等待前端启动..."
    sleep 15
else
    echo "  ✓ 前端服务已在运行"
fi

# 验证前端
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$FRONTEND_STATUS" = "200" ] || [ "$FRONTEND_STATUS" = "304" ]; then
    echo "  ✓ 前端服务: HTTP $FRONTEND_STATUS"
else
    echo "  ✗ 前端服务: HTTP $FRONTEND_STATUS"
fi

# 3. 检查Nginx
echo ""
echo "【3】检查Nginx..."
if sudo systemctl is-active --quiet nginx; then
    echo "  ✓ Nginx 正在运行"
    echo "  重新加载配置..."
    sudo nginx -t && sudo systemctl reload nginx
else
    echo "  ⚠ Nginx 未运行"
fi

# 4. 最终状态
echo ""
echo "========================================="
echo "服务状态总结"
echo "========================================="
echo ""
echo "后端 (8000): HTTP $BACKEND_STATUS"
echo "前端 (3000): HTTP $FRONTEND_STATUS"
echo ""
echo "进程数:"
echo "  后端: $(ps aux | grep uvicorn | grep -v grep | wc -l)"
echo "  前端: $(ps aux | grep -E 'next.*dev' | grep -v grep | wc -l)"
echo ""
echo "访问地址: http://aikz.usdt2026.cc/group-ai/accounts"
