#!/bin/bash
# 修复 Nginx 502 错误
# 1. 修复 aiadmin.usdt2026.cc（确保指向 8000）
# 2. 修复 aikz.usdt2026.cc（API 指向 8000，前端指向 3000）
# 3. 解决重复配置问题
# 4. 重启 Nginx

set -e

echo "=========================================="
echo "🔧 修复 Nginx 502 错误"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"

# 备份配置
BACKUP_DIR="/tmp/nginx_backup_$(date +%Y%m%d_%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"
sudo cp -r "$NGINX_AVAILABLE"/* "$BACKUP_DIR/" 2>/dev/null || true
sudo cp -r "$NGINX_ENABLED"/* "$BACKUP_DIR/enabled/" 2>/dev/null || true
echo "✅ 配置已备份到: $BACKUP_DIR"
echo ""

# 第一步：修复 aiadmin.usdt2026.cc（应该指向 8000）
echo "第一步：修复 aiadmin.usdt2026.cc"
echo "----------------------------------------"

ADMIN_CONFIG="$NGINX_AVAILABLE/aiadmin.usdt2026.cc"

if [ ! -f "$ADMIN_CONFIG" ]; then
    echo "创建 aiadmin.usdt2026.cc 配置..."
    sudo tee "$ADMIN_CONFIG" > /dev/null << 'EOF'
server {
    listen 443 ssl http2;
    server_name aiadmin.usdt2026.cc;
    
    # SSL 证书
    ssl_certificate /etc/letsencrypt/live/aiadmin.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aiadmin.usdt2026.cc/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    client_max_body_size 50M;
    
    # 所有请求都代理到后端
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

server {
    listen 80;
    server_name aiadmin.usdt2026.cc;
    return 301 https://$host$request_uri;
}
EOF
    echo "✅ 配置已创建"
else
    echo "✅ 配置文件已存在"
fi

# 确保符号链接存在
sudo ln -sf "$ADMIN_CONFIG" "$NGINX_ENABLED/aiadmin.usdt2026.cc"
echo "✅ 符号链接已创建"
echo ""

# 第二步：修复 aikz.usdt2026.cc（API 指向 8000，前端指向 3000）
echo "第二步：修复 aikz.usdt2026.cc"
echo "----------------------------------------"

AIKZ_CONFIG="$NGINX_AVAILABLE/aikz.usdt2026.cc"

# 检查 SSL 证书
if [ -f "/etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem" ]; then
    SSL_CERT="/etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem"
    SSL_KEY="/etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem"
else
    # 尝试其他可能的证书路径
    SSL_CERT="/etc/letsencrypt/live/usdt2026.cc/fullchain.pem"
    SSL_KEY="/etc/letsencrypt/live/usdt2026.cc/privkey.pem"
fi

echo "创建 aikz.usdt2026.cc 配置..."
sudo tee "$AIKZ_CONFIG" > /dev/null << EOF
server {
    listen 443 ssl http2;
    server_name aikz.usdt2026.cc;
    
    # SSL 证书
    ssl_certificate ${SSL_CERT};
    ssl_certificate_key ${SSL_KEY};
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    client_max_body_size 50M;
    
    # API 请求 - 优先匹配，代理到后端 8000
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # WebSocket 支持
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 前端应用 - 代理到前端 3000
    location / {
        proxy_pass http://127.0.0.1:3000;
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
    }
}

server {
    listen 80;
    server_name aikz.usdt2026.cc;
    return 301 https://\$host\$request_uri;
}
EOF
echo "✅ 配置已创建"

# 确保符号链接存在
sudo ln -sf "$AIKZ_CONFIG" "$NGINX_ENABLED/aikz.usdt2026.cc"
echo "✅ 符号链接已创建"
echo ""

# 第三步：清理重复配置
echo "第三步：清理重复配置"
echo "----------------------------------------"

# 查找所有包含 aikz.usdt2026.cc 的配置文件
DUPLICATE_FILES=$(sudo grep -r "server_name.*aikz.usdt2026.cc" "$NGINX_ENABLED" 2>/dev/null | cut -d: -f1 | sort -u | grep -v "^$AIKZ_CONFIG$" || true)

if [ -n "$DUPLICATE_FILES" ]; then
    echo "⚠️  发现重复配置，删除中..."
    for file in $DUPLICATE_FILES; do
        if [ -L "$file" ]; then
            echo "  删除符号链接: $file"
            sudo rm -f "$file"
        elif [ -f "$file" ]; then
            echo "  删除文件: $file"
            sudo rm -f "$file"
        fi
    done
    echo "✅ 重复配置已清理"
else
    echo "✅ 没有重复配置"
fi
echo ""

# 第四步：测试 Nginx 配置
echo "第四步：测试 Nginx 配置"
echo "----------------------------------------"

if sudo nginx -t 2>&1; then
    echo "✅ Nginx 配置语法正确"
else
    echo "❌ Nginx 配置语法错误"
    exit 1
fi
echo ""

# 第五步：重启 Nginx
echo "第五步：重启 Nginx"
echo "----------------------------------------"

if sudo systemctl restart nginx; then
    echo "✅ Nginx 已重启"
else
    echo "❌ Nginx 重启失败"
    exit 1
fi

sleep 2

# 检查 Nginx 状态
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务正在运行"
else
    echo "❌ Nginx 服务未运行"
    exit 1
fi
echo ""

# 第六步：验证
echo "第六步：验证配置"
echo "----------------------------------------"

echo "检查后端端口 8000..."
if sudo lsof -i :8000 >/dev/null 2>&1; then
    echo "✅ 后端端口 8000 正在监听"
else
    echo "❌ 后端端口 8000 未监听"
    echo "   请确保后端已启动: pm2 restart backend"
fi

echo ""
echo "测试 aiadmin.usdt2026.cc..."
ADMIN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -k https://aiadmin.usdt2026.cc/health 2>&1 || echo "000")
if [ "$ADMIN_RESPONSE" = "200" ]; then
    echo "✅ aiadmin.usdt2026.cc 可访问 (HTTP $ADMIN_RESPONSE)"
else
    echo "⚠️  aiadmin.usdt2026.cc 响应 (HTTP $ADMIN_RESPONSE)"
fi

echo ""
echo "测试 aikz.usdt2026.cc API..."
AIKZ_API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -k https://aikz.usdt2026.cc/api/health 2>&1 || echo "000")
if [ "$AIKZ_API_RESPONSE" = "200" ]; then
    echo "✅ aikz.usdt2026.cc API 可访问 (HTTP $AIKZ_API_RESPONSE)"
else
    echo "⚠️  aikz.usdt2026.cc API 响应 (HTTP $AIKZ_API_RESPONSE)"
fi

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "如果仍有 502 错误，请检查:"
echo "  1. 后端是否运行: pm2 status"
echo "  2. 端口 8000 是否监听: sudo lsof -i :8000"
echo "  3. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo ""

