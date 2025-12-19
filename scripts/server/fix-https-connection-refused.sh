#!/bin/bash
# ============================================================
# 修复 HTTPS 连接被拒绝问题
# ============================================================

set -e

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"

echo "=========================================="
echo "🔒 修复 HTTPS 连接问题"
echo "=========================================="
echo ""

# 检查是否以 root 或 sudo 运行
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "❌ 此脚本需要 sudo 权限"
    echo "请使用: sudo bash $0"
    exit 1
fi

# 1. 检查当前 Nginx 配置
echo "[1/6] 检查当前 Nginx 配置..."
echo "----------------------------------------"
if [ -f "$NGINX_CONFIG" ]; then
    echo "✅ 配置文件存在: $NGINX_CONFIG"
    if grep -q "listen 443" "$NGINX_CONFIG"; then
        echo "✅ 配置中已包含 HTTPS (443 端口)"
        if grep -q "ssl_certificate" "$NGINX_CONFIG"; then
            echo "✅ SSL 证书配置已存在"
        else
            echo "⚠️  HTTPS 配置存在但缺少 SSL 证书配置"
        fi
    else
        echo "❌ 配置中缺少 HTTPS (443 端口)"
        echo "   当前配置只有 HTTP (80 端口)"
    fi
else
    echo "❌ 配置文件不存在: $NGINX_CONFIG"
fi
echo ""

# 2. 检查端口监听状态
echo "[2/6] 检查端口监听状态..."
echo "----------------------------------------"
if sudo ss -tlnp | grep -q ":443 "; then
    echo "✅ 端口 443 正在监听"
    sudo ss -tlnp | grep ":443 "
else
    echo "❌ 端口 443 未监听"
    echo "   这是 HTTPS 无法访问的主要原因"
fi
echo ""

if sudo ss -tlnp | grep -q ":80 "; then
    echo "✅ 端口 80 正在监听"
else
    echo "⚠️  端口 80 未监听"
fi
echo ""

# 3. 检查防火墙
echo "[3/6] 检查防火墙配置..."
echo "----------------------------------------"
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(sudo ufw status | head -1)
    echo "防火墙状态: $UFW_STATUS"
    if sudo ufw status | grep -q "443/tcp"; then
        echo "✅ 防火墙已允许 443 端口"
    else
        echo "⚠️  防火墙未允许 443 端口"
        echo "   执行: sudo ufw allow 443/tcp"
    fi
else
    echo "ℹ️  ufw 未安装，跳过防火墙检查"
fi
echo ""

# 4. 检查 SSL 证书
echo "[4/6] 检查 SSL 证书..."
echo "----------------------------------------"
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"
if [ -d "$CERT_DIR" ]; then
    echo "✅ 证书目录存在: $CERT_DIR"
    if [ -f "$CERT_DIR/fullchain.pem" ] && [ -f "$CERT_DIR/privkey.pem" ]; then
        echo "✅ SSL 证书文件存在"
        CERT_EXPIRY=$(sudo openssl x509 -enddate -noout -in "$CERT_DIR/fullchain.pem" 2>/dev/null | cut -d= -f2)
        if [ -n "$CERT_EXPIRY" ]; then
            echo "   证书过期时间: $CERT_EXPIRY"
        fi
    else
        echo "❌ SSL 证书文件不存在"
    fi
else
    echo "❌ 证书目录不存在: $CERT_DIR"
    echo "   需要运行: sudo certbot --nginx -d $DOMAIN"
fi
echo ""

# 5. 检查 Certbot
echo "[5/6] 检查 Certbot..."
echo "----------------------------------------"
if command -v certbot &> /dev/null; then
    echo "✅ Certbot 已安装: $(certbot --version)"
    CERTBOT_CERTS=$(sudo certbot certificates 2>/dev/null | grep -A 5 "$DOMAIN" || echo "")
    if [ -n "$CERTBOT_CERTS" ]; then
        echo "✅ 找到 Certbot 证书:"
        echo "$CERTBOT_CERTS" | head -10
    else
        echo "⚠️  未找到 Certbot 证书"
    fi
else
    echo "❌ Certbot 未安装"
    echo "   安装命令: sudo apt-get install -y certbot python3-certbot-nginx"
fi
echo ""

# 6. 修复建议
echo "[6/6] 修复建议..."
echo "----------------------------------------"

# 检查是否需要添加 HTTPS 配置
if [ -f "$NGINX_CONFIG" ] && ! grep -q "listen 443" "$NGINX_CONFIG"; then
    echo "🔧 需要添加 HTTPS 配置"
    echo ""
    echo "选项 1: 使用 Certbot 自动配置（推荐）"
    echo "   sudo certbot --nginx -d $DOMAIN"
    echo ""
    echo "选项 2: 手动合并 HTTPS 配置"
    echo "   从项目目录复制 HTTPS 配置:"
    echo "   sudo cp $PROJECT_DIR/deploy/nginx/aikz-https.conf $NGINX_CONFIG"
    echo "   然后测试并重启 Nginx:"
    echo "   sudo nginx -t && sudo systemctl reload nginx"
    echo ""
elif [ -f "$NGINX_CONFIG" ] && grep -q "listen 443" "$NGINX_CONFIG" ] && ! grep -q "ssl_certificate" "$NGINX_CONFIG"; then
    echo "🔧 需要添加 SSL 证书配置"
    echo "   运行: sudo certbot --nginx -d $DOMAIN"
    echo ""
elif [ ! -d "$CERT_DIR" ]; then
    echo "🔧 需要获取 SSL 证书"
    echo "   运行: sudo certbot --nginx -d $DOMAIN"
    echo ""
elif ! sudo ss -tlnp | grep -q ":443 "; then
    echo "🔧 需要重启 Nginx 以启用 HTTPS"
    echo "   sudo nginx -t && sudo systemctl restart nginx"
    echo ""
fi

# 检查防火墙
if command -v ufw &> /dev/null && ! sudo ufw status | grep -q "443/tcp"; then
    echo "🔧 需要允许防火墙 443 端口"
    echo "   sudo ufw allow 443/tcp"
    echo ""
fi

echo "=========================================="
echo "✅ 检查完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请检查："
echo "  1. 域名 DNS 解析是否正确"
echo "  2. 服务器是否可以从外网访问"
echo "  3. 云服务商安全组是否允许 443 端口"
echo ""

