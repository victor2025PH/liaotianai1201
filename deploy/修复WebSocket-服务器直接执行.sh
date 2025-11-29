#!/bin/bash
# 修复 WebSocket 连接 - 在服务器上直接执行

NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

echo "修复 WebSocket 连接..."

# 备份
sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.bak.$(date +%Y%m%d_%H%M%S)"

# 检查是否已有 WebSocket location
if sudo grep -q "location /api/v1/notifications/ws" "$NGINX_CONFIG"; then
    echo "WebSocket location 已存在，检查配置..."
    
    # 检查配置是否正确
    if sudo grep -A 10 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | grep -q "Upgrade" && \
       sudo grep -A 10 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | grep -q "Connection.*upgrade"; then
        echo "WebSocket 配置已正确"
    else
        echo "WebSocket 配置不完整，需要修复..."
        # 使用 sed 修复（简单情况）
        sudo sed -i '/location \/api\/v1\/notifications\/ws {/,/}/ {
            /proxy_pass/ s|.*|        proxy_pass http://127.0.0.1:8000;|
            /proxy_http_version/ s|.*|        proxy_http_version 1.1;|
            /proxy_set_header Upgrade/ s|.*|        proxy_set_header Upgrade $http_upgrade;|
            /proxy_set_header Connection/ s|.*|        proxy_set_header Connection "upgrade";|
        }' "$NGINX_CONFIG"
        
        # 如果缺少 Upgrade 或 Connection，添加它们
        if ! sudo grep -A 10 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | grep -q "Upgrade"; then
            sudo sed -i '/location \/api\/v1\/notifications\/ws {/,/proxy_http_version/ {
                /proxy_http_version/a\        proxy_set_header Upgrade $http_upgrade;
            }' "$NGINX_CONFIG"
        fi
        
        if ! sudo grep -A 10 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | grep -q "Connection.*upgrade"; then
            sudo sed -i '/proxy_set_header Upgrade/,/proxy_set_header Host/ {
                /proxy_set_header Upgrade/a\        proxy_set_header Connection "upgrade";
            }' "$NGINX_CONFIG"
        fi
    fi
else
    echo "WebSocket location 不存在，添加配置..."
    
    # 在 location /api/ 之前添加 WebSocket location
    sudo sed -i '/location \/api\/ {/i\
    # WebSocket 支持 - 通知服务（必须在 /api/ 之前）\
    location /api/v1/notifications/ws {\
        proxy_pass http://127.0.0.1:8000;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection "upgrade";\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_read_timeout 86400;\
        proxy_send_timeout 86400;\
        proxy_buffering off;\
    }\
' "$NGINX_CONFIG"
fi

# 测试配置
if sudo nginx -t; then
    echo "Nginx 配置测试通过"
    sudo systemctl reload nginx
    echo "Nginx 已重新加载"
    echo ""
    echo "修复完成！请刷新浏览器页面验证。"
else
    echo "Nginx 配置测试失败"
    sudo nginx -t
    exit 1
fi

