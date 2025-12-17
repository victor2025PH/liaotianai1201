#!/bin/bash
# ============================================================
# 全自动配置脚本：验证 + Nginx + HTTPS
# ============================================================
# 
# 无需交互，自动完成所有配置
# 使用方法：
#   DOMAIN=your-domain.com EMAIL=your-email@example.com sudo bash auto-setup-all.sh
# 或者直接运行（会使用默认值或从 Nginx 配置中提取）
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================="
echo "全自动配置：验证 + Nginx + HTTPS"
echo "========================================="
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then 
    error_msg "请使用 sudo 运行此脚本"
    exit 1
fi

# 获取域名（优先使用环境变量，其次从 Nginx 配置提取，最后使用默认值）
if [ -z "$DOMAIN" ]; then
    if [ -f "/etc/nginx/sites-available/default" ]; then
        EXISTING_DOMAIN=$(grep -E "server_name\s+" /etc/nginx/sites-available/default | head -1 | sed 's/.*server_name\s*\([^;]*\);.*/\1/' | awk '{print $1}')
        if [ -n "$EXISTING_DOMAIN" ] && [ "$EXISTING_DOMAIN" != "_" ]; then
            DOMAIN="$EXISTING_DOMAIN"
            info_msg "从现有 Nginx 配置中检测到域名: $DOMAIN"
        fi
    fi
fi

# 如果没有域名，尝试从环境变量或使用默认值
if [ -z "$DOMAIN" ]; then
    # 尝试常见的域名
    DOMAIN="${DOMAIN:-aikz.usdt2026.cc}"
    info_msg "使用域名: $DOMAIN（如果不对，请设置环境变量 DOMAIN）"
fi

# 获取邮箱（优先使用环境变量，否则生成默认值）
if [ -z "$EMAIL" ]; then
    EMAIL="admin@${DOMAIN#*.}"  # 从域名生成邮箱
    info_msg "使用邮箱: $EMAIL（如果不对，请设置环境变量 EMAIL）"
fi

info_msg "配置参数："
info_msg "  域名: $DOMAIN"
info_msg "  邮箱: $EMAIL"
echo ""

# 步骤 1: 验证服务
step_msg "步骤 1/4: 验证服务运行状态"
echo ""

if [ -f "$SCRIPT_DIR/verify-services.sh" ]; then
    bash "$SCRIPT_DIR/verify-services.sh" 2>/dev/null || {
        info_msg "服务验证脚本执行失败，继续执行..."
    }
else
    info_msg "验证脚本不存在，跳过验证步骤"
fi
echo ""

# 步骤 2: 配置 Nginx（如果没有配置过）
step_msg "步骤 2/4: 配置 Nginx 反向代理"
echo ""

NGINX_CONFIG="/etc/nginx/sites-available/default"
NEEDS_NGINX_CONFIG=false

# 检查是否已经配置了反向代理
if [ -f "$NGINX_CONFIG" ]; then
    if grep -q "upstream backend" "$NGINX_CONFIG" && grep -q "upstream frontend" "$NGINX_CONFIG"; then
        info_msg "Nginx 已配置反向代理，跳过配置步骤"
    else
        NEEDS_NGINX_CONFIG=true
    fi
else
    NEEDS_NGINX_CONFIG=true
fi

if [ "$NEEDS_NGINX_CONFIG" = "true" ]; then
    info_msg "配置 Nginx 反向代理..."
    
    # 备份原配置
    if [ -f "$NGINX_CONFIG" ]; then
        cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # 生成 Nginx 配置
    cat > "$NGINX_CONFIG" << EOF
# Telegram AI System - Nginx 反向代理配置
# 生成时间: $(date)
# 域名: $DOMAIN

upstream backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

upstream frontend {
    server 127.0.0.1:3000;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    access_log /var/log/nginx/telegram-ai-access.log;
    error_log /var/log/nginx/telegram-ai-error.log;

    client_max_body_size 100M;

    # WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级更高）
    location /api/v1/notifications/ws {
        proxy_pass http://backend/api/v1/notifications/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 86400s;
        proxy_read_timeout 86400s;
        proxy_buffering off;
    }

    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
        proxy_request_buffering off;
    }

    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }

    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://frontend;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    location /nginx-health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF
    
    # 测试配置
    if nginx -t > /dev/null 2>&1; then
        systemctl reload nginx
        success_msg "Nginx 配置完成并已重载"
    else
        error_msg "Nginx 配置有错误"
        nginx -t
        exit 1
    fi
else
    # 即使已配置，也确保 Nginx 运行
    if ! systemctl is-active --quiet nginx; then
        systemctl start nginx
    fi
    success_msg "Nginx 服务正常运行"
fi
echo ""

# 步骤 3: 等待域名解析（如果刚配置）
step_msg "步骤 3/4: 验证域名解析"
echo ""

SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "")
DOMAIN_IP=$(dig +short "$DOMAIN" @8.8.8.8 2>/dev/null | head -1 || echo "")

if [ -z "$DOMAIN_IP" ]; then
        info_msg "无法解析域名 $DOMAIN，可能是 DNS 还未生效"
    info_msg "继续执行 HTTPS 配置（Certbot 会自动验证）"
else
    info_msg "域名 $DOMAIN 解析到: $DOMAIN_IP"
    if [ -n "$SERVER_IP" ] && [ "$DOMAIN_IP" = "$SERVER_IP" ]; then
        success_msg "域名解析正确"
    else
        info_msg "域名解析的 IP 与服务器 IP 可能不一致（继续执行）"
    fi
fi
echo ""

# 步骤 4: 配置 HTTPS
step_msg "步骤 4/4: 配置 HTTPS"
echo ""

# 检查是否已有证书
CERT_EXISTS=false
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    CERT_EXISTS=true
    info_msg "检测到已有 SSL 证书，跳过证书获取"
fi

if [ "$CERT_EXISTS" = "false" ]; then
    # 安装 Certbot（如果未安装）
    if ! command -v certbot > /dev/null 2>&1; then
        info_msg "安装 Certbot..."
        apt update -qq
        apt install -y certbot python3-certbot-nginx > /dev/null 2>&1
    fi
    
    # 获取证书
    info_msg "正在为 $DOMAIN 获取 SSL 证书（这可能需要 1-2 分钟）..."
    
    certbot --nginx \
        -d "$DOMAIN" \
        --email "$EMAIL" \
        --agree-tos \
        --non-interactive \
        --redirect \
        --quiet 2>&1 | grep -v "Saving debug log" || {
        error_msg "SSL 证书获取失败"
        echo ""
        echo "可能的原因："
        echo "  1. 域名未正确解析到此服务器"
        echo "  2. 防火墙阻止了 80/443 端口"
        echo "  3. 域名已在其他地方使用 Certbot"
        echo ""
        info_msg "跳过 HTTPS 配置，您可以稍后手动运行："
        info_msg "  sudo certbot --nginx -d $DOMAIN"
        CERT_FAILED=true
    }
    
    if [ "$CERT_FAILED" != "true" ]; then
        success_msg "SSL 证书获取成功"
    fi
else
    success_msg "SSL 证书已存在"
fi

# 设置自动续期
if command -v certbot > /dev/null 2>&1; then
    systemctl enable certbot.timer > /dev/null 2>&1
    systemctl start certbot.timer > /dev/null 2>&1
    
    if systemctl is-active --quiet certbot.timer; then
        success_msg "Certbot 自动续期已启用"
    fi
fi
echo ""

# 完成总结
echo "========================================="
echo "✅ 全自动配置完成！"
echo "========================================="
echo ""
echo "📊 配置摘要："
echo "  - 域名: $DOMAIN"
if [ "$CERT_FAILED" != "true" ]; then
    echo "  - HTTP: http://$DOMAIN/"
    echo "  - HTTPS: https://$DOMAIN/"
else
    echo "  - HTTP: http://$DOMAIN/"
    echo "  - HTTPS: 未配置（需要手动配置）"
fi
echo "  - 后端 API: http://$DOMAIN/api/"
echo ""
echo "🔍 验证命令："
if [ "$CERT_FAILED" != "true" ]; then
    echo "  curl -I https://$DOMAIN/"
    echo "  curl -I https://$DOMAIN/api/health"
else
    echo "  curl -I http://$DOMAIN/"
    echo "  curl -I http://$DOMAIN/api/health"
fi
echo ""
echo "📝 查看日志："
echo "  sudo tail -f /var/log/nginx/telegram-ai-access.log"
echo "  sudo tail -f /var/log/nginx/telegram-ai-error.log"
echo ""
success_msg "配置完成！"
