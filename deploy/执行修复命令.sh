#!/bin/bash
# Nginx WebSocket 配置修复脚本

echo "============================================================"
echo "修复 Nginx WebSocket 配置"
echo "============================================================"
echo ""

# 备份
echo ">>> 备份配置..."
sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.$(date +%Y%m%d_%H%M%S)
echo "[OK] 已备份"
echo ""

# 执行修复
echo ">>> 执行修复..."
sudo python3 << 'PYEOF'
import re

# 读取配置
with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到所有 location 块
location_indices = []
for i, line in enumerate(lines):
    if 'location /api/v1/notifications/ws' in line:
        location_indices.append(i)

print(f'找到 {len(location_indices)} 个 location 块')

# 删除重复的（保留第一个）
if len(location_indices) > 1:
    for idx in reversed(location_indices[1:]):
        # 向前查找注释
        block_start = idx
        for j in range(max(0, idx-3), idx):
            if '# WebSocket' in lines[j] or ('#' in lines[j] and 'WebSocket' in lines[j]):
                block_start = j
                break
        
        # 向后查找结束的 }
        brace_count = 0
        block_end = idx
        found_open = False
        for j in range(idx, len(lines)):
            if '{' in lines[j]:
                brace_count += lines[j].count('{')
                found_open = True
            if '}' in lines[j]:
                brace_count -= lines[j].count('}')
                if found_open and brace_count == 0:
                    block_end = j
                    break
        
        print(f'删除行 {block_start+1} 到 {block_end+1}')
        lines = lines[:block_start] + lines[block_end+1:]

# 修复第一个 location 中的 proxy_pass
first_location_idx = None
for i, line in enumerate(lines):
    if 'location /api/v1/notifications/ws' in line:
        first_location_idx = i
        break

if first_location_idx is not None:
    for i in range(first_location_idx, min(first_location_idx + 20, len(lines))):
        if 'proxy_pass' in lines[i] and 'notifications/ws' in lines[i]:
            # 修复 proxy_pass，确保末尾有斜杠
            if 'http://127.0.0.1:8000/api/v1/notifications/ws;' in lines[i]:
                old_line = lines[i]
                lines[i] = lines[i].replace(
                    'http://127.0.0.1:8000/api/v1/notifications/ws;',
                    'http://127.0.0.1:8000/api/v1/notifications/ws/;'
                )
                print(f'修改行 {i+1}：proxy_pass 添加末尾斜杠')
                print(f'  旧: {old_line.strip()}')
                print(f'  新: {lines[i].strip()}')
            break

# 写入新配置
with open('/etc/nginx/sites-available/aikz.usdt2026.cc', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('修复完成')
PYEOF

echo ""
echo ">>> 验证配置..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo ""
    echo ">>> 应用配置..."
    sudo systemctl reload nginx
    echo "[OK] 配置已应用"
    echo ""
    echo ">>> 最终配置："
    sudo grep -A 15 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc
else
    echo "[错误] 配置测试失败，请检查错误信息"
fi

echo ""
echo "============================================================"
echo "完成"
echo "============================================================"

