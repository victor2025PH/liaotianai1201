#!/bin/bash
# ============================================================
# 快速诊断连接拒绝错误 (ERR_CONNECTION_REFUSED)
# ============================================================

echo "=========================================="
echo "🔍 快速诊断连接拒绝错误"
echo "=========================================="
echo ""

# 1. 检查 Nginx 状态
echo "[1/6] 检查 Nginx 状态..."
echo "----------------------------------------"
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 正在运行"
    systemctl status nginx --no-pager | head -5
else
    echo "❌ Nginx 未运行！"
    echo "尝试启动 Nginx..."
    sudo systemctl start nginx
    sleep 2
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已启动"
    else
        echo "❌ Nginx 启动失败"
        echo "查看错误日志:"
        sudo journalctl -u nginx -n 20 --no-pager | tail -10
    fi
fi
echo ""

# 2. 检查端口 80 和 443
echo "[2/6] 检查端口 80 和 443..."
echo "----------------------------------------"
PORT_80=$(sudo ss -tlnp 2>/dev/null | grep ":80 " || echo "")
PORT_443=$(sudo ss -tlnp 2>/dev/null | grep ":443 " || echo "")

if [ -n "$PORT_80" ]; then
    echo "✅ 端口 80 正在监听"
    echo "  $PORT_80"
else
    echo "❌ 端口 80 未监听"
fi

if [ -n "$PORT_443" ]; then
    echo "✅ 端口 443 正在监听"
    echo "  $PORT_443"
else
    echo "⚠️  端口 443 未监听（如果使用 HTTPS）"
fi
echo ""

# 3. 检查前端服务
echo "[3/6] 检查前端服务..."
echo "----------------------------------------"
FRONTEND_SERVICE=""
if systemctl cat liaotian-frontend.service >/dev/null 2>&1; then
    FRONTEND_SERVICE="liaotian-frontend"
elif systemctl cat smart-tg-frontend.service >/dev/null 2>&1; then
    FRONTEND_SERVICE="smart-tg-frontend"
fi

if [ -n "$FRONTEND_SERVICE" ]; then
    STATUS=$(systemctl is-active "$FRONTEND_SERVICE" 2>/dev/null || echo "inactive")
    echo "  服务: $FRONTEND_SERVICE"
    echo "  状态: $STATUS"
    if [ "$STATUS" != "active" ]; then
        echo "  ❌ 前端服务未运行！"
        echo "  尝试启动: sudo systemctl start $FRONTEND_SERVICE"
    fi
else
    # 检查 PM2
    if command -v pm2 >/dev/null 2>&1; then
        echo "  检查 PM2 前端服务..."
        PM2_FRONTEND=$(sudo -u ubuntu pm2 list 2>/dev/null | grep frontend || echo "")
        if [ -n "$PM2_FRONTEND" ]; then
            echo "  ✅ PM2 前端服务存在"
            sudo -u ubuntu pm2 list | grep frontend
        else
            echo "  ❌ PM2 前端服务未找到"
        fi
    else
        echo "  ⚠️  未找到前端服务（systemd 或 PM2）"
    fi
fi
echo ""

# 4. 检查端口 3000
echo "[4/6] 检查端口 3000（前端）..."
echo "----------------------------------------"
PORT_3000=$(sudo ss -tlnp 2>/dev/null | grep ":3000 " || echo "")
if [ -n "$PORT_3000" ]; then
    echo "✅ 端口 3000 正在监听"
    echo "  $PORT_3000"
else
    echo "❌ 端口 3000 未监听（前端服务可能未启动）"
fi
echo ""

# 5. 检查后端服务
echo "[5/6] 检查后端服务..."
echo "----------------------------------------"
BACKEND_SERVICE=""
if systemctl cat luckyred-api.service >/dev/null 2>&1; then
    BACKEND_SERVICE="luckyred-api"
elif systemctl cat telegram-backend.service >/dev/null 2>&1; then
    BACKEND_SERVICE="telegram-backend"
fi

if [ -n "$BACKEND_SERVICE" ]; then
    STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "inactive")
    echo "  服务: $BACKEND_SERVICE"
    echo "  状态: $STATUS"
    if [ "$STATUS" != "active" ]; then
        echo "  ❌ 后端服务未运行！"
        echo "  尝试启动: sudo systemctl start $BACKEND_SERVICE"
    fi
else
    # 检查 PM2
    if command -v pm2 >/dev/null 2>&1; then
        echo "  检查 PM2 后端服务..."
        PM2_BACKEND=$(sudo -u ubuntu pm2 list 2>/dev/null | grep backend || echo "")
        if [ -n "$PM2_BACKEND" ]; then
            echo "  ✅ PM2 后端服务存在"
            sudo -u ubuntu pm2 list | grep backend
        else
            echo "  ❌ PM2 后端服务未找到"
        fi
    else
        echo "  ⚠️  未找到后端服务（systemd 或 PM2）"
    fi
fi
echo ""

# 6. 检查 Nginx 配置
echo "[6/6] 检查 Nginx 配置..."
echo "----------------------------------------"
NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
if [ -f "$NGINX_CONFIG" ]; then
    echo "✅ Nginx 配置文件存在: $NGINX_CONFIG"
    # 检查配置语法
    if sudo nginx -t 2>/dev/null; then
        echo "✅ Nginx 配置语法正确"
    else
        echo "❌ Nginx 配置语法错误"
        sudo nginx -t 2>&1 | head -10
    fi
else
    echo "❌ Nginx 配置文件不存在: $NGINX_CONFIG"
    echo "  需要运行部署脚本或手动创建配置"
fi
echo ""

# 总结
echo "=========================================="
echo "📋 诊断总结"
echo "=========================================="
echo ""
echo "如果 Nginx 未运行，执行: sudo systemctl start nginx"
echo "如果前端服务未运行，执行: sudo systemctl start $FRONTEND_SERVICE"
echo "如果后端服务未运行，执行: sudo systemctl start $BACKEND_SERVICE"
echo ""
echo "查看 Nginx 日志: sudo journalctl -u nginx -n 50"
echo "查看前端日志: sudo journalctl -u $FRONTEND_SERVICE -n 50"
echo "查看后端日志: sudo journalctl -u $BACKEND_SERVICE -n 50"
echo ""

