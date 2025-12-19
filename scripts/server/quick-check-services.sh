#!/bin/bash
# ============================================================
# 快速检查服务状态
# ============================================================

echo "=========================================="
echo "🔍 快速检查服务状态"
echo "=========================================="
echo ""

# 1. 检查 PM2 服务
echo "[1/5] 检查 PM2 服务..."
echo "----------------------------------------"
PM2_LIST=$(sudo -u ubuntu pm2 list 2>/dev/null)
if [ -z "$PM2_LIST" ]; then
    echo "❌ PM2 未运行或无法访问"
else
    echo "$PM2_LIST"
    echo ""
    
    # 检查服务状态
    if echo "$PM2_LIST" | grep -q "backend.*online"; then
        echo "✅ 后端服务: 运行中"
    else
        echo "❌ 后端服务: 未运行或异常"
    fi
    
    if echo "$PM2_LIST" | grep -q "frontend.*online"; then
        echo "✅ 前端服务: 运行中"
    else
        echo "❌ 前端服务: 未运行或异常"
    fi
fi
echo ""

# 2. 检查端口监听
echo "[2/5] 检查端口监听..."
echo "----------------------------------------"
PORT_3000=$(sudo ss -tlnp | grep ":3000" || echo "")
PORT_8000=$(sudo ss -tlnp | grep ":8000" || echo "")
PORT_80=$(sudo ss -tlnp | grep ":80 " || echo "")
PORT_443=$(sudo ss -tlnp | grep ":443 " || echo "")

if [ -n "$PORT_3000" ]; then
    echo "✅ 端口 3000 (前端): 监听中"
else
    echo "❌ 端口 3000 (前端): 未监听"
fi

if [ -n "$PORT_8000" ]; then
    echo "✅ 端口 8000 (后端): 监听中"
else
    echo "❌ 端口 8000 (后端): 未监听"
fi

if [ -n "$PORT_80" ]; then
    echo "✅ 端口 80 (HTTP): 监听中"
else
    echo "❌ 端口 80 (HTTP): 未监听"
fi

if [ -n "$PORT_443" ]; then
    echo "✅ 端口 443 (HTTPS): 监听中"
else
    echo "❌ 端口 443 (HTTPS): 未监听"
fi
echo ""

# 3. 检查 Nginx
echo "[3/5] 检查 Nginx 服务..."
echo "----------------------------------------"
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务: 运行中"
    if sudo nginx -t 2>&1 | grep -q "successful"; then
        echo "✅ Nginx 配置: 正确"
    else
        echo "❌ Nginx 配置: 有错误"
        sudo nginx -t 2>&1 | tail -5
    fi
else
    echo "❌ Nginx 服务: 未运行"
    echo "   尝试启动: sudo systemctl start nginx"
fi
echo ""

# 4. 测试本地连接
echo "[4/5] 测试本地连接..."
echo "----------------------------------------"
echo "测试前端 (端口 3000):"
FRONTEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_TEST" = "200" ] || [ "$FRONTEND_TEST" = "404" ]; then
    echo "✅ 前端响应: HTTP $FRONTEND_TEST"
else
    echo "❌ 前端无响应: HTTP $FRONTEND_TEST"
fi

echo "测试后端 (端口 8000):"
BACKEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_TEST" = "200" ]; then
    echo "✅ 后端响应: HTTP $BACKEND_TEST"
else
    echo "❌ 后端无响应: HTTP $BACKEND_TEST"
fi

echo "测试 Nginx (端口 80):"
NGINX_80_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1 2>/dev/null || echo "000")
if [ "$NGINX_80_TEST" = "200" ] || [ "$NGINX_80_TEST" = "301" ] || [ "$NGINX_80_TEST" = "302" ]; then
    echo "✅ Nginx HTTP 响应: HTTP $NGINX_80_TEST"
else
    echo "❌ Nginx HTTP 无响应: HTTP $NGINX_80_TEST"
fi

echo "测试 Nginx (端口 443):"
NGINX_443_TEST=$(curl -s -o /dev/null -w "%{http_code}" -k https://127.0.0.1 2>/dev/null || echo "000")
if [ "$NGINX_443_TEST" = "200" ] || [ "$NGINX_443_TEST" = "301" ] || [ "$NGINX_443_TEST" = "302" ]; then
    echo "✅ Nginx HTTPS 响应: HTTP $NGINX_443_TEST"
else
    echo "❌ Nginx HTTPS 无响应: HTTP $NGINX_443_TEST"
fi
echo ""

# 5. 快速修复建议
echo "[5/5] 快速修复建议..."
echo "----------------------------------------"

# 如果服务未运行，提供启动命令
if ! echo "$PM2_LIST" | grep -q "backend.*online"; then
    echo "❌ 后端服务未运行"
    echo "   启动命令: sudo -u ubuntu pm2 start ecosystem.config.js --only backend"
fi

if ! echo "$PM2_LIST" | grep -q "frontend.*online"; then
    echo "❌ 前端服务未运行"
    echo "   启动命令: sudo -u ubuntu pm2 start ecosystem.config.js --only frontend"
fi

if ! systemctl is-active --quiet nginx; then
    echo "❌ Nginx 未运行"
    echo "   启动命令: sudo systemctl start nginx"
fi

# 如果端口未监听，提供检查命令
if [ -z "$PORT_3000" ]; then
    echo "❌ 前端端口未监听"
    echo "   检查命令: sudo -u ubuntu pm2 logs frontend --lines 50"
fi

if [ -z "$PORT_8000" ]; then
    echo "❌ 后端端口未监听"
    echo "   检查命令: sudo -u ubuntu pm2 logs backend --lines 50"
fi

echo ""

# 6. 一键修复（如果服务未运行）
echo "=========================================="
echo "🔧 一键修复"
echo "=========================================="
echo ""

FIX_NEEDED=0

# 检查并启动 Nginx
if ! systemctl is-active --quiet nginx; then
    echo "启动 Nginx..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
    sleep 2
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已启动"
    else
        echo "❌ Nginx 启动失败"
        FIX_NEEDED=1
    fi
fi

# 检查并启动 PM2 服务
cd /home/ubuntu/telegram-ai-system || exit 1

if ! sudo -u ubuntu pm2 list 2>/dev/null | grep -q "backend.*online"; then
    echo "启动后端服务..."
    sudo -u ubuntu pm2 start ecosystem.config.js --only backend
    sleep 3
    if sudo -u ubuntu pm2 list 2>/dev/null | grep -q "backend.*online"; then
        echo "✅ 后端服务已启动"
    else
        echo "❌ 后端服务启动失败"
        FIX_NEEDED=1
    fi
fi

if ! sudo -u ubuntu pm2 list 2>/dev/null | grep -q "frontend.*online"; then
    echo "启动前端服务..."
    sudo -u ubuntu pm2 start ecosystem.config.js --only frontend
    sleep 3
    if sudo -u ubuntu pm2 list 2>/dev/null | grep -q "frontend.*online"; then
        echo "✅ 前端服务已启动"
    else
        echo "❌ 前端服务启动失败"
        FIX_NEEDED=1
    fi
fi

echo ""

# 7. 最终状态
echo "=========================================="
echo "📊 最终状态"
echo "=========================================="
echo ""

echo "PM2 服务:"
sudo -u ubuntu pm2 list 2>/dev/null || echo "PM2 未运行"
echo ""

echo "Nginx 状态:"
sudo systemctl status nginx --no-pager | head -5
echo ""

echo "端口监听:"
sudo ss -tlnp | grep -E ":(80|443|3000|8000)" || echo "未发现监听端口"
echo ""

if [ $FIX_NEEDED -eq 0 ]; then
    echo "✅ 所有服务已启动"
    echo ""
    echo "🌐 访问地址:"
    echo "   HTTPS: https://aikz.usdt2026.cc"
    echo "   HTTP: http://aikz.usdt2026.cc (自动重定向到 HTTPS)"
else
    echo "⚠️  部分服务启动失败，请检查日志:"
    echo "   后端日志: sudo -u ubuntu pm2 logs backend --lines 50"
    echo "   前端日志: sudo -u ubuntu pm2 logs frontend --lines 50"
    echo "   Nginx 日志: sudo tail -50 /var/log/nginx/error.log"
fi

echo ""
echo "=========================================="
echo "✅ 检查完成"
echo "=========================================="

