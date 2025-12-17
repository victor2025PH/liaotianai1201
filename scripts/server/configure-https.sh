#!/bin/bash
# 配置 HTTPS 脚本

set -e

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/$DOMAIN"

echo "========================================="
echo "配置 HTTPS for $DOMAIN"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

success_msg() { echo -e "${GREEN}✅ $1${NC}"; }
info_msg() { echo -e "${YELLOW}ℹ️  $1${NC}"; }
error_msg() { echo -e "${RED}❌ $1${NC}"; }

# 步骤 1: 检查 Certbot 是否安装
echo "[1/5] 检查 Certbot..."
if ! command -v certbot &> /dev/null; then
    info_msg "Certbot 未安装，正在安装..."
    sudo apt-get update -qq
    sudo apt-get install -y certbot python3-certbot-nginx || error_exit "Certbot 安装失败"
fi
success_msg "Certbot 已安装: $(certbot --version)"
echo ""

# 步骤 2: 检查 Nginx 配置
echo "[2/5] 检查 Nginx 配置..."
if [ ! -f "$NGINX_CONFIG" ]; then
    error_msg "Nginx 配置文件不存在: $NGINX_CONFIG"
    exit 1
fi

# 检查是否已经配置了 HTTPS
if grep -q "listen 443" "$NGINX_CONFIG"; then
    info_msg "Nginx 配置中已包含 HTTPS (443 端口)"
    if grep -q "ssl_certificate" "$NGINX_CONFIG"; then
        success_msg "SSL 证书配置已存在"
        echo ""
        echo "如果仍然无法访问 HTTPS，请检查："
        echo "  1. 端口 443 是否监听: sudo ss -tlnp | grep :443"
        echo "  2. 防火墙是否允许 443: sudo ufw status"
        echo "  3. SSL 证书是否有效: sudo certbot certificates"
        exit 0
    fi
fi
echo ""

# 步骤 3: 检查端口 80 是否监听（Certbot 需要）
echo "[3/5] 检查端口 80..."
if sudo ss -tlnp | grep -q ":80 "; then
    success_msg "端口 80 正在监听"
else
    error_msg "端口 80 未监听，Certbot 需要端口 80 来验证域名"
    exit 1
fi
echo ""

# 步骤 4: 获取 SSL 证书
echo "[4/5] 获取 SSL 证书..."
info_msg "使用 Certbot 自动配置 HTTPS..."
info_msg "这可能需要几分钟..."

# 使用 Certbot 自动配置
sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@$DOMAIN --redirect || {
    error_msg "Certbot 配置失败"
    echo ""
    echo "常见问题："
    echo "  1. DNS 解析不正确 - 请检查: nslookup $DOMAIN"
    echo "  2. 端口 80 被防火墙阻止 - 请检查: sudo ufw status"
    echo "  3. 域名验证失败 - 请确保域名指向此服务器 IP"
    exit 1
}

success_msg "SSL 证书已获取并配置"
echo ""

# 步骤 5: 验证配置
echo "[5/5] 验证 HTTPS 配置..."

# 测试 Nginx 配置
if sudo nginx -t; then
    success_msg "Nginx 配置语法正确"
else
    error_msg "Nginx 配置有错误"
    exit 1
fi

# 重新加载 Nginx
sudo systemctl reload nginx
success_msg "Nginx 已重新加载"

# 检查端口 443
sleep 2
if sudo ss -tlnp | grep -q ":443 "; then
    success_msg "端口 443 (HTTPS) 正在监听"
else
    error_msg "端口 443 未监听"
fi

echo ""
echo "========================================="
echo "HTTPS 配置完成！"
echo "========================================="
echo ""
echo "现在可以访问:"
echo "  HTTPS: https://$DOMAIN"
echo "  HTTP: http://$DOMAIN (会自动重定向到 HTTPS)"
echo ""
echo "查看证书信息:"
echo "  sudo certbot certificates"
echo ""
