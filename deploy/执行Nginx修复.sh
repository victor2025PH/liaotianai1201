#!/bin/bash
# Nginx 配置修复脚本

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
    content = f.read()

# 查找并替换 server 块
pattern = r'server\s*\{[^}]*server_name\s+aikz\.usdt2026\.cc.*?\n\}'
new_server = """server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级最高）
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

    # 后端 API（必须在 / 之前，优先级高于前端）
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }

    # 前端（最后，最低优先级）
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
}"""

# 使用更精确的匹配
lines = content.split('\n')
new_lines = []
in_server = False
server_brace_count = 0
server_start = -1

for i, line in enumerate(lines):
    if 'server_name aikz.usdt2026.cc' in line:
        # 向前查找 server {
        for j in range(max(0, i-10), i+1):
            if 'server {' in lines[j] or 'server{' in lines[j]:
                server_start = j
                in_server = True
                server_brace_count = 0
                break
        if server_start >= 0:
            # 添加新配置
            new_lines.append(new_server)
            # 跳过旧的 server 块
            continue
    
    if in_server:
        server_brace_count += line.count('{') - line.count('}')
        if server_brace_count == 0 and '{' in line or '}' in line:
            in_server = False
            continue
        if in_server:
            continue
    
    new_lines.append(line)

with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

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
    echo "[错误] 配置测试失败，请检查错误信息"
fi

echo ""
echo "============================================================"
echo "完成"
echo "============================================================"

