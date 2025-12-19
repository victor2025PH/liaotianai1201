#!/bin/bash
# ============================================================
# 修复后端端口未监听和 HTTPS 端口未监听问题
# ============================================================

echo "=========================================="
echo "🔧 修复后端和 HTTPS 问题"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"

# 1. 检查后端服务
echo "[1/4] 检查并修复后端服务..."
echo "----------------------------------------"
echo "检查后端进程:"
BACKEND_PID=$(sudo -u ubuntu pm2 list 2>/dev/null | grep backend | awk '{print $10}' || echo "")
if [ -n "$BACKEND_PID" ]; then
    echo "后端 PM2 PID: $BACKEND_PID"
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "✅ 后端进程存在"
    else
        echo "❌ 后端进程不存在（PM2 显示 online 但进程已退出）"
    fi
fi
echo ""

echo "检查端口 8000:"
PORT_8000=$(sudo ss -tlnp | grep ":8000" || echo "")
if [ -z "$PORT_8000" ]; then
    echo "❌ 端口 8000 未监听"
    echo "查看后端日志:"
    sudo -u ubuntu pm2 logs backend --lines 30 --nostream 2>&1 | tail -30
    echo ""
    
    echo "重启后端服务..."
    sudo -u ubuntu pm2 stop backend 2>/dev/null || true
    sudo -u ubuntu pm2 delete backend 2>/dev/null || true
    sleep 2
    
    # 清理端口
    sudo lsof -t -i:8000 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
    sleep 2
    
    # 检查虚拟环境
    if [ ! -f "$BACKEND_DIR/venv/bin/uvicorn" ]; then
        echo "虚拟环境不完整，正在重建..."
        cd "$BACKEND_DIR" || exit 1
        rm -rf venv
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip --quiet
        pip install -r requirements.txt --quiet
        echo "✅ 虚拟环境已重建"
    fi
    
    # 启动后端
    cd "$PROJECT_DIR" || exit 1
    sudo -u ubuntu pm2 start ecosystem.config.js --only backend
    echo "✅ 后端服务已重启"
    
    # 等待启动
    echo "等待后端启动 (10秒)..."
    sleep 10
    
    # 验证
    NEW_PORT_8000=$(sudo ss -tlnp | grep ":8000" || echo "")
    if [ -n "$NEW_PORT_8000" ]; then
        echo "✅ 端口 8000 现在正在监听"
        echo "   $NEW_PORT_8000"
    else
        echo "❌ 端口 8000 仍然未监听"
        echo "查看详细日志:"
        sudo -u ubuntu pm2 logs backend --lines 50 --nostream 2>&1 | tail -50
    fi
else
    echo "✅ 端口 8000 正在监听"
    echo "   $PORT_8000"
fi
echo ""

# 2. 检查 HTTPS 配置
echo "[2/4] 检查 HTTPS 配置..."
echo "----------------------------------------"
PORT_443=$(sudo ss -tlnp | grep ":443 " || echo "")
if [ -z "$PORT_443" ]; then
    echo "❌ 端口 443 未监听"
    echo "检查 Nginx 配置..."
    
    if [ -f "$NGINX_CONFIG" ]; then
        if grep -q "listen 443" "$NGINX_CONFIG"; then
            echo "✅ Nginx 配置包含 HTTPS (端口 443)"
            
            # 检查 SSL 证书
            if [ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
                echo "✅ SSL 证书存在"
                
                # 测试 Nginx 配置
                if sudo nginx -t 2>&1 | grep -q "successful"; then
                    echo "✅ Nginx 配置语法正确"
                    echo "重新加载 Nginx..."
                    sudo systemctl reload nginx
                    sleep 3
                    
                    NEW_PORT_443=$(sudo ss -tlnp | grep ":443 " || echo "")
                    if [ -n "$NEW_PORT_443" ]; then
                        echo "✅ 端口 443 现在正在监听"
                    else
                        echo "❌ 端口 443 仍然未监听"
                        echo "检查 Nginx 错误日志:"
                        sudo tail -20 /var/log/nginx/error.log
                    fi
                else
                    echo "❌ Nginx 配置语法错误"
                    sudo nginx -t
                fi
            else
                echo "❌ SSL 证书不存在"
                echo "请运行: sudo bash scripts/server/setup-https-ssl.sh"
            fi
        else
            echo "❌ Nginx 配置不包含 HTTPS"
            echo "请运行: sudo bash scripts/server/setup-https-ssl.sh"
        fi
    else
        echo "❌ Nginx 配置文件不存在"
    fi
else
    echo "✅ 端口 443 正在监听"
    echo "   $PORT_443"
fi
echo ""

# 3. 测试服务连接
echo "[3/4] 测试服务连接..."
echo "----------------------------------------"
echo "测试后端 /health:"
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    echo "✅ 后端健康检查成功 (HTTP $BACKEND_HEALTH)"
else
    echo "❌ 后端健康检查失败: HTTP $BACKEND_HEALTH"
fi

echo "测试 HTTPS:"
HTTPS_TEST=$(curl -s -o /dev/null -w "%{http_code}" -k https://127.0.0.1 2>/dev/null || echo "000")
if [ "$HTTPS_TEST" = "200" ] || [ "$HTTPS_TEST" = "301" ] || [ "$HTTPS_TEST" = "302" ]; then
    echo "✅ HTTPS 连接成功 (HTTP $HTTPS_TEST)"
else
    echo "❌ HTTPS 连接失败: HTTP $HTTPS_TEST"
fi

echo "测试 HTTP 到 HTTPS 重定向:"
HTTP_REDIRECT=$(curl -s -o /dev/null -w "%{http_code}" -L http://127.0.0.1 2>/dev/null || echo "000")
if [ "$HTTP_REDIRECT" = "200" ]; then
    echo "✅ HTTP 到 HTTPS 重定向成功"
else
    echo "⚠️  HTTP 重定向: HTTP $HTTP_REDIRECT"
fi
echo ""

# 4. 最终状态
echo "[4/4] 最终状态..."
echo "----------------------------------------"
echo "PM2 服务:"
sudo -u ubuntu pm2 list
echo ""

echo "端口监听:"
sudo ss -tlnp | grep -E ":(80|443|3000|8000)" || echo "未发现监听端口"
echo ""

echo "Nginx 状态:"
sudo systemctl status nginx --no-pager | head -5
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请检查:"
echo "1. 后端日志: sudo -u ubuntu pm2 logs backend --lines 100"
echo "2. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo "3. 后端进程: ps aux | grep uvicorn"
echo ""

