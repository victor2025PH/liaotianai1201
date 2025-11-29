#!/bin/bash
# 查看并修复重复的 WebSocket location 配置

echo "============================================================"
echo "查看当前 WebSocket location 配置"
echo "============================================================"

# 1. 查看所有 location 块的行号
echo ""
echo ">>> 所有 location 块的行号："
sudo grep -n 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc

# 2. 查看配置内容
echo ""
echo ">>> 配置内容："
sudo grep -B 2 -A 20 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc

# 3. 备份
echo ""
echo ">>> 备份配置..."
sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.$(date +%Y%m%d_%H%M%S)

# 4. 使用 Python 修复
echo ""
echo ">>> 修复配置..."
sudo python3 << 'PYEOF'
import re

with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到所有包含 location 的行
location_lines = []
for i, line in enumerate(lines):
    if 'location /api/v1/notifications/ws' in line:
        location_lines.append(i)

print(f'找到 {len(location_lines)} 个 location 定义')

if len(location_lines) > 1:
    # 找到第二个 location 块的完整范围
    start_idx = location_lines[1]
    
    # 向前查找注释（最多向前 2 行）
    block_start = start_idx
    if start_idx > 0 and '# WebSocket' in lines[start_idx - 1]:
        block_start = start_idx - 1
    
    # 向后查找结束的 }
    brace_count = 0
    block_end = start_idx
    found_brace = False
    
    for i in range(start_idx, len(lines)):
        line = lines[i]
        if '{' in line:
            brace_count += line.count('{')
            found_brace = True
        if '}' in line:
            brace_count -= line.count('}')
            if found_brace and brace_count == 0:
                block_end = i
                break
    
    print(f'删除行 {block_start+1} 到 {block_end+1}')
    
    # 删除这些行
    new_lines = lines[:block_start] + lines[block_end+1:]
    
    with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print('已删除重复的 location 块')
else:
    print('未发现重复配置')
PYEOF

# 5. 验证
echo ""
echo ">>> 验证修复结果..."
count=$(sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc)
echo "WebSocket location 数量: $count"

if [ "$count" == "1" ]; then
    echo "[OK] 重复配置已删除"
    
    # 6. 测试配置
    echo ""
    echo ">>> 测试 Nginx 配置..."
    sudo nginx -t
    
    if [ $? -eq 0 ]; then
        echo ""
        echo ">>> 重载 Nginx..."
        sudo systemctl reload nginx
        echo "[OK] Nginx 已重载"
        
        echo ""
        echo ">>> 最终配置："
        sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc
    fi
else
    echo "[错误] 仍有 $count 个 location，需要手动修复"
fi

echo ""
echo "============================================================"
echo "完成"
echo "============================================================"

