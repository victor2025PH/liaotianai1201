#!/bin/bash
# 检查当前配置并修复重复的 location

echo "============================================================"
echo "检查当前 WebSocket location 配置"
echo "============================================================"
echo ""

# 1. 查看所有 location 的行号
echo ">>> 1. 所有 location 块的行号："
sudo grep -n 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc
echo ""

# 2. 统计数量
echo ">>> 2. location 块数量："
count=$(sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc)
echo "找到 $count 个 location 块"
echo ""

# 3. 显示所有 location 块
echo ">>> 3. 所有 location 块的内容："
sudo grep -B 2 -A 20 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc
echo ""

if [ "$count" == "2" ]; then
    echo "============================================================"
    echo "发现重复配置，准备修复"
    echo "============================================================"
    echo ""
    
    # 获取第二个 location 的行号
    second_line=$(sudo grep -n 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc | tail -1 | cut -d: -f1)
    
    echo ">>> 第二个 location 块的位置：第 $second_line 行"
    echo ""
    echo ">>> 第二个 location 块的内容（要删除的部分）："
    # 向前查找注释
    start_line=$((second_line - 1))
    sudo sed -n "${start_line},+15p" /etc/nginx/sites-available/aikz.usdt2026.cc
    echo ""
    
    echo "============================================================"
    echo "修复方案"
    echo "============================================================"
    echo "备份配置..."
    sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.check
    
    echo ""
    echo "使用 Python 脚本精确删除第二个 location 块..."
    sudo python3 << 'PYEOF'
import re

with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到所有 location 行
location_indices = []
for i, line in enumerate(lines):
    if 'location /api/v1/notifications/ws' in line:
        location_indices.append(i)

print(f'找到 {len(location_indices)} 个 location 定义')

if len(location_indices) > 1:
    # 第二个 location 的位置
    second_start = location_indices[1]
    
    # 向前查找注释（最多向前 3 行）
    block_start = second_start
    for i in range(max(0, second_start-3), second_start):
        if '# WebSocket' in lines[i] or '# WebSocket' in lines[i].strip():
            block_start = i
            break
    
    # 向后查找结束的 }
    brace_count = 0
    block_end = second_start
    found_open = False
    
    for i in range(second_start, len(lines)):
        line = lines[i]
        if '{' in line:
            brace_count += line.count('{')
            found_open = True
        if '}' in line:
            brace_count -= line.count('}')
            if found_open and brace_count == 0:
                block_end = i
                break
    
    print(f'删除行 {block_start+1} 到 {block_end+1}')
    print(f'删除内容：')
    for i in range(block_start, min(block_end+1, len(lines))):
        print(f'  {i+1}: {lines[i].rstrip()}')
    
    # 删除
    new_lines = lines[:block_start] + lines[block_end+1:]
    
    with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f'\n已删除 {block_end - block_start + 1} 行')
    print('重复的 location 块已删除')
else:
    print('未发现重复配置')
PYEOF

    echo ""
    echo ">>> 验证删除结果..."
    new_count=$(sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc)
    echo "剩余 location 数量: $new_count"
    
    if [ "$new_count" == "1" ]; then
        echo "[OK] 重复配置已删除"
        echo ""
        echo ">>> 测试 Nginx 配置..."
        sudo nginx -t
        
        if [ $? -eq 0 ]; then
            echo ""
            echo ">>> 重载 Nginx..."
            sudo systemctl reload nginx
            echo "[OK] 修复完成！"
            echo ""
            echo ">>> 最终配置："
            sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc
        fi
    else
        echo "[错误] 仍有 $new_count 个 location，需要手动修复"
    fi
else
    echo "[OK] 配置正常，只有 $count 个 location 块"
fi

echo ""
echo "============================================================"
echo "完成"
echo "============================================================"

