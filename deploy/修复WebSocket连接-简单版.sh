#!/bin/bash
# 修复 WebSocket 连接问题 - 简单版本

echo "修复 WebSocket 连接..."

NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

# 备份
sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.bak.$(date +%Y%m%d_%H%M%S)"

# 检查并修复
python3 << 'PYEOF'
import re

config_path = "/etc/nginx/sites-available/aikz.usdt2026.cc"

with open(config_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查找 server 块中 location /api/ 的位置
api_location_idx = None
for i, line in enumerate(lines):
    if 'location /api/' in line and api_location_idx is None:
        api_location_idx = i
        break

if api_location_idx is None:
    print("错误: 未找到 location /api/")
    exit(1)

# 检查是否已有 WebSocket location
has_ws = False
for i in range(max(0, api_location_idx - 20), api_location_idx):
    if 'location /api/v1/notifications/ws' in lines[i]:
        has_ws = True
        break

if not has_ws:
    # 在 location /api/ 之前插入 WebSocket location
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
    lines[api_location_idx:api_location_idx] = ws_block
    print("已添加 WebSocket location 配置")
else:
    print("WebSocket location 配置已存在")

# 写入文件
with open(config_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("配置已更新")
PYEOF

# 测试并重新加载
sudo nginx -t && sudo systemctl reload nginx && echo "修复完成！"

