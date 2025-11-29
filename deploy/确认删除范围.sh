#!/bin/bash
# 确认要删除的范围

echo "============================================================"
echo "确认 WebSocket location 配置的删除范围"
echo "============================================================"
echo ""

# 1. 显示所有 location 的行号
echo ">>> 所有 location 块的行号："
sudo grep -n 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc
echo ""

# 2. 显示第一个 location 块（保留）
echo ">>> 第一个 location 块（保留这个）："
first_line=$(sudo grep -n 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc | head -1 | cut -d: -f1)
sudo sed -n "${first_line},+15p" /etc/nginx/sites-available/aikz.usdt2026.cc
echo ""

# 3. 显示第二个 location 块（删除这个）
echo ">>> 第二个 location 块（删除这个）："
second_line=$(sudo grep -n 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc | tail -1 | cut -d: -f1)
# 向前查找注释
start_line=$((second_line - 1))
sudo sed -n "${start_line},+15p" /etc/nginx/sites-available/aikz.usdt2026.cc
echo ""

# 4. 确认删除范围
echo "============================================================"
echo "删除范围确认："
echo "============================================================"
echo "保留：第一个 location 块（行 $first_line 开始）"
echo "删除：第二个 location 块（行 $start_line 开始，包括前面的注释）"
echo ""
echo "要删除的行号范围：$start_line 到大约 $((start_line + 14))"
echo ""
read -p "确认删除？(y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ">>> 备份配置..."
    sudo cp /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-available/aikz.usdt2026.cc.bak.confirm
    
    # 找到第二个 location 块的结束行
    brace_count=0
    end_line=$second_line
    found_brace=false
    
    while IFS= read -r line; do
        if [[ $line == *"{"* ]]; then
            brace_count=$((brace_count + 1))
            found_brace=true
        fi
        if [[ $line == *"}"* ]]; then
            brace_count=$((brace_count - 1))
            if [ "$found_brace" = true ] && [ $brace_count -eq 0 ]; then
                break
            fi
        fi
        end_line=$((end_line + 1))
    done < <(sudo sed -n "${second_line},$"p /etc/nginx/sites-available/aikz.usdt2026.cc)
    
    echo "删除行 $start_line 到 $end_line"
    sudo sed -i "${start_line},${end_line}d" /etc/nginx/sites-available/aikz.usdt2026.cc
    
    echo ""
    echo ">>> 验证删除结果..."
    count=$(sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc)
    echo "剩余 location 数量: $count"
    
    if [ "$count" == "1" ]; then
        echo "[OK] 重复配置已删除"
        echo ""
        echo ">>> 测试配置..."
        sudo nginx -t
        
        if [ $? -eq 0 ]; then
            echo ""
            echo ">>> 重载 Nginx..."
            sudo systemctl reload nginx
            echo "[OK] 修复完成！"
        fi
    else
        echo "[错误] 仍有 $count 个 location"
    fi
else
    echo "已取消"
fi

