#!/bin/bash
# 直接修复 502 - 最直接的方法

set -e

cd ~/liaotian/saas-demo

echo "========================================"
echo "直接修复 502"
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 1. 确保端口配置正确
echo "[1] 确保端口配置为 3000..."
sed -i 's/"dev": "next dev -p 3001"/"dev": "next dev -p 3000"/g' package.json
grep '"dev"' package.json
echo ""

# 2. 停止并清理
echo "[2] 停止旧进程..."
pkill -f "next.*dev|node.*3000" || true
sleep 2

if sudo lsof -i :3000 2>/dev/null | grep -q LISTEN; then
    sudo lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    sleep 2
fi
echo "完成"
echo ""

# 3. 安装依赖（如果需要）
echo "[3] 检查依赖..."
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/next" ]; then
    echo "安装依赖..."
    npm install 2>&1 | tail -20
fi
echo ""

# 4. 启动服务
echo "[4] 启动前端服务..."
npm run dev > /tmp/frontend_direct.log 2>&1 &
PID=$!
echo "PID: $PID"
sleep 45

# 5. 验证
echo "[5] 验证..."
if ps -p $PID > /dev/null 2>&1; then
    echo "✅ 进程运行"
else
    echo "❌ 进程退出，日志:"
    tail -30 /tmp/frontend_direct.log
    exit 1
fi

if curl -s --max-time 5 http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 端口可访问"
else
    echo "❌ 端口不可访问"
    tail -30 /tmp/frontend_direct.log
    exit 1
fi
echo ""

# 6. 检查并修复 Nginx
echo "[6] 检查 Nginx..."
NGINX_FILE="/etc/nginx/sites-enabled/default"

# 备份配置
sudo cp "$NGINX_FILE" "${NGINX_FILE}.backup.$(date +%s)" 2>/dev/null || true

# 检查是否需要添加 /group-ai 配置
if ! grep -q "location.*group-ai" "$NGINX_FILE"; then
    echo "检查 Nginx 配置结构..."
    # 先检查现有的 location / 配置
    if grep -q "location / {" "$NGINX_FILE"; then
        echo "已有 location / 配置，应该可以工作"
    else
        echo "⚠️  未找到 location / 配置，可能需要添加"
    fi
fi

# 确保 proxy_pass 指向 3000
if grep -q "proxy_pass.*3000" "$NGINX_FILE"; then
    echo "✅ proxy_pass 已指向 3000"
else
    echo "⚠️  检查 proxy_pass 配置..."
    grep "proxy_pass" "$NGINX_FILE" | head -3
fi

# 测试并重载
echo ""
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置正确"
    sudo systemctl reload nginx
    echo "✅ Nginx 已重载"
else
    echo "❌ Nginx 配置错误:"
    sudo nginx -t
fi
echo ""

# 7. 最终测试
echo "[7] 最终测试..."
sleep 3

echo "本地 3000:"
curl -s -I http://localhost:3000 | head -2 || echo "失败"
echo ""

echo "Nginx 代理:"
curl -s -I http://localhost/group-ai/accounts | head -2 || echo "失败"
echo ""

echo "域名访问:"
curl -s -I http://aikz.usdt2026.cc/group-ai/accounts | head -2 || echo "失败"
echo ""

echo "========================================"
echo "修复完成"
echo "========================================"
