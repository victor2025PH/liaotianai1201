#!/bin/bash
# ============================================================
# 轻量级修复 Nginx WebSocket 配置（最小内存占用）
# ============================================================

NGINX_CONFIG="/etc/nginx/sites-available/default"

# 检查 WebSocket 配置
if grep -q "location /api/v1/notifications/ws" "$NGINX_CONFIG"; then
    if grep -A 5 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | grep -q "proxy_set_header Upgrade"; then
        echo "✅ WebSocket 配置已存在且正确"
        exit 0
    fi
fi

# 创建临时文件（使用 sed 而不是完整重写，节省内存）
TMP_FILE=$(mktemp)

# 读取配置并插入 WebSocket 配置
sed '/location \/api\/ {/i\
    # WebSocket 支持 - 通知服务\
    location /api/v1/notifications/ws {\
        proxy_pass http://backend/api/v1/notifications/ws;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection "upgrade";\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_connect_timeout 60s;\
        proxy_send_timeout 86400s;\
        proxy_read_timeout 86400s;\
        proxy_buffering off;\
    }\
' "$NGINX_CONFIG" > "$TMP_FILE"

# 测试配置
if nginx -t -c "$TMP_FILE" 2>&1 | grep -q "successful"; then
    mv "$TMP_FILE" "$NGINX_CONFIG"
    nginx -s reload
    echo "✅ WebSocket 配置已添加并重载"
else
    echo "❌ 配置错误"
    nginx -t -c "$TMP_FILE"
    rm -f "$TMP_FILE"
    exit 1
fi
