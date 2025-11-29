#!/bin/bash
# 修复 WebSocket 配置 - 最终版

NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

echo "=========================================="
echo "修复 WebSocket 配置"
echo "=========================================="
echo

# 备份
BACKUP_FILE="${NGINX_CONFIG}.bak.$(date +%Y%m%d_%H%M%S)"
sudo cp "$NGINX_CONFIG" "$BACKUP_FILE"
echo "已备份配置到: $BACKUP_FILE"
echo

# 检查是否已有 WebSocket location
if sudo grep -q "location /api/v1/notifications/ws" "$NGINX_CONFIG"; then
    echo "WebSocket location 已存在，检查并修复配置..."
    
    # 删除所有现有的 WebSocket location 块（可能有重复）
    sudo sed -i '/# WebSocket 支持/,/^[[:space:]]*}$/d' "$NGINX_CONFIG"
    sudo sed -i '/location \/api\/v1\/notifications\/ws/,/^[[:space:]]*}$/d' "$NGINX_CONFIG"
    
    echo "已删除旧的 WebSocket 配置"
fi

# 在 location /api/ 之前插入 WebSocket location
echo "添加新的 WebSocket 配置..."

# 找到 location /api/ 的位置
API_LINE=$(sudo grep -n "location /api/" "$NGINX_CONFIG" | head -1 | cut -d: -f1)

if [ -z "$API_LINE" ]; then
    echo "错误: 未找到 location /api/ 配置"
    exit 1
fi

# 创建临时文件
TEMP_FILE=$(mktemp)

# 读取配置并插入 WebSocket 配置
sudo sed "${API_LINE}i\\
    # WebSocket 支持 - 通知服务（必须在 /api/ 之前）\\
    location /api/v1/notifications/ws {\\
        proxy_pass http://127.0.0.1:8000;\\
        proxy_http_version 1.1;\\
        proxy_set_header Upgrade \$http_upgrade;\\
        proxy_set_header Connection \"upgrade\";\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
        proxy_read_timeout 86400;\\
        proxy_send_timeout 86400;\\
        proxy_buffering off;\\
    }\\
" "$NGINX_CONFIG" > "$TEMP_FILE"

sudo mv "$TEMP_FILE" "$NGINX_CONFIG"

echo "WebSocket 配置已添加"
echo

# 验证配置
echo "验证 Nginx 配置..."
if sudo nginx -t 2>&1 | grep -q "syntax is ok"; then
    echo "✓ Nginx 配置语法正确"
    echo
    echo "重新加载 Nginx..."
    sudo systemctl reload nginx
    echo "✓ Nginx 已重新加载"
    echo
    echo "=========================================="
    echo "修复完成！"
    echo "=========================================="
    echo
    echo "WebSocket 配置："
    sudo grep -A 15 "location /api/v1/notifications/ws" "$NGINX_CONFIG"
else
    echo "✗ Nginx 配置语法错误"
    sudo nginx -t
    echo
    echo "恢复备份..."
    sudo cp "$BACKUP_FILE" "$NGINX_CONFIG"
    exit 1
fi

