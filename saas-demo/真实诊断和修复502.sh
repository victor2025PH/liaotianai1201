#!/bin/bash
# 真实诊断和修复 502 - 必须以实际结果为准

set -e

cd ~/liaotian/saas-demo

echo "========================================"
echo "真实诊断和修复 502"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 步骤 1: 确认项目
echo "[步骤 1] 确认项目..."
if [ ! -f "package.json" ] || ! grep -q '"next"' package.json; then
    echo "❌ 不是 Next.js 项目"
    exit 1
fi
echo "✅ Next.js 项目确认"
echo ""

# 步骤 2: 检查端口配置
echo "[步骤 2] 检查端口配置..."
if ! grep -q '"dev": "next dev -p 3000"' package.json; then
    echo "修复端口配置..."
    sed -i 's/"dev": "next dev -p 3001"/"dev": "next dev -p 3000"/g' package.json
    sed -i 's/"dev": "next dev"/"dev": "next dev -p 3000"/g' package.json
    echo "✅ 端口已修复为 3000"
fi
echo ""

# 步骤 3: 停止旧进程
echo "[步骤 3] 停止旧进程..."
pkill -f "next.*dev|node.*3000" || true
sleep 3
sudo lsof -i :3000 2>/dev/null | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true
sleep 2
echo "✅ 完成"
echo ""

# 步骤 4: 检查依赖
echo "[步骤 4] 检查依赖..."
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/next" ]; then
    echo "安装依赖..."
    npm install 2>&1 | tail -30
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
fi
echo "✅ 依赖正常"
echo ""

# 步骤 5: 前台启动查看真实错误
echo "[步骤 5] 前台启动查看真实错误..."
echo "启动前端服务（30秒超时）..."
timeout 30 npm run dev 2>&1 | tee /tmp/frontend_foreground.log || EXIT_CODE=$?

if [ -n "$EXIT_CODE" ]; then
    echo ""
    echo "⚠️  前端启动异常，查看错误:"
    cat /tmp/frontend_foreground.log
    echo ""
    echo "分析错误并修复..."
    
    # 检查常见错误
    if grep -q "Cannot find module\|Module not found" /tmp/frontend_foreground.log; then
        echo "发现模块缺失错误，重新安装依赖..."
        rm -rf node_modules package-lock.json
        npm install
    fi
    
    if grep -q "TypeScript error\|SyntaxError" /tmp/frontend_foreground.log; then
        echo "发现代码错误，查看详细日志..."
        cat /tmp/frontend_foreground.log | grep -i "error" | head -20
    fi
fi
echo ""

# 步骤 6: 后台启动并验证
echo "[步骤 6] 后台启动并验证..."
pkill -f "next.*dev|node.*3000" || true
sleep 2

npm run dev > /tmp/frontend_background.log 2>&1 &
DEV_PID=$!
echo "前端已启动 PID: $DEV_PID"

echo "等待服务启动（60秒）..."
sleep 60

# 验证进程
if ! ps -p $DEV_PID > /dev/null 2>&1; then
    echo "❌ 进程已退出，查看错误日志:"
    tail -50 /tmp/frontend_background.log
    exit 1
fi

# 验证端口
echo "验证端口 3000..."
if ! curl -s --max-time 5 http://localhost:3000 > /dev/null 2>&1; then
    echo "❌ 端口 3000 无法访问"
    echo "查看启动日志:"
    tail -50 /tmp/frontend_background.log
    exit 1
fi

# 验证 HTTP 状态码
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3000)
echo "HTTP 状态码: $HTTP_CODE"

if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "301" ] && [ "$HTTP_CODE" != "302" ] && [ "$HTTP_CODE" != "304" ]; then
    echo "❌ HTTP 状态码异常: $HTTP_CODE"
    tail -50 /tmp/frontend_background.log
    exit 1
fi

echo "✅ 前端服务正常运行"
echo ""

# 步骤 7: 检查后端
echo "[步骤 7] 检查后端服务..."
if ! curl -s --max-time 5 http://localhost:8000/health | grep -q "ok\|status"; then
    echo "后端未运行，启动后端..."
    cd ~/liaotian/admin-backend
    
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        pkill -f "uvicorn.*app.main:app" || true
        sleep 2
        nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
        sleep 8
        
        if curl -s --max-time 5 http://localhost:8000/health | grep -q "ok\|status"; then
            echo "✅ 后端服务已启动"
        else
            echo "❌ 后端服务启动失败"
            tail -30 /tmp/backend.log
        fi
    else
        echo "❌ 后端虚拟环境不存在"
    fi
    cd ../saas-demo
else
    echo "✅ 后端服务正常运行"
fi
echo ""

# 步骤 8: 检查 Nginx
echo "[步骤 8] 检查 Nginx 配置..."
NGINX_FILE="/etc/nginx/sites-enabled/default"

if [ -f "$NGINX_FILE" ]; then
    if grep -q "proxy_pass.*127.0.0.1:3000" "$NGINX_FILE"; then
        echo "✅ Nginx 配置正确"
    else
        echo "⚠️  检查 Nginx proxy_pass 配置..."
        grep "proxy_pass" "$NGINX_FILE" | head -3
    fi
    
    if sudo nginx -t 2>&1 | grep -q "successful"; then
        echo "✅ Nginx 配置语法正确"
        sudo systemctl reload nginx
        echo "✅ Nginx 已重载"
    else
        echo "❌ Nginx 配置错误:"
        sudo nginx -t
    fi
fi
echo ""

# 步骤 9: 最终验证
echo "[步骤 9] 最终验证..."
sleep 5

echo "1. 前端服务 (localhost:3000):"
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3000)
echo "   HTTP $FRONTEND_CODE"

echo "2. 后端服务 (localhost:8000/health):"
BACKEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8000/health)
echo "   HTTP $BACKEND_CODE"

echo "3. 域名访问 (aikz.usdt2026.cc/group-ai/accounts):"
DOMAIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://aikz.usdt2026.cc/group-ai/accounts)
echo "   HTTP $DOMAIN_CODE"
echo ""

# 结果判断
SUCCESS=true

if [ "$FRONTEND_CODE" != "200" ] && [ "$FRONTEND_CODE" != "301" ] && [ "$FRONTEND_CODE" != "302" ] && [ "$FRONTEND_CODE" != "304" ]; then
    echo "❌ 前端服务异常: HTTP $FRONTEND_CODE"
    SUCCESS=false
fi

if [ "$BACKEND_CODE" != "200" ] && [ "$BACKEND_CODE" != "301" ] && [ "$BACKEND_CODE" != "302" ]; then
    echo "❌ 后端服务异常: HTTP $BACKEND_CODE"
    SUCCESS=false
fi

if [ "$DOMAIN_CODE" = "502" ]; then
    echo "❌ 域名访问仍然是 502"
    echo "查看 Nginx 错误日志:"
    sudo tail -30 /var/log/nginx/error.log
    SUCCESS=false
elif [ "$DOMAIN_CODE" != "200" ] && [ "$DOMAIN_CODE" != "301" ] && [ "$DOMAIN_CODE" != "302" ] && [ "$DOMAIN_CODE" != "304" ]; then
    echo "⚠️  域名访问状态码: HTTP $DOMAIN_CODE"
    SUCCESS=false
fi

echo ""
echo "========================================"
if [ "$SUCCESS" = true ]; then
    echo "✅ 修复成功！所有服务正常"
    echo "========================================"
    exit 0
else
    echo "❌ 修复未完成，继续排查..."
    echo "========================================"
    exit 1
fi
