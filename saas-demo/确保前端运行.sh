#!/bin/bash
# 确保前端服务运行

cd ~/liaotian/saas-demo

echo "========================================"
echo "确保前端服务运行"
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 1. 确保端口配置正确
if ! grep -q '"dev": "next dev -p 3000"' package.json; then
    echo "修复端口配置..."
    sed -i 's/"dev": "next dev -p 3001"/"dev": "next dev -p 3000"/g' package.json
    sed -i 's/"dev": "next dev"/"dev": "next dev -p 3000"/g' package.json
fi

# 2. 停止旧进程
pkill -f "next.*dev|node.*3000" || true
sleep 3
sudo lsof -i :3000 2>/dev/null | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true
sleep 2

# 3. 检查依赖
[ ! -d "node_modules" ] && npm install 2>&1 | tail -20

# 4. 启动服务
npm run dev > /tmp/frontend_ensure.log 2>&1 &
PID=$!
echo "前端已启动 PID: $PID"

# 5. 等待并验证
echo "等待启动（60秒）..."
sleep 60

# 检查进程
if ps -p $PID > /dev/null 2>&1; then
    echo "✅ 进程运行中"
else
    echo "❌ 进程退出，查看日志:"
    tail -30 /tmp/frontend_ensure.log
    exit 1
fi

# 检查端口
if curl -s --max-time 5 http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 服务可访问"
else
    echo "⚠️  服务可能还在启动中"
    tail -20 /tmp/frontend_ensure.log
fi

# 6. 重载 Nginx
sudo systemctl reload nginx

echo ""
echo "========================================"
echo "完成"
echo "========================================"
