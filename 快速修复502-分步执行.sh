#!/bin/bash
# 快速修复 502 错误 - 分步执行

cd ~/liaotian

echo "========================================"
echo "快速修复 502 错误"
echo "========================================"
echo ""

# 步骤 1: 检查后端
echo "步骤 1: 检查后端服务"
if curl -s --max-time 3 http://localhost:8000/health 2>&1 | grep -q "ok\|status"; then
    echo "✅ 后端服务正常"
else
    echo "❌ 后端服务未运行，正在启动..."
    cd admin-backend
    source .venv/bin/activate
    pkill -f "uvicorn.*app.main:app" || true
    sleep 2
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_$(date +%s).log 2>&1 &
    echo "后端已启动，等待 5 秒..."
    sleep 5
    cd ..
fi

# 步骤 2: 检查前端
echo ""
echo "步骤 2: 检查前端服务"
if curl -s --max-time 3 http://localhost:3000 2>&1 | head -1 | grep -q "html\|DOCTYPE"; then
    echo "✅ 前端服务正常"
else
    echo "❌ 前端服务未运行，正在启动..."
    cd saas-demo
    pkill -f "next.*dev\|node.*3000" || true
    sleep 2
    nohup npm run dev > /tmp/frontend_$(date +%s).log 2>&1 &
    echo "前端已启动，等待 10 秒..."
    sleep 10
    cd ..
fi

# 步骤 3: 检查并重载 Nginx
echo ""
echo "步骤 3: 检查 Nginx"
if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx 正在运行"
    echo "重新加载 Nginx..."
    sudo systemctl reload nginx
else
    echo "启动 Nginx..."
    sudo systemctl start nginx
fi

# 步骤 4: 最终验证
echo ""
echo "步骤 4: 最终验证"
sleep 3

if curl -s --max-time 3 http://localhost:8000/health 2>&1 | grep -q "ok\|status"; then
    echo "✅ 后端服务正常"
else
    echo "❌ 后端服务异常"
fi

if curl -s --max-time 3 http://localhost:3000 2>&1 | head -1 | grep -q "html\|DOCTYPE"; then
    echo "✅ 前端服务正常"
else
    echo "❌ 前端服务异常"
fi

echo ""
echo "完成！请稍等片刻后刷新浏览器"
