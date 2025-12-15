#!/bin/bash
# ============================================================
# 验证前端服务状态
# ============================================================

set +e

echo "=========================================="
echo "🔍 验证前端服务状态"
echo "=========================================="
echo ""

FRONTEND_PORT=3000

# 1. 检查端口监听
echo "[1/4] 检查端口 $FRONTEND_PORT 监听..."
echo "----------------------------------------"
PORT_PID=$(sudo lsof -ti:$FRONTEND_PORT 2>/dev/null || true)
if [ -n "$PORT_PID" ]; then
    echo "✅ 端口 $FRONTEND_PORT 正在监听"
    echo "进程信息:"
    ps -fp $PORT_PID 2>/dev/null | head -5
    echo ""
    
    # 检查进程命令
    PROCESS_CMD=$(ps -fp $PORT_PID -o cmd= 2>/dev/null || echo "")
    if echo "$PROCESS_CMD" | grep -q "next\|node"; then
        echo "✅ 检测到 Next.js/Node.js 进程"
    fi
else
    echo "❌ 端口 $FRONTEND_PORT 未监听"
fi
echo ""

# 2. 检查 PM2 进程
echo "[2/4] 检查 PM2 进程..."
echo "----------------------------------------"
if command -v pm2 &> /dev/null; then
    PM2_LIST=$(pm2 list 2>/dev/null)
    if [ -n "$PM2_LIST" ]; then
        echo "$PM2_LIST"
        echo ""
        
        # 检查 frontend 进程状态
        FRONTEND_STATUS=$(pm2 list | grep frontend | awk '{print $10}' || echo "")
        if [ "$FRONTEND_STATUS" = "online" ]; then
            echo "✅ PM2 frontend 进程状态: online"
        else
            echo "⚠️  PM2 frontend 进程状态: $FRONTEND_STATUS"
            echo "查看日志: pm2 logs frontend --lines 50"
        fi
    else
        echo "⚠️  PM2 未运行或没有进程"
    fi
else
    echo "⚠️  PM2 未安装"
fi
echo ""

# 3. 测试本地连接
echo "[3/4] 测试本地连接..."
echo "----------------------------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$FRONTEND_PORT/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
    echo "✅ 前端服务响应正常 (HTTP $HTTP_CODE)"
    
    # 测试 /login 路由
    LOGIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$FRONTEND_PORT/login 2>/dev/null || echo "000")
    if [ "$LOGIN_CODE" = "200" ]; then
        echo "✅ /login 路由响应正常 (HTTP 200)"
    else
        echo "⚠️  /login 路由响应异常 (HTTP $LOGIN_CODE)"
    fi
else
    echo "❌ 前端服务响应异常 (HTTP $HTTP_CODE)"
    echo ""
    echo "可能原因:"
    echo "1. 前端服务未完全启动（等待 30-60 秒后重试）"
    echo "2. 前端服务启动失败（查看日志: pm2 logs frontend）"
    echo "3. 端口被其他进程占用"
fi
echo ""

# 4. 检查 Nginx 错误日志
echo "[4/4] 检查 Nginx 错误日志（最近10行）..."
echo "----------------------------------------"
NGINX_ERRORS=$(sudo tail -10 /var/log/nginx/error.log | grep -iE "3000|frontend|upstream" || true)
if [ -n "$NGINX_ERRORS" ]; then
    echo "发现相关错误:"
    echo "$NGINX_ERRORS"
else
    echo "✅ 未发现相关错误"
fi
echo ""

echo "=========================================="
echo "📋 总结"
echo "=========================================="
echo ""

if [ -n "$PORT_PID" ] && [ "$HTTP_CODE" = "200" ]; then
    echo "✅ 前端服务运行正常"
    echo ""
    echo "如果 HTTPS /login 仍然返回 502，请检查:"
    echo "1. Nginx 配置是否正确: sudo nginx -t"
    echo "2. Nginx 是否已重新加载: sudo systemctl reload nginx"
    echo "3. 等待 30 秒后再次测试: curl -I https://aikz.usdt2026.cc/login"
else
    echo "⚠️  前端服务可能未完全启动"
    echo ""
    echo "建议操作:"
    echo "1. 查看 PM2 日志: pm2 logs frontend --lines 50"
    echo "2. 检查前端服务目录: cd /home/ubuntu/telegram-ai-system/saas-demo"
    echo "3. 手动启动测试: npm run start"
    echo "4. 等待 30-60 秒后再次运行此脚本验证"
fi
echo ""

