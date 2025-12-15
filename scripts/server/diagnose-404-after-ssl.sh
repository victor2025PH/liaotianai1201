#!/bin/bash
# ============================================================
# 诊断 SSL 配置后的 404 错误
# ============================================================

set +e

echo "=========================================="
echo "🔍 诊断 404 错误（SSL 配置后）"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

DOMAIN="aikz.usdt2026.cc"
BACKEND_SERVICE="luckyred-api"
FRONTEND_SERVICE="liaotian-frontend"

# 1. 检查服务状态
echo "[1/6] 检查服务状态..."
echo "----------------------------------------"
if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    echo "✅ 后端服务运行中"
else
    echo "❌ 后端服务未运行"
    systemctl status "$BACKEND_SERVICE" --no-pager -l | head -10
fi

if systemctl is-active --quiet "$FRONTEND_SERVICE"; then
    echo "✅ 前端服务运行中"
else
    echo "❌ 前端服务未运行"
    systemctl status "$FRONTEND_SERVICE" --no-pager -l | head -10
fi
echo ""

# 2. 检查端口监听
echo "[2/6] 检查端口监听..."
echo "----------------------------------------"
PORT_8000=$(lsof -ti:8000 2>/dev/null || true)
PORT_3000=$(lsof -ti:3000 2>/dev/null || true)

if [ -n "$PORT_8000" ]; then
    echo "✅ 端口 8000 正在监听 (PID: $PORT_8000)"
else
    echo "❌ 端口 8000 未监听"
fi

if [ -n "$PORT_3000" ]; then
    echo "✅ 端口 3000 正在监听 (PID: $PORT_3000)"
else
    echo "❌ 端口 3000 未监听"
fi
echo ""

# 3. 测试本地服务
echo "[3/6] 测试本地服务..."
echo "----------------------------------------"
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    echo "✅ 后端健康检查: HTTP 200"
else
    echo "❌ 后端健康检查: HTTP $BACKEND_HEALTH"
fi

FRONTEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/login 2>/dev/null || echo "000")
if [ "$FRONTEND_TEST" = "200" ]; then
    echo "✅ 前端登录页面: HTTP 200"
else
    echo "❌ 前端登录页面: HTTP $FRONTEND_TEST"
fi
echo ""

# 4. 检查 Nginx 配置
echo "[4/6] 检查 Nginx 配置..."
echo "----------------------------------------"
if nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
else
    echo "❌ Nginx 配置语法错误"
    nginx -t
fi

# 检查 HTTPS server 块
HTTPS_BLOCK=$(nginx -T 2>/dev/null | grep -A 20 "server_name $DOMAIN" | grep -A 20 "listen 443" || true)
if [ -n "$HTTPS_BLOCK" ]; then
    echo "✅ 找到 HTTPS server 块"
    
    # 检查 /login 路由
    if echo "$HTTPS_BLOCK" | grep -q "location /login"; then
        echo "✅ 找到 /login 路由配置"
        echo "$HTTPS_BLOCK" | grep -A 5 "location /login"
    else
        echo "❌ 未找到 /login 路由配置"
    fi
    
    # 检查 /api 路由
    if echo "$HTTPS_BLOCK" | grep -q "location /api"; then
        echo "✅ 找到 /api 路由配置"
    else
        echo "❌ 未找到 /api 路由配置"
    fi
    
    # 检查根路径
    if echo "$HTTPS_BLOCK" | grep -q "location /"; then
        echo "✅ 找到根路径配置"
    else
        echo "❌ 未找到根路径配置"
    fi
else
    echo "❌ 未找到 HTTPS server 块"
fi
echo ""

# 5. 检查 Nginx 错误日志
echo "[5/6] 检查 Nginx 错误日志（最近20行）..."
echo "----------------------------------------"
NGINX_ERRORS=$(tail -20 /var/log/nginx/error.log 2>/dev/null | grep -iE "404|502|upstream|connect|3000|8000" || true)
if [ -n "$NGINX_ERRORS" ]; then
    echo "发现相关错误:"
    echo "$NGINX_ERRORS"
else
    echo "✅ 未发现相关错误"
fi
echo ""

# 6. 测试 HTTPS 访问
echo "[6/6] 测试 HTTPS 访问..."
echo "----------------------------------------"
HTTPS_LOGIN=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/login 2>/dev/null || echo "000")
if [ "$HTTPS_LOGIN" = "200" ]; then
    echo "✅ HTTPS /login: HTTP 200"
elif [ "$HTTPS_LOGIN" = "404" ]; then
    echo "❌ HTTPS /login: HTTP 404 (Not Found)"
    echo "   可能原因:"
    echo "   1. 前端服务未运行"
    echo "   2. Nginx 配置错误（/login 路由未正确配置）"
    echo "   3. 前端构建不完整"
else
    echo "⚠️  HTTPS /login: HTTP $HTTPS_LOGIN"
fi

HTTPS_API=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/api/v1/health 2>/dev/null || echo "000")
if [ "$HTTPS_API" = "200" ] || [ "$HTTPS_API" = "404" ] || [ "$HTTPS_API" = "401" ]; then
    echo "✅ HTTPS /api: HTTP $HTTPS_API"
else
    echo "⚠️  HTTPS /api: HTTP $HTTPS_API"
fi
echo ""

# 总结和建议
echo "=========================================="
echo "📋 诊断总结"
echo "=========================================="
echo ""

if [ "$FRONTEND_TEST" != "200" ] || [ -z "$PORT_3000" ]; then
    echo "❌ 问题: 前端服务未正常运行"
    echo ""
    echo "解决方案:"
    echo "1. 检查前端服务状态:"
    echo "   sudo systemctl status $FRONTEND_SERVICE"
    echo ""
    echo "2. 查看前端服务日志:"
    echo "   sudo journalctl -u $FRONTEND_SERVICE -n 50 --no-pager"
    echo ""
    echo "3. 检查前端构建:"
    echo "   ls -la /home/ubuntu/telegram-ai-system/saas-demo/.next/standalone/"
    echo ""
    echo "4. 如果构建不存在，重新构建:"
    echo "   cd /home/ubuntu/telegram-ai-system/saas-demo"
    echo "   npm run build"
fi

if [ "$HTTPS_LOGIN" = "404" ] && [ "$FRONTEND_TEST" = "200" ]; then
    echo "❌ 问题: 前端服务正常，但 Nginx 路由配置错误"
    echo ""
    echo "解决方案:"
    echo "1. 重新配置 Nginx:"
    echo "   cd /home/ubuntu/telegram-ai-system"
    echo "   sudo bash scripts/server/reset-nginx-config.sh"
    echo ""
    echo "2. 检查 Nginx 配置:"
    echo "   sudo nginx -T | grep -A 10 'location /login'"
fi

echo ""

