#!/bin/bash
# 完整 502 修复流程 - 自动诊断和修复

set -e

cd ~/liaotian/saas-demo

echo "========================================"
echo "完整 502 修复流程"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

LOG_FILE="/tmp/502_fix_$(date +%s).log"
exec > >(tee -a "$LOG_FILE")
exec 2>&1

# 步骤 1: 检查项目
echo "[1/7] 检查项目..."
if [ ! -f "package.json" ]; then
    echo "❌ 错误: 找不到 package.json"
    exit 1
fi

if ! grep -q '"next"' package.json; then
    echo "❌ 错误: 这不是 Next.js 项目"
    exit 1
fi

echo "✅ Next.js 项目确认"
echo "Node: $(node -v 2>&1)"
echo "npm: $(npm -v 2>&1)"
echo ""

# 步骤 2: 检查并修复端口配置
echo "[2/7] 检查端口配置..."
if grep -q '"dev": "next dev -p 3001"' package.json; then
    echo "⚠️  端口配置为 3001，修复为 3000..."
    sed -i 's/"dev": "next dev -p 3001"/"dev": "next dev -p 3000"/g' package.json
    echo "✅ 已修复"
fi

PORT_CHECK=$(grep '"dev"' package.json | grep -o '3000')
if [ "$PORT_CHECK" != "3000" ]; then
    echo "⚠️  端口配置可能有问题，检查中..."
fi
echo ""

# 步骤 3: 停止旧进程
echo "[3/7] 停止旧进程..."
pkill -f "next.*dev|node.*3000|node.*3001" || true
sleep 2

# 清理端口
if sudo lsof -i :3000 2>/dev/null | grep -q LISTEN; then
    echo "清理端口 3000..."
    sudo lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    sleep 2
fi
echo "✅ 完成"
echo ""

# 步骤 4: 检查依赖
echo "[4/7] 检查依赖..."
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/next" ]; then
    echo "⚠️  依赖不完整，安装中..."
    rm -rf node_modules package-lock.json
    npm install 2>&1 | tail -30
    
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
    echo "✅ 依赖安装完成"
else
    echo "✅ 依赖正常"
fi
echo ""

# 步骤 5: 检查构建
echo "[5/7] 检查构建..."
if [ ! -d ".next" ]; then
    echo "⚠️  未构建，开始构建..."
    npm run build 2>&1 | tail -50
    
    if [ $? -ne 0 ]; then
        echo "⚠️  构建失败，但继续尝试启动开发服务器"
    else
        echo "✅ 构建完成"
    fi
else
    echo "✅ 构建存在"
fi
echo ""

# 步骤 6: 启动前端服务
echo "[6/7] 启动前端服务..."
npm run dev > /tmp/frontend_502fix.log 2>&1 &
DEV_PID=$!
echo "进程 PID: $DEV_PID"

echo "等待服务启动（45秒）..."
sleep 45

# 验证进程
if ps -p $DEV_PID > /dev/null 2>&1; then
    echo "✅ 进程运行中"
else
    echo "❌ 进程已退出，查看日志:"
    tail -50 /tmp/frontend_502fix.log
    exit 1
fi

# 验证端口
if curl -s --max-time 5 http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 端口 3000 可访问"
else
    echo "❌ 端口 3000 无法访问"
    tail -50 /tmp/frontend_502fix.log
    exit 1
fi
echo ""

# 步骤 7: 检查 Nginx 配置
echo "[7/7] 检查 Nginx 配置..."
NGINX_CONFIG="/etc/nginx/sites-enabled/default"

# 检查配置是否存在
if [ ! -f "$NGINX_CONFIG" ]; then
    echo "⚠️  Nginx 配置文件不存在，检查其他位置..."
    NGINX_CONFIG=$(find /etc/nginx -name "*aikz*" -o -name "*default*" 2>/dev/null | head -1)
fi

if [ -f "$NGINX_CONFIG" ]; then
    echo "配置文件: $NGINX_CONFIG"
    
    # 检查是否有 /group-ai 路径配置
    if ! grep -q "location.*group-ai" "$NGINX_CONFIG"; then
        echo "⚠️  未找到 /group-ai 路径配置"
        echo "当前 location / 配置:"
        grep -A 5 "location /" "$NGINX_CONFIG" | head -6
    else
        echo "✅ 找到 /group-ai 配置"
    fi
    
    # 检查 proxy_pass 端口
    if grep -q "proxy_pass.*3000" "$NGINX_CONFIG"; then
        echo "✅ proxy_pass 指向端口 3000"
    else
        echo "⚠️  proxy_pass 可能未指向端口 3000"
    fi
else
    echo "⚠️  未找到 Nginx 配置文件"
fi

echo ""
echo "测试配置..."
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
    echo "重新加载 Nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx 已重新加载"
else
    echo "❌ Nginx 配置错误"
    sudo nginx -t
fi
echo ""

# 最终验证
echo "========================================"
echo "最终验证"
echo "========================================"
echo ""

echo "1. 前端进程:"
ps aux | grep -E "next.*dev|node.*3000" | grep -v grep | head -2 || echo "未找到进程"
echo ""

echo "2. 端口 3000:"
sudo netstat -tlnp | grep 3000 || sudo ss -tlnp | grep 3000 || echo "未监听"
echo ""

echo "3. 本地访问测试:"
curl -s -I http://localhost:3000 | head -3 || echo "无法访问"
echo ""

echo "4. Nginx 代理测试:"
curl -s -I http://localhost/group-ai/accounts | head -3 || echo "无法访问"
echo ""

echo "5. 域名访问测试:"
curl -s -I http://aikz.usdt2026.cc/group-ai/accounts | head -3 || echo "无法访问"
echo ""

echo "========================================"
echo "修复完成"
echo "========================================"
echo "日志文件: $LOG_FILE"
echo "前端日志: /tmp/frontend_502fix.log"
