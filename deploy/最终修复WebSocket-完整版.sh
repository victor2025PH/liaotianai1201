#!/bin/bash
# 最终修复 WebSocket 配置 - 完整版

set -e

NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

echo "=========================================="
echo "最终修复 WebSocket 配置"
echo "=========================================="
echo

# 备份
BACKUP_FILE="${NGINX_CONFIG}.bak.$(date +%Y%m%d_%H%M%S)"
sudo cp "$NGINX_CONFIG" "$BACKUP_FILE"
echo "✓ 已备份配置到: $BACKUP_FILE"
echo

# 1. 删除所有现有的 WebSocket location 块
echo "[步骤 1] 清理旧的 WebSocket 配置..."
sudo sed -i '/# WebSocket 支持/,/^[[:space:]]*}$/d' "$NGINX_CONFIG"
sudo sed -i '/location \/api\/v1\/notifications\/ws/,/^[[:space:]]*}$/d' "$NGINX_CONFIG"
echo "✓ 已删除旧的 WebSocket 配置"
echo

# 2. 找到 location /api/ 的位置
echo "[步骤 2] 查找 location /api/ 位置..."
API_LINE=$(sudo grep -n "^[[:space:]]*location /api/" "$NGINX_CONFIG" | head -1 | cut -d: -f1)

if [ -z "$API_LINE" ]; then
    echo "✗ 错误: 未找到 location /api/ 配置"
    exit 1
fi

echo "✓ 找到 location /api/ 在第 $API_LINE 行"
echo

# 3. 插入 WebSocket 配置
echo "[步骤 3] 插入 WebSocket 配置..."

# 创建临时文件
TEMP_FILE=$(mktemp)

# 读取前 N-1 行
head -n $((API_LINE - 1)) "$NGINX_CONFIG" > "$TEMP_FILE"

# 添加 WebSocket 配置
cat >> "$TEMP_FILE" << 'EOF'
    # WebSocket 支持 - 通知服务（必须在 /api/ 之前）
    location /api/v1/notifications/ws {
        proxy_pass http://127.0.0.1:8000;
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

EOF

# 添加剩余的行
tail -n +$API_LINE "$NGINX_CONFIG" >> "$TEMP_FILE"

# 替换原文件
sudo mv "$TEMP_FILE" "$NGINX_CONFIG"
sudo chown root:root "$NGINX_CONFIG"
sudo chmod 644 "$NGINX_CONFIG"

echo "✓ WebSocket 配置已添加"
echo

# 4. 验证配置
echo "[步骤 4] 验证 Nginx 配置..."
if sudo nginx -t 2>&1 | grep -q "syntax is ok"; then
    echo "✓ Nginx 配置语法正确"
    echo
else
    echo "✗ Nginx 配置语法错误"
    sudo nginx -t
    echo
    echo "恢复备份..."
    sudo cp "$BACKUP_FILE" "$NGINX_CONFIG"
    exit 1
fi

# 5. 重新加载 Nginx
echo "[步骤 5] 重新加载 Nginx..."
if sudo systemctl reload nginx; then
    echo "✓ Nginx 已重新加载"
else
    echo "✗ Nginx 重新加载失败"
    exit 1
fi

echo
echo "=========================================="
echo "修复完成！"
echo "=========================================="
echo
echo "WebSocket 配置："
sudo grep -A 15 "location /api/v1/notifications/ws" "$NGINX_CONFIG"
echo
echo "下一步："
echo "1. 刷新浏览器页面（F5）"
echo "2. 检查 Console（F12）中的 WebSocket 错误是否消失"
echo

