#!/bin/bash
# ============================================================
# 完全修复 HTTP 和 HTTPS 访问问题
# ============================================================

set -e

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
CONFIG_TEMPLATE="$PROJECT_DIR/deploy/nginx/aikz-https.conf"

echo "=========================================="
echo "🔧 完全修复 HTTP 和 HTTPS 访问问题"
echo "=========================================="
echo ""

# 检查是否以 root 或 sudo 运行
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "❌ 此脚本需要 sudo 权限"
    echo "请使用: sudo bash $0"
    exit 1
fi

# 1. 检查后端服务
echo "[1/7] 检查后端服务..."
echo "----------------------------------------"
if sudo -u ubuntu pm2 list 2>/dev/null | grep -q "backend.*online"; then
    echo "✅ 后端服务正在运行"
    BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health || echo "000")
    if [ "$BACKEND_STATUS" = "200" ]; then
        echo "✅ 后端健康检查通过"
    else
        echo "⚠️  后端健康检查失败 (状态码: $BACKEND_STATUS)"
        echo "   重启后端服务..."
        sudo -u ubuntu pm2 restart backend
        sleep 3
    fi
else
    echo "❌ 后端服务未运行，启动..."
    cd "$PROJECT_DIR"
    sudo -u ubuntu pm2 start ecosystem.config.js --only backend 2>/dev/null || sudo -u ubuntu pm2 restart backend 2>/dev/null || {
        echo "   尝试删除旧进程后重新启动..."
        sudo -u ubuntu pm2 delete backend 2>/dev/null || true
        sudo -u ubuntu pm2 start ecosystem.config.js --only backend
    }
    sleep 3
fi
echo ""

# 2. 检查前端服务
echo "[2/7] 检查前端服务..."
echo "----------------------------------------"
if sudo -u ubuntu pm2 list 2>/dev/null | grep -q "next-server.*online"; then
    echo "✅ 前端服务正在运行"
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000 || echo "000")
    if [ "$FRONTEND_STATUS" = "200" ] || [ "$FRONTEND_STATUS" = "301" ] || [ "$FRONTEND_STATUS" = "302" ]; then
        echo "✅ 前端服务响应正常"
    else
        echo "⚠️  前端服务响应异常 (状态码: $FRONTEND_STATUS)"
        echo "   重启前端服务..."
        sudo -u ubuntu pm2 restart next-server
        sleep 3
    fi
else
    echo "❌ 前端服务未运行，启动..."
    cd "$PROJECT_DIR"
    sudo -u ubuntu pm2 start ecosystem.config.js --only next-server 2>/dev/null || sudo -u ubuntu pm2 restart next-server 2>/dev/null || {
        echo "   尝试删除旧进程后重新启动..."
        sudo -u ubuntu pm2 delete next-server 2>/dev/null || true
        sudo -u ubuntu pm2 start ecosystem.config.js --only next-server
    }
    sleep 3
fi
echo ""

# 3. 检查 SSL 证书
echo "[3/7] 检查 SSL 证书..."
echo "----------------------------------------"
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"
if [ -d "$CERT_DIR" ] && [ -f "$CERT_DIR/fullchain.pem" ] && [ -f "$CERT_DIR/privkey.pem" ]; then
    echo "✅ SSL 证书存在"
    CERT_PATH="$CERT_DIR/fullchain.pem"
    KEY_PATH="$CERT_DIR/privkey.pem"
else
    echo "❌ SSL 证书不存在"
    echo "   需要先运行: sudo certbot --nginx -d $DOMAIN"
    exit 1
fi
echo ""

# 4. 备份当前配置
echo "[4/7] 备份当前配置..."
echo "----------------------------------------"
BACKUP_DIR="/etc/nginx/backups"
mkdir -p "$BACKUP_DIR"
if [ -f "$NGINX_CONFIG" ]; then
    BACKUP_FILE="$BACKUP_DIR/aikz.usdt2026.cc.$(date +%Y%m%d_%H%M%S).conf"
    sudo cp "$NGINX_CONFIG" "$BACKUP_FILE"
    echo "✅ 配置已备份到: $BACKUP_FILE"
else
    echo "⚠️  配置文件不存在，将创建新配置"
fi
echo ""

# 5. 使用模板文件创建配置（直接复制，避免语法错误）
echo "[5/7] 创建完整的 Nginx 配置..."
echo "----------------------------------------"
if [ -f "$CONFIG_TEMPLATE" ]; then
    echo "✅ 使用配置模板: $CONFIG_TEMPLATE"
    sudo cp "$CONFIG_TEMPLATE" "$NGINX_CONFIG"
    echo "✅ 配置文件已创建"
else
    echo "❌ 配置模板不存在: $CONFIG_TEMPLATE"
    echo "   将使用默认配置..."
    
    # 创建默认配置
    sudo tee "$NGINX_CONFIG" > /dev/null << 'NGINX_EOF'
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name aikz.usdt2026.cc;
    
    # Let's Encrypt 验证路径
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # 重定向所有 HTTP 请求到 HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name aikz.usdt2026.cc;

    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/aikz.usdt2026.cc/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    client_max_body_size 50M;

    # WebSocket 支持 - 通知服务
    location /api/v1/notifications/ws {
        proxy_pass http://127.0.0.1:8000/api/v1/notifications/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_buffering off;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }

    # Next.js 静态资源
    location /_next/static {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        expires 365d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Next.js 静态资源（兼容路径）
    location /next/static {
        rewrite ^/next/static/(.*)$ /_next/static/$1 break;
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        expires 365d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # public 目录资源
    location /public {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        expires 30d;
        access_log off;
    }

    # 前端应用
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
}
NGINX_EOF
    echo "✅ 默认配置文件已创建"
fi
echo ""

# 6. 确保配置文件链接
echo "[6/7] 确保配置文件链接..."
echo "----------------------------------------"
if [ ! -L "$NGINX_ENABLED" ] && [ ! -f "$NGINX_ENABLED" ]; then
    sudo ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"
    echo "✅ 配置文件链接已创建"
elif [ -L "$NGINX_ENABLED" ]; then
    LINK_TARGET=$(readlink -f "$NGINX_ENABLED")
    if [ "$LINK_TARGET" != "$NGINX_CONFIG" ]; then
        sudo rm -f "$NGINX_ENABLED"
        sudo ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"
        echo "✅ 配置文件链接已更新"
    else
        echo "✅ 配置文件链接正确"
    fi
fi
echo ""

# 7. 测试并重新加载 Nginx
echo "[7/7] 测试并重新加载 Nginx..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
    echo "✅ Nginx 配置测试成功"
    sudo systemctl reload nginx
    sleep 3
    
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已重新加载"
    else
        echo "⚠️  重新加载失败，尝试重启..."
        sudo systemctl restart nginx
        sleep 3
        if systemctl is-active --quiet nginx; then
            echo "✅ Nginx 已重启"
        else
            echo "❌ Nginx 启动失败"
            sudo systemctl status nginx --no-pager | head -20
            exit 1
        fi
    fi
else
    echo "❌ Nginx 配置测试失败"
    echo "查看详细错误："
    sudo nginx -t 2>&1 | tail -20
    exit 1
fi
echo ""

# 8. 最终验证
echo "最终验证..."
echo "----------------------------------------"
sleep 3

# 检查端口
echo "检查端口监听状态："
if sudo ss -tlnp | grep -q ":443 "; then
    echo "✅ 端口 443 正在监听"
    sudo ss -tlnp | grep ":443 "
else
    echo "❌ 端口 443 仍未监听"
    echo "   查看 Nginx 错误日志："
    sudo tail -30 /var/log/nginx/error.log | grep -i "443\|ssl\|certificate" || sudo tail -30 /var/log/nginx/error.log
fi

if sudo ss -tlnp | grep -q ":80 "; then
    echo "✅ 端口 80 正在监听"
else
    echo "⚠️  端口 80 未监听"
fi
echo ""

# 测试连接
echo "测试连接..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ || echo "000")
HTTPS_CODE=$(curl -s -k -o /dev/null -w "%{http_code}" https://127.0.0.1/ || echo "000")

if [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✅ HTTP 本地连接正常 (重定向到 HTTPS)"
elif [ "$HTTP_CODE" = "200" ]; then
    echo "⚠️  HTTP 本地连接正常，但未重定向到 HTTPS"
else
    echo "❌ HTTP 本地连接失败 (状态码: $HTTP_CODE)"
fi

if [ "$HTTPS_CODE" = "200" ] || [ "$HTTPS_CODE" = "301" ] || [ "$HTTPS_CODE" = "302" ]; then
    echo "✅ HTTPS 本地连接正常"
else
    echo "❌ HTTPS 本地连接失败 (状态码: $HTTPS_CODE)"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "验证命令："
echo "  sudo ss -tlnp | grep ':443'"
echo "  curl -I https://aikz.usdt2026.cc"
echo "  curl -I http://aikz.usdt2026.cc"
echo ""

