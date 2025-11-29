#!/bin/bash
# 修复 WebSocket 连接 - 简化版本（在服务器上直接执行）

NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

echo "修复 WebSocket 连接..."

# 备份
sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.bak.$(date +%Y%m%d_%H%M%S)"

# 使用 Python 脚本修复（更可靠）
python3 << 'PYEOF'
import re

config_path = "/etc/nginx/sites-available/aikz.usdt2026.cc"

with open(config_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查找 location /api/ 的位置
api_idx = None
for i, line in enumerate(lines):
    if 'location /api/' in line:
        api_idx = i
        break

if api_idx is None:
    print("错误: 未找到 location /api/")
    exit(1)

# 检查是否已有 WebSocket location
has_ws = any('location /api/v1/notifications/ws' in line for line in lines[:api_idx])

if not has_ws:
    ws_block = [
        '    # WebSocket 支持 - 通知服务（必须在 /api/ 之前）\n',
        '    location /api/v1/notifications/ws {\n',
        '        proxy_pass http://127.0.0.1:8000;\n',
        '        proxy_http_version 1.1;\n',
        '        proxy_set_header Upgrade $http_upgrade;\n',
        '        proxy_set_header Connection "upgrade";\n',
        '        proxy_set_header Host $host;\n',
        '        proxy_set_header X-Real-IP $remote_addr;\n',
        '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n',
        '        proxy_set_header X-Forwarded-Proto $scheme;\n',
        '        proxy_read_timeout 86400;\n',
        '        proxy_send_timeout 86400;\n',
        '        proxy_buffering off;\n',
        '    }\n',
        '\n'
    ]
    lines[api_idx:api_idx] = ws_block
    print("已添加 WebSocket location 配置")
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("配置已更新")
else:
    print("WebSocket location 已存在")
    # 检查配置是否正确
    ws_start = None
    for i, line in enumerate(lines):
        if 'location /api/v1/notifications/ws' in line:
            ws_start = i
            break
    
    if ws_start:
        ws_block = ''.join(lines[ws_start:ws_start+15])
        if 'Upgrade' not in ws_block or 'upgrade' not in ws_block:
            print("WebSocket 配置不完整，需要修复")
            # 这里可以添加修复逻辑，但先简单提示
        else:
            print("WebSocket 配置已正确")
PYEOF

# 测试配置
if sudo nginx -t; then
    echo "Nginx 配置测试通过"
    sudo systemctl reload nginx
    echo "Nginx 已重新加载"
    echo ""
    echo "验证配置："
    sudo grep -A 12 "location /api/v1/notifications/ws" "$NGINX_CONFIG"
    echo ""
    echo "修复完成！"
else
    echo "Nginx 配置测试失败"
    sudo nginx -t
    exit 1
fi

