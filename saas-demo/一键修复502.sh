#!/bin/bash
# 一键修复 502 - 简化版本

cd ~/liaotian/saas-demo

echo "========================================"
echo "一键修复 502"
echo "========================================"
echo ""

# 1. 修复端口
echo "[1] 修复端口配置..."
sed -i 's/"dev": "next dev -p 3001"/"dev": "next dev -p 3000"/g' package.json
echo "✅ 完成"
echo ""

# 2. 停止旧进程
echo "[2] 停止旧进程..."
pkill -f "next.*dev|node.*3000" || true
sleep 3
sudo lsof -i :3000 2>/dev/null | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true
sleep 2
echo "✅ 完成"
echo ""

# 3. 安装依赖
echo "[3] 检查依赖..."
[ ! -d "node_modules" ] && npm install 2>&1 | tail -10 || echo "依赖已存在"
echo "✅ 完成"
echo ""

# 4. 启动服务
echo "[4] 启动前端..."
npm run dev > /tmp/frontend_now.log 2>&1 &
echo "等待 60 秒..."
sleep 60
echo "✅ 启动完成"
echo ""

# 5. 验证
echo "[5] 验证服务..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 本地服务正常"
else
    echo "❌ 本地服务异常"
    tail -20 /tmp/frontend_now.log
    exit 1
fi
echo ""

# 6. 重载 Nginx
echo "[6] 重载 Nginx..."
sudo nginx -t && sudo systemctl reload nginx
echo "✅ 完成"
echo ""

# 7. 最终测试
echo "[7] 最终测试..."
sleep 3

echo "本地 3000: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000)"
echo "Nginx代理: $(curl -s -o /dev/null -w '%{http_code}' http://localhost/group-ai/accounts)"
echo "域名访问: $(curl -s -o /dev/null -w '%{http_code}' http://aikz.usdt2026.cc/group-ai/accounts)"
echo ""

echo "========================================"
echo "修复完成"
echo "========================================"
