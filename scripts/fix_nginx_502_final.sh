#!/bin/bash
# 最终修复 502 错误
# 确保 Nginx 可以正确连接到后端

set -e

echo "=========================================="
echo "🔧 最终修复 Nginx 502 错误"
echo "=========================================="
echo ""

# 第一步：检查后端状态
echo "第一步：检查后端状态"
echo "----------------------------------------"

if pm2 list | grep -q "backend.*online"; then
    echo "✅ 后端进程在线"
else
    echo "❌ 后端进程未运行，启动后端..."
    pm2 restart backend || pm2 start /home/ubuntu/telegram-ai-system/admin-backend/start.sh --name backend
    sleep 3
fi

# 检查端口监听
if sudo lsof -i :8000 >/dev/null 2>&1; then
    echo "✅ 端口 8000 正在监听"
    sudo lsof -i :8000 | head -3
else
    echo "❌ 端口 8000 未监听"
    echo "重启后端..."
    pm2 restart backend
    sleep 5
    
    if sudo lsof -i :8000 >/dev/null 2>&1; then
        echo "✅ 端口 8000 现在正在监听"
    else
        echo "❌ 后端无法启动，请检查日志: pm2 logs backend --lines 50"
        exit 1
    fi
fi

# 测试后端可访问性
if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health)
    echo "✅ 后端可访问 (HTTP $HTTP_CODE)"
else
    echo "❌ 后端无法访问"
    exit 1
fi

echo ""

# 第二步：修复 Nginx 配置（确保使用 127.0.0.1，不是 localhost）
echo "第二步：修复 Nginx 配置"
echo "----------------------------------------"

AIADMIN_CONFIG="/etc/nginx/sites-available/aiadmin.usdt2026.cc"
AIKZ_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

# 修复 aiadmin.usdt2026.cc
if [ -f "$AIADMIN_CONFIG" ]; then
    echo "修复 aiadmin.usdt2026.cc..."
    
    # 确保使用 127.0.0.1 而不是 localhost
    sudo sed -i 's/proxy_pass http:\/\/localhost:8000/proxy_pass http:\/\/127.0.0.1:8000/g' "$AIADMIN_CONFIG"
    sudo sed -i 's/proxy_pass http:\/\/127\.0\.0\.1:300[0-9]/proxy_pass http:\/\/127.0.0.1:8000/g' "$AIADMIN_CONFIG"
    
    # 确保配置正确
    if ! grep -q "proxy_pass http://127.0.0.1:8000" "$AIADMIN_CONFIG"; then
        echo "⚠️  配置中未找到正确的 proxy_pass，重新创建..."
        sudo tee "$AIADMIN_CONFIG" > /dev/null << 'EOF'
server {
    listen 443 ssl http2;
    server_name aiadmin.usdt2026.cc;
    
    ssl_certificate /etc/letsencrypt/live/aiadmin.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aiadmin.usdt2026.cc/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
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
    fi
    echo "✅ aiadmin.usdt2026.cc 配置已修复"
else
    echo "⚠️  配置文件不存在，创建中..."
    sudo tee "$AIADMIN_CONFIG" > /dev/null << 'EOF'
server {
    listen 443 ssl http2;
    server_name aiadmin.usdt2026.cc;
    
    ssl_certificate /etc/letsencrypt/live/aiadmin.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aiadmin.usdt2026.cc/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
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
    sudo ln -sf "$AIADMIN_CONFIG" /etc/nginx/sites-enabled/aiadmin.usdt2026.cc
    echo "✅ aiadmin.usdt2026.cc 配置已创建"
fi

# 修复 aikz.usdt2026.cc
if [ -f "$AIKZ_CONFIG" ]; then
    echo "修复 aikz.usdt2026.cc..."
    
    # 确保 API 使用 127.0.0.1:8000
    sudo sed -i 's/proxy_pass http:\/\/localhost:8000/proxy_pass http:\/\/127.0.0.1:8000/g' "$AIKZ_CONFIG"
    
    # 确保前端使用 127.0.0.1:3000
    sudo sed -i '/location \/ {/,/}/ s/proxy_pass http:\/\/127\.0\.0\.1:[0-9]*/proxy_pass http:\/\/127.0.0.1:3000/' "$AIKZ_CONFIG"
    
    # 检查配置是否正确
    if ! grep -q "location /api/" "$AIKZ_CONFIG" || ! grep -A 1 "location /api/" "$AIKZ_CONFIG" | grep -q "proxy_pass http://127.0.0.1:8000"; then
        echo "⚠️  API 配置不正确，重新创建..."
        
        # 检查 SSL 证书
        if [ -f "/etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem" ]; then
            SSL_CERT="/etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem"
            SSL_KEY="/etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem"
        else
            SSL_CERT="/etc/letsencrypt/live/usdt2026.cc/fullchain.pem"
            SSL_KEY="/etc/letsencrypt/live/usdt2026.cc/privkey.pem"
        fi
        
        sudo tee "$AIKZ_CONFIG" > /dev/null << EOF
server {
    listen 443 ssl http2;
    server_name aikz.usdt2026.cc;
    
    ssl_certificate ${SSL_CERT};
    ssl_certificate_key ${SSL_KEY};
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    client_max_body_size 50M;
    
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
    fi
    echo "✅ aikz.usdt2026.cc 配置已修复"
fi

# 确保符号链接存在
sudo ln -sf "$AIADMIN_CONFIG" /etc/nginx/sites-enabled/aiadmin.usdt2026.cc
sudo ln -sf "$AIKZ_CONFIG" /etc/nginx/sites-enabled/aikz.usdt2026.cc

echo ""

# 第三步：测试 Nginx 配置
echo "第三步：测试 Nginx 配置"
echo "----------------------------------------"

if sudo nginx -t 2>&1; then
    echo "✅ Nginx 配置语法正确"
else
    echo "❌ Nginx 配置语法错误"
    exit 1
fi

echo ""

# 第四步：重启 Nginx
echo "第四步：重启 Nginx"
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

# 第五步：验证
echo "第五步：验证修复"
echo "----------------------------------------"

sleep 2

echo "测试 aiadmin.usdt2026.cc..."
ADMIN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -k https://aiadmin.usdt2026.cc/health 2>&1 || echo "000")
if [ "$ADMIN_RESPONSE" = "200" ]; then
    echo "✅ aiadmin.usdt2026.cc 可访问 (HTTP $ADMIN_RESPONSE)"
else
    echo "❌ aiadmin.usdt2026.cc 返回 (HTTP $ADMIN_RESPONSE)"
    echo "查看错误日志:"
    sudo tail -5 /var/log/nginx/error.log | grep -E "(aiadmin|502|connect)" || echo "未找到相关错误"
fi

echo ""
echo "测试 aikz.usdt2026.cc API..."
AIKZ_API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -k https://aikz.usdt2026.cc/api/health 2>&1 || echo "000")
if [ "$AIKZ_API_RESPONSE" = "200" ]; then
    echo "✅ aikz.usdt2026.cc API 可访问 (HTTP $AIKZ_API_RESPONSE)"
else
    echo "❌ aikz.usdt2026.cc API 返回 (HTTP $AIKZ_API_RESPONSE)"
    echo "查看错误日志:"
    sudo tail -5 /var/log/nginx/error.log | grep -E "(aikz|502|connect)" || echo "未找到相关错误"
fi

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "如果仍有 502 错误，请运行诊断脚本:"
echo "  ./scripts/diagnose_502_deep.sh"
echo ""
echo "查看完整错误日志:"
echo "  sudo tail -50 /var/log/nginx/error.log"
echo ""

