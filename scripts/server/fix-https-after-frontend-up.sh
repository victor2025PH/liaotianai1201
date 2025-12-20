#!/bin/bash
# ============================================================
# 修复前端服务正常但 HTTPS 无法访问的问题
# ============================================================

set -e

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"

echo "=========================================="
echo "🔒 修复 HTTPS 访问问题"
echo "=========================================="
echo ""

# 1. 检查前端服务
echo "[1/6] 检查前端服务..."
echo "----------------------------------------"
if curl -s http://127.0.0.1:3000 > /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000)
    echo "✅ 前端服务正常运行 (HTTP $HTTP_CODE)"
else
    echo "❌ 前端服务无法访问"
    echo "   请先修复前端服务"
    exit 1
fi
echo ""

# 2. 检查端口监听
echo "[2/6] 检查端口监听..."
echo "----------------------------------------"
if sudo ss -tlnp | grep -q ":3000 "; then
    echo "✅ 端口 3000 正在监听"
    sudo ss -tlnp | grep ":3000 "
else
    echo "❌ 端口 3000 未监听"
    exit 1
fi
echo ""

if sudo ss -tlnp | grep -q ":443 "; then
    echo "✅ 端口 443 正在监听"
    sudo ss -tlnp | grep ":443 "
else
    echo "❌ 端口 443 未监听"
    echo "   这是 HTTPS 无法访问的主要原因"
fi
echo ""

# 3. 检查 Nginx 配置
echo "[3/6] 检查 Nginx 配置..."
echo "----------------------------------------"
if [ ! -f "$NGINX_CONFIG" ]; then
    echo "❌ Nginx 配置文件不存在: $NGINX_CONFIG"
    exit 1
fi

# 检查是否有 HTTPS server 块
if grep -q "listen 443" "$NGINX_CONFIG"; then
    echo "✅ 配置中包含 HTTPS (443) server 块"
    
    # 检查 SSL 证书配置
    if grep -q "ssl_certificate" "$NGINX_CONFIG"; then
        echo "✅ 包含 SSL 证书配置"
        
        # 检查证书文件是否存在
        CERT_PATH=$(grep "ssl_certificate " "$NGINX_CONFIG" | awk '{print $2}' | tr -d ';' | head -1)
        if [ -n "$CERT_PATH" ] && [ -f "$CERT_PATH" ]; then
            echo "✅ SSL 证书文件存在: $CERT_PATH"
        else
            echo "❌ SSL 证书文件不存在: $CERT_PATH"
        fi
    else
        echo "❌ 缺少 SSL 证书配置"
    fi
else
    echo "❌ 配置中缺少 HTTPS (443) server 块"
    echo "   需要添加 HTTPS 配置"
fi
echo ""

# 4. 检查配置文件链接
echo "[4/6] 检查配置文件链接..."
echo "----------------------------------------"
if [ -L "$NGINX_ENABLED" ]; then
    echo "✅ 符号链接存在"
    LINK_TARGET=$(readlink -f "$NGINX_ENABLED")
    echo "   指向: $LINK_TARGET"
    if [ "$LINK_TARGET" = "$NGINX_CONFIG" ]; then
        echo "✅ 链接目标正确"
    else
        echo "⚠️  链接目标不匹配，重新创建..."
        sudo rm -f "$NGINX_ENABLED"
        sudo ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"
    fi
else
    echo "⚠️  符号链接不存在，创建..."
    sudo ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"
fi
echo ""

# 5. 测试 Nginx 配置
echo "[5/6] 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
    echo "✅ Nginx 配置语法正确"
else
    echo "❌ Nginx 配置有错误"
    echo "   请检查配置文件: $NGINX_CONFIG"
    exit 1
fi
echo ""

# 6. 重新加载/重启 Nginx
echo "[6/6] 重新加载 Nginx..."
echo "----------------------------------------"
echo "尝试重新加载..."
if sudo systemctl reload nginx 2>&1; then
    echo "✅ Nginx 已重新加载"
else
    echo "⚠️  重新加载失败，尝试重启..."
    sudo systemctl restart nginx
    sleep 2
fi

# 检查 Nginx 状态
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务正在运行"
else
    echo "❌ Nginx 服务未运行"
    sudo systemctl status nginx --no-pager | head -10
    exit 1
fi
echo ""

# 7. 验证端口监听
echo "验证端口监听..."
echo "----------------------------------------"
sleep 2

if sudo ss -tlnp | grep -q ":443 "; then
    echo "✅ 端口 443 正在监听"
    sudo ss -tlnp | grep ":443 "
else
    echo "❌ 端口 443 仍未监听"
    echo "   可能的原因："
    echo "   1. Nginx 配置中 HTTPS server 块有错误"
    echo "   2. SSL 证书文件路径不正确"
    echo "   3. 需要检查 Nginx 错误日志"
    echo ""
    echo "查看 Nginx 错误日志："
    sudo tail -20 /var/log/nginx/error.log | grep -i "443\|ssl\|certificate" || sudo tail -20 /var/log/nginx/error.log
fi
echo ""

# 8. 测试连接
echo "测试连接..."
echo "----------------------------------------"
echo "测试 HTTP (本地):"
if curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1/ | grep -q "200\|301\|302"; then
    echo "✅ HTTP 本地连接正常"
else
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ || echo "000")
    echo "⚠️  HTTP 本地连接异常 (状态码: $HTTP_CODE)"
fi

echo ""
echo "测试 HTTPS (本地):"
if curl -s -k -o /dev/null -w "HTTPS %{http_code}\n" https://127.0.0.1/ | grep -q "200\|301\|302"; then
    echo "✅ HTTPS 本地连接正常"
else
    HTTPS_CODE=$(curl -s -k -o /dev/null -w "%{http_code}" https://127.0.0.1/ || echo "000")
    echo "❌ HTTPS 本地连接失败 (状态码: $HTTPS_CODE)"
    
    if [ "$HTTPS_CODE" = "000" ]; then
        echo "   连接被拒绝，可能是端口 443 未监听"
    fi
fi
echo ""

# 9. 检查防火墙
echo "检查防火墙..."
echo "----------------------------------------"
if command -v ufw &> /dev/null; then
    if sudo ufw status | grep -q "443/tcp"; then
        echo "✅ 防火墙允许 443 端口"
    else
        echo "⚠️  防火墙未允许 443 端口"
        echo "   执行: sudo ufw allow 443/tcp"
    fi
else
    echo "ℹ️  ufw 未安装"
fi
echo ""

echo "=========================================="
echo "✅ 检查完成"
echo "=========================================="
echo ""
echo "如果端口 443 仍未监听，请："
echo "  1. 检查 Nginx 配置: sudo cat $NGINX_CONFIG | grep -A 5 'listen 443'"
echo "  2. 检查 SSL 证书: sudo ls -la /etc/letsencrypt/live/$DOMAIN/"
echo "  3. 查看 Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo "  4. 使用 Certbot 重新配置: sudo certbot --nginx -d $DOMAIN"
echo ""

