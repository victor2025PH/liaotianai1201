#!/bin/bash
# 修复502错误 - 启动前端服务

cd ~/liaotian

echo "========================================="
echo "修复502错误 - 启动前端服务"
echo "========================================="
echo ""

# 1. 检查后端
echo "【1】检查后端服务..."
BACKEND_OK=$(curl -s http://localhost:8000/health 2>/dev/null)
if [[ "$BACKEND_OK" == *"ok"* ]]; then
    echo "  ✓ 后端服务正常: $BACKEND_OK"
else
    echo "  ✗ 后端服务异常"
    echo "  启动后端服务..."
    cd admin-backend
    source .venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 &
    sleep 5
    cd ..
fi
echo ""

# 2. 检查并启动前端
echo "【2】检查前端服务..."
FRONTEND_RUNNING=$(ps aux | grep -E 'next.*dev|node.*3000' | grep -v grep | wc -l)

if [ "$FRONTEND_RUNNING" -eq 0 ]; then
    echo "  ⚠ 前端服务未运行"
    echo "  启动前端服务..."
    cd saas-demo
    
    # 清理旧进程
    pkill -f 'next.*dev|node.*3000' 2>/dev/null || true
    sleep 2
    
    # 启动前端
    nohup npm run dev > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "  前端已启动，PID: $FRONTEND_PID"
    echo "  等待前端启动（15秒）..."
    sleep 15
else
    echo "  ✓ 前端服务已在运行"
fi

# 3. 验证前端
echo ""
echo "【3】验证前端服务..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$FRONTEND_STATUS" = "200" ] || [ "$FRONTEND_STATUS" = "304" ]; then
    echo "  ✓ 前端服务正常: HTTP $FRONTEND_STATUS"
else
    echo "  ⚠ 前端服务可能未完全启动: HTTP $FRONTEND_STATUS"
    echo "  查看日志: tail -50 /tmp/frontend.log"
fi

# 4. 重新加载Nginx
echo ""
echo "【4】重新加载Nginx..."
if sudo nginx -t 2>/dev/null; then
    sudo systemctl reload nginx
    echo "  ✓ Nginx 配置已重新加载"
else
    echo "  ⚠ Nginx 配置测试失败"
fi

# 5. 最终状态
echo ""
echo "========================================="
echo "完成！"
echo "========================================="
echo ""
echo "服务状态:"
echo "  后端 (8000): $(curl -s http://localhost:8000/health | grep -o 'ok' || echo '异常')"
echo "  前端 (3000): HTTP $FRONTEND_STATUS"
echo ""
echo "进程数:"
echo "  后端: $(ps aux | grep uvicorn | grep -v grep | wc -l)"
echo "  前端: $(ps aux | grep -E 'next.*dev' | grep -v grep | wc -l)"
echo ""
echo "请刷新浏览器测试: http://aikz.usdt2026.cc/group-ai/accounts"
