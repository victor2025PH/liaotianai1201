#!/bin/bash
# ============================================================
# 完全修复 HTTPS 无法访问问题
# ============================================================

set -e

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"

echo "=========================================="
echo "🔒 完全修复 HTTPS 访问问题"
echo "=========================================="
echo ""

# 检查是否以 root 或 sudo 运行
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "❌ 此脚本需要 sudo 权限"
    echo "请使用: sudo bash $0"
    exit 1
fi

# 1. 检查前端和后端服务
echo "[1/8] 检查前端和后端服务..."
echo "----------------------------------------"
if curl -s http://127.0.0.1:3000 > /dev/null; then
    echo "✅ 前端服务正常运行"
else
    echo "❌ 前端服务无法访问"
    echo "   检查 PM2: pm2 list"
    echo "   重启前端: pm2 restart next-server"
fi

if curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "✅ 后端服务正常运行"
else
    echo "❌ 后端服务无法访问"
    echo "   检查 PM2: pm2 list"
    echo "   重启后端: pm2 restart backend"
fi
echo ""

# 2. 检查端口监听
echo "[2/8] 检查端口监听..."
echo "----------------------------------------"
if sudo ss -tlnp | grep -q ":3000 "; then
    echo "✅ 端口 3000 正在监听"
else
    echo "❌ 端口 3000 未监听"
fi

if sudo ss -tlnp | grep -q ":8000 "; then
    echo "✅ 端口 8000 正在监听"
else
    echo "❌ 端口 8000 未监听"
fi

if sudo ss -tlnp | grep -q ":443 "; then
    echo "✅ 端口 443 正在监听"
    sudo ss -tlnp | grep ":443 "
else
    echo "❌ 端口 443 未监听 - 这是 HTTPS 无法访问的主要原因"
fi
echo ""

# 3. 检查 Nginx 服务
echo "[3/8] 检查 Nginx 服务..."
echo "----------------------------------------"
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务正在运行"
else
    echo "❌ Nginx 服务未运行"
    echo "   启动 Nginx..."
    sudo systemctl start nginx
    sleep 2
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已启动"
    else
        echo "❌ Nginx 启动失败"
        sudo systemctl status nginx --no-pager | head -10
    fi
fi
echo ""

# 4. 检查 Nginx 配置
echo "[4/8] 检查 Nginx 配置..."
echo "----------------------------------------"
if [ ! -f "$NGINX_CONFIG" ]; then
    echo "❌ 配置文件不存在: $NGINX_CONFIG"
    exit 1
fi

# 检查是否有 HTTPS server 块
if grep -q "listen 443" "$NGINX_CONFIG"; then
    echo "✅ 配置中包含 HTTPS (443) server 块"
    
    # 检查 SSL 证书配置
    if grep -q "ssl_certificate" "$NGINX_CONFIG"; then
        echo "✅ 包含 SSL 证书配置"
        
        # 检查证书文件
        CERT_PATH=$(grep "ssl_certificate " "$NGINX_CONFIG" | awk '{print $2}' | tr -d ';' | head -1)
        if [ -n "$CERT_PATH" ] && [ -f "$CERT_PATH" ]; then
            echo "✅ SSL 证书文件存在: $CERT_PATH"
        else
            echo "❌ SSL 证书文件不存在: $CERT_PATH"
            echo "   需要重新获取证书"
        fi
    else
        echo "❌ 缺少 SSL 证书配置"
    fi
else
    echo "❌ 配置中缺少 HTTPS (443) server 块"
    echo "   需要添加 HTTPS 配置"
fi
echo ""

# 5. 检查配置文件链接
echo "[5/8] 检查配置文件链接..."
echo "----------------------------------------"
if [ -L "$NGINX_ENABLED" ] || [ -f "$NGINX_ENABLED" ]; then
    echo "✅ 配置文件链接存在"
    if [ -L "$NGINX_ENABLED" ]; then
        LINK_TARGET=$(readlink -f "$NGINX_ENABLED")
        echo "   指向: $LINK_TARGET"
    fi
else
    echo "⚠️  配置文件链接不存在，创建..."
    sudo ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"
    echo "✅ 链接已创建"
fi
echo ""

# 6. 测试 Nginx 配置
echo "[6/8] 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
    echo "✅ Nginx 配置语法正确"
else
    echo "❌ Nginx 配置有错误"
    echo "   查看详细错误："
    sudo nginx -t 2>&1 | tail -20
    exit 1
fi
echo ""

# 7. 如果缺少 HTTPS 配置，使用 Certbot 添加
echo "[7/8] 检查并添加 HTTPS 配置..."
echo "----------------------------------------"
if ! grep -q "listen 443" "$NGINX_CONFIG"; then
    echo "⚠️  缺少 HTTPS 配置，使用 Certbot 添加..."
    
    if command -v certbot &> /dev/null; then
        echo "使用 Certbot 自动配置 HTTPS..."
        echo "请选择选项 1（重新安装现有证书）"
        sudo certbot --nginx -d $DOMAIN
    else
        echo "❌ Certbot 未安装"
        echo "   安装命令: sudo apt-get install -y certbot python3-certbot-nginx"
        exit 1
    fi
else
    echo "✅ HTTPS 配置已存在"
fi
echo ""

# 8. 重新加载 Nginx
echo "[8/8] 重新加载 Nginx..."
echo "----------------------------------------"
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

# 9. 最终验证
echo "最终验证..."
echo "----------------------------------------"
sleep 3

# 检查端口
if sudo ss -tlnp | grep -q ":443 "; then
    echo "✅ 端口 443 正在监听"
    sudo ss -tlnp | grep ":443 "
else
    echo "❌ 端口 443 仍未监听"
    echo ""
    echo "查看 Nginx 错误日志："
    sudo tail -30 /var/log/nginx/error.log | grep -i "443\|ssl\|certificate" || sudo tail -30 /var/log/nginx/error.log
    echo ""
    echo "查看 Nginx 配置中的 HTTPS 部分："
    sudo grep -A 20 "listen 443" "$NGINX_CONFIG" || echo "未找到 listen 443"
fi
echo ""

# 测试连接
echo "测试连接..."
if curl -s -k -o /dev/null -w "HTTPS 本地: %{http_code}\n" https://127.0.0.1/ | grep -q "200\|301\|302"; then
    echo "✅ HTTPS 本地连接正常"
else
    HTTPS_CODE=$(curl -s -k -o /dev/null -w "%{http_code}" https://127.0.0.1/ || echo "000")
    echo "❌ HTTPS 本地连接失败 (状态码: $HTTPS_CODE)"
fi

if curl -s -o /dev/null -w "HTTP 本地: %{http_code}\n" http://127.0.0.1/ | grep -q "200\|301\|302"; then
    echo "✅ HTTP 本地连接正常"
else
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ || echo "000")
    echo "⚠️  HTTP 本地连接异常 (状态码: $HTTP_CODE)"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果端口 443 仍未监听，请："
echo "  1. 检查 Nginx 配置: sudo cat $NGINX_CONFIG | grep -A 10 'listen 443'"
echo "  2. 查看错误日志: sudo tail -50 /var/log/nginx/error.log"
echo "  3. 使用 Certbot: sudo certbot --nginx -d $DOMAIN"
echo ""

