#!/bin/bash
# 强制重写 Nginx 配置，修复 502 错误
# 直接重写配置文件，确保指向正确的端口

set -e

echo "=========================================="
echo "🔧 强制重写 Nginx 配置"
echo "=========================================="
echo ""

# 备份配置
BACKUP_DIR="/tmp/nginx_force_backup_$(date +%Y%m%d_%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"
sudo cp -r /etc/nginx/sites-available/* "$BACKUP_DIR/" 2>/dev/null || true
sudo cp -r /etc/nginx/sites-enabled/* "$BACKUP_DIR/enabled/" 2>/dev/null || true
echo "✅ 配置已备份到: $BACKUP_DIR"
echo ""

# 第一步：修复 aiadmin.usdt2026.cc（所有请求指向 8000）
echo "第一步：修复 aiadmin.usdt2026.cc"
echo "----------------------------------------"

AIADMIN_CONFIG="/etc/nginx/sites-available/aiadmin.usdt2026.cc"

# 检查 SSL 证书
if [ -f "/etc/letsencrypt/live/aiadmin.usdt2026.cc/fullchain.pem" ]; then
    SSL_CERT="/etc/letsencrypt/live/aiadmin.usdt2026.cc/fullchain.pem"
    SSL_KEY="/etc/letsencrypt/live/aiadmin.usdt2026.cc/privkey.pem"
else
    # 尝试通配符证书
    SSL_CERT="/etc/letsencrypt/live/usdt2026.cc/fullchain.pem"
    SSL_KEY="/etc/letsencrypt/live/usdt2026.cc/privkey.pem"
fi

echo "重写 aiadmin.usdt2026.cc 配置..."
sudo tee "$AIADMIN_CONFIG" > /dev/null << EOF
server {
    listen 443 ssl http2;
    server_name aiadmin.usdt2026.cc;
    
    ssl_certificate ${SSL_CERT};
    ssl_certificate_key ${SSL_KEY};
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    client_max_body_size 50M;
    
    # 所有请求都代理到后端 8000
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # WebSocket 支持
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

server {
    listen 80;
    server_name aiadmin.usdt2026.cc;
    return 301 https://\$host\$request_uri;
}
EOF

sudo ln -sf "$AIADMIN_CONFIG" /etc/nginx/sites-enabled/aiadmin.usdt2026.cc
echo "✅ aiadmin.usdt2026.cc 配置已重写"
echo ""

# 第二步：修复 aikz.usdt2026.cc（API 指向 8000，前端指向 3000）
echo "第二步：修复 aikz.usdt2026.cc"
echo "----------------------------------------"

AIKZ_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

# 检查 SSL 证书
if [ -f "/etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem" ]; then
    SSL_CERT_AIKZ="/etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem"
    SSL_KEY_AIKZ="/etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem"
else
    SSL_CERT_AIKZ="/etc/letsencrypt/live/usdt2026.cc/fullchain.pem"
    SSL_KEY_AIKZ="/etc/letsencrypt/live/usdt2026.cc/privkey.pem"
fi

echo "重写 aikz.usdt2026.cc 配置..."
sudo tee "$AIKZ_CONFIG" > /dev/null << EOF
server {
    listen 443 ssl http2;
    server_name aikz.usdt2026.cc;
    
    ssl_certificate ${SSL_CERT_AIKZ};
    ssl_certificate_key ${SSL_KEY_AIKZ};
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    client_max_body_size 50M;
    
    # API 请求 - 代理到后端 8000（必须在 location / 之前）
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
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

sudo ln -sf "$AIKZ_CONFIG" /etc/nginx/sites-enabled/aikz.usdt2026.cc
echo "✅ aikz.usdt2026.cc 配置已重写"
echo ""

# 第三步：清理所有重复配置
echo "第三步：清理重复配置"
echo "----------------------------------------"

# 查找所有可能重复的配置
DUPLICATE_FILES=$(sudo find /etc/nginx/sites-enabled -name "*aiadmin*" -o -name "*aikz*" | grep -v "^${AIADMIN_CONFIG}$" | grep -v "^${AIKZ_CONFIG}$" | grep -v "$(readlink -f /etc/nginx/sites-enabled/aiadmin.usdt2026.cc 2>/dev/null)" | grep -v "$(readlink -f /etc/nginx/sites-enabled/aikz.usdt2026.cc 2>/dev/null)" || true)

if [ -n "$DUPLICATE_FILES" ]; then
    echo "发现重复配置，删除中..."
    for file in $DUPLICATE_FILES; do
        echo "  删除: $file"
        sudo rm -f "$file"
    done
    echo "✅ 重复配置已清理"
else
    echo "✅ 没有重复配置"
fi

echo ""

# 第四步：验证配置文件内容
echo "第四步：验证配置文件"
echo "----------------------------------------"

echo "aiadmin.usdt2026.cc proxy_pass 配置:"
sudo grep -A 2 "proxy_pass" "$AIADMIN_CONFIG" | head -3
echo ""

echo "aikz.usdt2026.cc proxy_pass 配置:"
sudo grep -A 2 "proxy_pass" "$AIKZ_CONFIG"
echo ""

# 第五步：测试 Nginx 配置
echo "第五步：测试 Nginx 配置"
echo "----------------------------------------"

if sudo nginx -t 2>&1; then
    echo "✅ Nginx 配置语法正确"
else
    echo "❌ Nginx 配置语法错误"
    exit 1
fi

echo ""

# 第六步：重启 Nginx
echo "第六步：重启 Nginx"
echo "----------------------------------------"

sudo systemctl restart nginx
sleep 3

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 已重启"
else
    echo "❌ Nginx 重启失败"
    sudo systemctl status nginx | head -20
    exit 1
fi

echo ""

# 第七步：验证后端可访问性
echo "第七步：验证后端可访问性"
echo "----------------------------------------"

if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health)
    echo "✅ 后端可访问 (HTTP $HTTP_CODE)"
else
    echo "❌ 后端无法访问，请检查后端服务"
    echo "   运行: pm2 status"
    echo "   或: pm2 restart backend"
fi

echo ""

# 第八步：验证修复
echo "第八步：验证修复"
echo "----------------------------------------"

sleep 2

echo "测试 aiadmin.usdt2026.cc..."
ADMIN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -k https://aiadmin.usdt2026.cc/health 2>&1 || echo "000")
if [ "$ADMIN_RESPONSE" = "200" ]; then
    echo "✅ aiadmin.usdt2026.cc 可访问 (HTTP $ADMIN_RESPONSE)"
else
    echo "⚠️  aiadmin.usdt2026.cc 返回 (HTTP $ADMIN_RESPONSE)"
fi

echo ""
echo "测试 aikz.usdt2026.cc API..."
AIKZ_API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -k https://aikz.usdt2026.cc/api/health 2>&1 || echo "000")
if [ "$AIKZ_API_RESPONSE" = "200" ]; then
    echo "✅ aikz.usdt2026.cc API 可访问 (HTTP $AIKZ_API_RESPONSE)"
else
    echo "⚠️  aikz.usdt2026.cc API 返回 (HTTP $AIKZ_API_RESPONSE)"
fi

echo ""
echo "=========================================="
echo "✅ 配置重写完成！"
echo "=========================================="
echo ""
echo "如果仍有问题，请检查:"
echo "  1. 后端是否运行: pm2 status"
echo "  2. 端口 8000 是否监听: sudo lsof -i :8000"
echo "  3. Nginx 错误日志: sudo tail -20 /var/log/nginx/error.log"
echo ""

