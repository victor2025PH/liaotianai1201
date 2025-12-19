#!/bin/bash
# ============================================================
# 诊断 HTTP 和 HTTPS 都无法访问的问题
# ============================================================

set -e

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"

echo "=========================================="
echo "🔍 诊断 HTTP/HTTPS 无法访问问题"
echo "=========================================="
echo ""

# 1. 检查 Nginx 服务状态
echo "[1/8] 检查 Nginx 服务状态..."
echo "----------------------------------------"
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务正在运行"
else
    echo "❌ Nginx 服务未运行"
    echo "   尝试启动: sudo systemctl start nginx"
fi
systemctl status nginx --no-pager | head -5
echo ""

# 2. 检查端口监听
echo "[2/8] 检查端口监听状态..."
echo "----------------------------------------"
if sudo ss -tlnp | grep -q ":80 "; then
    echo "✅ 端口 80 (HTTP) 正在监听"
    sudo ss -tlnp | grep ":80 "
else
    echo "❌ 端口 80 (HTTP) 未监听"
fi
echo ""

if sudo ss -tlnp | grep -q ":443 "; then
    echo "✅ 端口 443 (HTTPS) 正在监听"
    sudo ss -tlnp | grep ":443 "
else
    echo "❌ 端口 443 (HTTPS) 未监听"
fi
echo ""

# 3. 检查 Nginx 配置语法
echo "[3/8] 检查 Nginx 配置语法..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
    echo "✅ Nginx 配置语法正确"
else
    echo "❌ Nginx 配置有错误"
    echo "   请检查配置文件: $NGINX_CONFIG"
fi
echo ""

# 4. 检查前端服务（端口 3000）
echo "[4/8] 检查前端服务（端口 3000）..."
echo "----------------------------------------"
if sudo ss -tlnp | grep -q ":3000 "; then
    echo "✅ 前端服务正在运行（端口 3000）"
    sudo ss -tlnp | grep ":3000 "
    
    # 测试本地连接
    if curl -s http://127.0.0.1:3000 > /dev/null; then
        echo "✅ 前端服务可以正常响应"
    else
        echo "⚠️  前端服务无法响应（可能正在启动中）"
    fi
else
    echo "❌ 前端服务未运行（端口 3000）"
    echo "   检查 PM2: pm2 list"
    echo "   启动前端: cd /home/ubuntu/telegram-ai-system/saas-demo && pm2 start npm --name next-server -- start"
fi
echo ""

# 5. 检查后端服务（端口 8000）
echo "[5/8] 检查后端服务（端口 8000）..."
echo "----------------------------------------"
if sudo ss -tlnp | grep -q ":8000 "; then
    echo "✅ 后端服务正在运行（端口 8000）"
    sudo ss -tlnp | grep ":8000 "
    
    # 测试健康检查
    if curl -s http://127.0.0.1:8000/health > /dev/null; then
        echo "✅ 后端服务可以正常响应"
    else
        echo "⚠️  后端服务无法响应（可能正在启动中）"
    fi
else
    echo "❌ 后端服务未运行（端口 8000）"
    echo "   检查 PM2: pm2 list"
    echo "   启动后端: cd /home/ubuntu/telegram-ai-system/admin-backend && pm2 start ecosystem.config.js"
fi
echo ""

# 6. 检查 Nginx 配置内容
echo "[6/8] 检查 Nginx 配置内容..."
echo "----------------------------------------"
if [ -f "$NGINX_CONFIG" ]; then
    echo "✅ 配置文件存在: $NGINX_CONFIG"
    
    # 检查是否有 HTTP 配置
    if grep -q "listen 80" "$NGINX_CONFIG"; then
        echo "✅ 包含 HTTP (80) 配置"
    else
        echo "❌ 缺少 HTTP (80) 配置"
    fi
    
    # 检查是否有 HTTPS 配置
    if grep -q "listen 443" "$NGINX_CONFIG"; then
        echo "✅ 包含 HTTPS (443) 配置"
        
        # 检查 SSL 证书配置
        if grep -q "ssl_certificate" "$NGINX_CONFIG"; then
            echo "✅ 包含 SSL 证书配置"
        else
            echo "❌ 缺少 SSL 证书配置"
        fi
    else
        echo "❌ 缺少 HTTPS (443) 配置"
    fi
    
    # 检查代理配置
    if grep -q "proxy_pass.*127.0.0.1:3000" "$NGINX_CONFIG"; then
        echo "✅ 包含前端代理配置（端口 3000）"
    else
        echo "❌ 缺少前端代理配置"
    fi
    
    if grep -q "proxy_pass.*127.0.0.1:8000" "$NGINX_CONFIG"; then
        echo "✅ 包含后端代理配置（端口 8000）"
    else
        echo "❌ 缺少后端代理配置"
    fi
else
    echo "❌ 配置文件不存在: $NGINX_CONFIG"
fi
echo ""

# 7. 检查配置文件链接
echo "[7/8] 检查配置文件链接..."
echo "----------------------------------------"
if [ -L "$NGINX_ENABLED" ]; then
    echo "✅ 符号链接存在: $NGINX_ENABLED"
    echo "   指向: $(readlink -f $NGINX_ENABLED)"
else
    echo "❌ 符号链接不存在: $NGINX_ENABLED"
    echo "   创建链接: sudo ln -sf $NGINX_CONFIG $NGINX_ENABLED"
fi
echo ""

# 8. 测试本地连接
echo "[8/8] 测试本地连接..."
echo "----------------------------------------"
echo "测试 HTTP (本地):"
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ | grep -q "200\|301\|302"; then
    echo "✅ HTTP 本地连接正常"
else
    echo "❌ HTTP 本地连接失败"
    curl -v http://127.0.0.1/ 2>&1 | head -10
fi
echo ""

echo "测试 HTTPS (本地):"
if curl -s -k -o /dev/null -w "%{http_code}" https://127.0.0.1/ | grep -q "200\|301\|302"; then
    echo "✅ HTTPS 本地连接正常"
else
    echo "❌ HTTPS 本地连接失败"
    curl -k -v https://127.0.0.1/ 2>&1 | head -10
fi
echo ""

echo "=========================================="
echo "✅ 诊断完成"
echo "=========================================="
echo ""
echo "如果发现问题，请执行："
echo "  1. 修复 Nginx 配置: sudo nginx -t"
echo "  2. 重启 Nginx: sudo systemctl restart nginx"
echo "  3. 检查服务: pm2 list"
echo "  4. 重启服务: pm2 restart all"
echo ""

