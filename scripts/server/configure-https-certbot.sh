#!/bin/bash
# ============================================================
# 使用 Certbot 配置 HTTPS
# ============================================================
# 
# 功能：
# 1. 安装 Certbot
# 2. 获取 SSL 证书
# 3. 自动配置 Nginx HTTPS
# 4. 设置自动续期
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success_msg() { echo -e "${GREEN}✅ $1${NC}"; }
error_msg() { echo -e "${RED}❌ $1${NC}"; }
info_msg() { echo -e "${YELLOW}ℹ️  $1${NC}"; }
step_msg() { echo -e "${BLUE}📌 $1${NC}"; }

echo "========================================="
echo "配置 HTTPS (使用 Certbot)"
echo "========================================="
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then 
    error_msg "请使用 sudo 运行此脚本"
    exit 1
fi

# 检查 Nginx 是否运行
if ! systemctl is-active --quiet nginx; then
    error_msg "Nginx 未运行，请先配置 Nginx"
    exit 1
fi

# 询问域名和邮箱
echo "请输入您的域名（例如：aikz.usdt2026.cc）："
read -r DOMAIN

if [ -z "$DOMAIN" ]; then
    error_msg "域名不能为空"
    exit 1
fi

echo "请输入您的邮箱（用于证书到期提醒）："
read -r EMAIL

if [ -z "$EMAIL" ]; then
    error_msg "邮箱不能为空"
    exit 1
fi

info_msg "域名: $DOMAIN"
info_msg "邮箱: $EMAIL"
echo ""

# 1. 安装 Certbot
step_msg "[1/4] 安装 Certbot..."

if command -v certbot > /dev/null 2>&1; then
    success_msg "Certbot 已安装: $(certbot --version | head -1)"
else
    info_msg "安装 Certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
    
    if command -v certbot > /dev/null 2>&1; then
        success_msg "Certbot 安装成功"
    else
        error_msg "Certbot 安装失败"
        exit 1
    fi
fi
echo ""

# 2. 验证域名解析
step_msg "[2/4] 验证域名解析..."

SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "")
DOMAIN_IP=$(dig +short "$DOMAIN" @8.8.8.8 2>/dev/null | head -1 || echo "")

if [ -z "$DOMAIN_IP" ]; then
    error_msg "无法解析域名 $DOMAIN"
    echo "请确保："
    echo "  1. 域名 DNS A 记录已正确配置"
    echo "  2. DNS 已生效（可能需要等待几分钟）"
    exit 1
fi

info_msg "域名 $DOMAIN 解析到: $DOMAIN_IP"

if [ -n "$SERVER_IP" ] && [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
    info_msg "服务器公网 IP: $SERVER_IP"
    warning_msg "⚠️  域名解析的 IP ($DOMAIN_IP) 与服务器 IP ($SERVER_IP) 不一致"
    echo "请确认域名是否正确指向此服务器"
    echo ""
    read -p "是否继续？(y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    success_msg "域名解析正常"
fi
echo ""

# 3. 获取 SSL 证书
step_msg "[3/4] 获取 SSL 证书..."

info_msg "正在为 $DOMAIN 获取 SSL 证书..."
info_msg "这可能需要几分钟时间..."

# 使用 Certbot 获取证书并自动配置 Nginx
certbot --nginx \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive \
    --redirect

if [ $? -eq 0 ]; then
    success_msg "SSL 证书获取成功"
else
    error_msg "SSL 证书获取失败"
    echo ""
    echo "常见问题："
    echo "  1. 域名未正确解析到此服务器"
    echo "  2. 防火墙阻止了 80/443 端口"
    echo "  3. 域名已在其他地方使用 Certbot 获取过证书"
    exit 1
fi
echo ""

# 4. 设置自动续期
step_msg "[4/4] 设置自动续期..."

# 启用并启动 Certbot 自动续期定时器
systemctl enable certbot.timer
systemctl start certbot.timer

if systemctl is-active --quiet certbot.timer; then
    success_msg "Certbot 自动续期已启用"
    
    # 显示下次续期时间
    NEXT_RENEWAL=$(systemctl list-timers certbot.timer --no-pager | grep certbot.timer | awk '{print $1, $2, $3, $4, $5}')
    if [ -n "$NEXT_RENEWAL" ]; then
        info_msg "下次自动续期时间: $NEXT_RENEWAL"
    fi
else
    warning_msg "Certbot 自动续期定时器启动失败，请手动检查"
fi

# 测试续期（干跑模式）
info_msg "测试证书续期（干跑模式）..."
certbot renew --dry-run

if [ $? -eq 0 ]; then
    success_msg "证书续期测试通过"
else
    warning_msg "证书续期测试失败，但证书已安装"
fi
echo ""

# 完成
echo "========================================="
echo "✅ HTTPS 配置完成！"
echo "========================================="
echo ""
echo "📊 配置信息："
echo "  - 域名: $DOMAIN"
echo "  - HTTPS: https://$DOMAIN/"
echo "  - 证书提供商: Let's Encrypt"
echo "  - 自动续期: 已启用"
echo ""
echo "🔍 验证命令："
echo "  curl -I https://$DOMAIN/"
echo "  curl -I https://$DOMAIN/api/health"
echo ""
echo "📝 查看证书信息："
echo "  sudo certbot certificates"
echo ""
echo "🔄 手动续期（如需要）："
echo "  sudo certbot renew"
echo ""
echo "📋 证书位置："
echo "  /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
echo "  /etc/letsencrypt/live/$DOMAIN/privkey.pem"
echo ""

success_msg "您的网站现在已启用 HTTPS！"
