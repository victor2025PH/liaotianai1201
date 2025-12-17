#!/bin/bash
# ============================================================
# 配置 Nginx 反向代理
# ============================================================
# 
# 功能：
# 1. 备份原 Nginx 配置
# 2. 配置反向代理（后端 + 前端）
# 3. 测试配置并重载
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
echo "配置 Nginx 反向代理"
echo "========================================="
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then 
    error_msg "请使用 sudo 运行此脚本"
    exit 1
fi

# 检查 Nginx 是否安装
if ! command -v nginx > /dev/null 2>&1; then
    error_msg "Nginx 未安装，请先安装 Nginx"
    exit 1
fi

# 询问域名
echo "请输入您的域名（例如：aikz.usdt2026.cc）："
read -r DOMAIN

if [ -z "$DOMAIN" ]; then
    error_msg "域名不能为空"
    exit 1
fi

info_msg "将配置域名: $DOMAIN"
echo ""

# 1. 备份原配置
step_msg "[1/4] 备份原 Nginx 配置..."
NGINX_CONFIG="/etc/nginx/sites-available/default"
BACKUP_FILE="${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

if [ -f "$NGINX_CONFIG" ]; then
    cp "$NGINX_CONFIG" "$BACKUP_FILE"
    success_msg "配置已备份到: $BACKUP_FILE"
else
    info_msg "原配置文件不存在，将创建新配置"
fi
echo ""

# 2. 生成新的 Nginx 配置
step_msg "[2/4] 生成新的 Nginx 配置..."

cat > "$NGINX_CONFIG" << EOF
# Telegram AI System - Nginx 反向代理配置
# 生成时间: $(date)
# 域名: $DOMAIN

# 后端 upstream
upstream backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# 前端 upstream
upstream frontend {
    server 127.0.0.1:3000;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # 日志配置
    access_log /var/log/nginx/telegram-ai-access.log;
    error_log /var/log/nginx/telegram-ai-error.log;

    # 客户端最大请求体大小
    client_max_body_size 100M;

    # 后端 API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        
        # 请求头
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲设置
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # 前端应用
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        
        # 请求头
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket 支持
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲设置
        proxy_buffering off;
    }

    # 静态文件缓存（优化性能）
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://frontend;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # 健康检查端点（可选）
    location /nginx-health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

success_msg "Nginx 配置已生成"
echo ""

# 3. 测试配置
step_msg "[3/4] 测试 Nginx 配置..."

if nginx -t; then
    success_msg "Nginx 配置语法正确"
else
    error_msg "Nginx 配置有错误，请检查"
    echo "恢复备份配置..."
    if [ -f "$BACKUP_FILE" ]; then
        cp "$BACKUP_FILE" "$NGINX_CONFIG"
        info_msg "已恢复备份配置"
    fi
    exit 1
fi
echo ""

# 4. 重载 Nginx
step_msg "[4/4] 重载 Nginx..."

systemctl reload nginx

if systemctl is-active --quiet nginx; then
    success_msg "Nginx 已重载并运行"
else
    error_msg "Nginx 重载失败"
    systemctl status nginx --no-pager | head -10
    exit 1
fi
echo ""

# 完成
echo "========================================="
echo "✅ Nginx 反向代理配置完成！"
echo "========================================="
echo ""
echo "📊 配置信息："
echo "  - 域名: $DOMAIN"
echo "  - 后端 API: http://$DOMAIN/api/"
echo "  - 前端应用: http://$DOMAIN/"
echo ""
echo "🔍 验证命令："
echo "  curl -I http://$DOMAIN/"
echo "  curl -I http://$DOMAIN/api/health"
echo ""
echo "📝 查看日志："
echo "  sudo tail -f /var/log/nginx/telegram-ai-access.log"
echo "  sudo tail -f /var/log/nginx/telegram-ai-error.log"
echo ""
info_msg "下一步：配置 HTTPS（使用 Certbot）"
