#!/bin/bash
# 一键修复 Nginx API 404 问题

echo "============================================================"
echo "修复 Nginx 配置 - 解决 API 404 问题"
echo "============================================================"
echo ""

# 备份
echo ">>> [1] 备份配置..."
sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.$(date +%Y%m%d_%H%M%S)
echo "[OK] 已备份"
echo ""

# 执行修复
echo ">>> [2] 执行修复..."
sudo python3 << 'PYEOF'
import re

with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'r', encoding='utf-8') as f:
    lines = f.readlines()

server_start = None
server_end = None

for i, line in enumerate(lines):
    if 'server_name aikz.usdt2026.cc' in line:
        for j in range(max(0, i-10), i+1):
            if 'server {' in lines[j] or 'server{' in lines[j]:
                server_start = j
                break
        if server_start is None:
            server_start = i
        
        brace_count = 0
        found_open = False
        for j in range(server_start, len(lines)):
            if '{' in lines[j]:
                brace_count += lines[j].count('{')
                found_open = True
            if '}' in lines[j]:
                brace_count -= lines[j].count('}')
                if found_open and brace_count == 0:
                    server_end = j
                    break
        break

if server_start is None or server_end is None:
    print('未找到 server 块')
    exit(1)

new_lines = []
new_lines.extend(lines[:server_start])
new_lines.append('server {\n')
new_lines.append('    listen 80;\n')
new_lines.append('    server_name aikz.usdt2026.cc;\n')
new_lines.append('\n')
new_lines.append('    # WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级最高）\n')
new_lines.append('    location /api/v1/notifications/ws {\n')
new_lines.append('        proxy_pass http://127.0.0.1:8000;\n')
new_lines.append('        proxy_http_version 1.1;\n')
new_lines.append('        proxy_set_header Upgrade $http_upgrade;\n')
new_lines.append('        proxy_set_header Connection "upgrade";\n')
new_lines.append('        proxy_set_header Host $host;\n')
new_lines.append('        proxy_set_header X-Real-IP $remote_addr;\n')
new_lines.append('        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n')
new_lines.append('        proxy_set_header X-Forwarded-Proto $scheme;\n')
new_lines.append('        proxy_read_timeout 86400;\n')
new_lines.append('        proxy_send_timeout 86400;\n')
new_lines.append('        proxy_buffering off;\n')
new_lines.append('    }\n')
new_lines.append('\n')
new_lines.append('    # 后端 API（必须在 / 之前，优先级高于前端）\n')
new_lines.append('    location /api/ {\n')
new_lines.append('        proxy_pass http://127.0.0.1:8000;\n')
new_lines.append('        proxy_http_version 1.1;\n')
new_lines.append('        proxy_set_header Host $host;\n')
new_lines.append('        proxy_set_header X-Real-IP $remote_addr;\n')
new_lines.append('        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n')
new_lines.append('        proxy_set_header X-Forwarded-Proto $scheme;\n')
new_lines.append('        proxy_read_timeout 300;\n')
new_lines.append('    }\n')
new_lines.append('\n')
new_lines.append('    # 前端（最后，最低优先级）\n')
new_lines.append('    location / {\n')
new_lines.append('        proxy_pass http://127.0.0.1:3000;\n')
new_lines.append('        proxy_http_version 1.1;\n')
new_lines.append('        proxy_set_header Upgrade $http_upgrade;\n')
new_lines.append('        proxy_set_header Connection "upgrade";\n')
new_lines.append('        proxy_set_header Host $host;\n')
new_lines.append('        proxy_set_header X-Real-IP $remote_addr;\n')
new_lines.append('        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n')
new_lines.append('        proxy_read_timeout 86400;\n')
new_lines.append('    }\n')
new_lines.append('}\n')
new_lines.extend(lines[server_end+1:])

with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('配置已修复')
PYEOF

echo ""
echo ">>> [3] 测试配置..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo ""
    echo ">>> [4] 应用配置..."
    sudo systemctl reload nginx
    echo "[OK] 配置已应用"
    echo ""
    echo ">>> [5] 验证配置..."
    echo "Location 配置："
    sudo grep -A 3 'location /api/' /etc/nginx/sites-available/aikz.usdt2026.cc
else
    echo "[错误] 配置测试失败"
fi

echo ""
echo "============================================================"
echo "完成"
echo "============================================================"

