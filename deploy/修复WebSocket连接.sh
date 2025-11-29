#!/bin/bash
# 修复 WebSocket 连接问题

echo "============================================================"
echo "修复 WebSocket 连接问题"
echo "============================================================"

NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

# 1. 备份配置
echo ""
echo ">>> [1] 备份 Nginx 配置..."
sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.bak.$(date +%Y%m%d_%H%M%S)"
echo "[OK] 已备份: ${NGINX_CONFIG}.bak.$(date +%Y%m%d_%H%M%S)"

# 2. 检查当前配置
echo ""
echo ">>> [2] 检查当前 WebSocket 配置..."
if sudo grep -q "location /api/v1/notifications/ws" "$NGINX_CONFIG"; then
    echo "[信息] 找到 WebSocket location 配置"
    sudo grep -A 15 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | head -20
else
    echo "[警告] 未找到 WebSocket location 配置，将添加"
fi

# 3. 检查配置是否正确
echo ""
echo ">>> [3] 检查配置是否正确..."
has_upgrade=$(sudo grep -A 10 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | grep -q "Upgrade" && echo "yes" || echo "no")
has_connection=$(sudo grep -A 10 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | grep -q "Connection.*upgrade" && echo "yes" || echo "no")
proxy_pass_correct=$(sudo grep -A 5 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | grep "proxy_pass" | grep -q "http://127.0.0.1:8000;" && echo "yes" || echo "no")

echo "Upgrade header: $has_upgrade"
echo "Connection header: $has_connection"
echo "proxy_pass 正确: $proxy_pass_correct"

# 4. 修复配置（如果需要）
if [ "$has_upgrade" = "no" ] || [ "$has_connection" = "no" ] || [ "$proxy_pass_correct" = "no" ]; then
    echo ""
    echo ">>> [4] 修复 WebSocket 配置..."
    
    # 使用 Python 脚本修复（更可靠）
    python3 << 'PYEOF'
import re
import sys

config_path = "/etc/nginx/sites-available/aikz.usdt2026.cc"

# 读取配置
with open(config_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 检查是否存在 WebSocket location
ws_location_pattern = r'location\s+/api/v1/notifications/ws\s*\{[^}]*\}'
ws_match = re.search(ws_location_pattern, content, re.DOTALL)

if ws_match:
    # 如果存在，检查并修复
    ws_block = ws_match.group(0)
    
    # 检查是否需要修复
    needs_fix = False
    if 'proxy_set_header Upgrade' not in ws_block:
        needs_fix = True
    if 'proxy_set_header Connection "upgrade"' not in ws_block and 'proxy_set_header Connection upgrade' not in ws_block:
        needs_fix = True
    if 'proxy_pass http://127.0.0.1:8000;' not in ws_block and 'proxy_pass http://127.0.0.1:8000' not in ws_block:
        needs_fix = True
    
    if needs_fix:
        # 替换为正确的配置
        correct_block = '''    location /api/v1/notifications/ws {
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
    }'''
        
        content = content.replace(ws_block, correct_block)
        print("[修复] 已更新现有 WebSocket location 配置")
    else:
        print("[OK] WebSocket location 配置已正确")
else:
    # 如果不存在，需要添加
    # 找到 server 块
    server_pattern = r'(server\s+\{[^}]*listen\s+80[^}]*server_name\s+aikz\.usdt2026\.cc[^}]*\{)'
    server_match = re.search(server_pattern, content, re.DOTALL)
    
    if server_match:
        # 在 server 块开始后，在 location /api/ 之前添加
        api_location_pattern = r'(location\s+/api/\s*\{)'
        api_match = re.search(api_location_pattern, content)
        
        if api_match:
            insert_pos = api_match.start()
            ws_block = '''    # WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级最高）
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

'''
            content = content[:insert_pos] + ws_block + content[insert_pos:]
            print("[修复] 已添加 WebSocket location 配置")
        else:
            print("[错误] 未找到 location /api/ 块，无法自动添加")
            sys.exit(1)
    else:
        print("[错误] 未找到 server 块")
        sys.exit(1)

# 写入文件
with open(config_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] 配置已更新")
PYEOF

    if [ $? -eq 0 ]; then
        echo "[OK] WebSocket 配置已修复"
    else
        echo "[错误] 配置修复失败"
        exit 1
    fi
else
    echo ""
    echo ">>> [4] WebSocket 配置已正确，无需修复"
fi

# 5. 检查重复的 location 块
echo ""
echo ">>> [5] 检查重复的 location 块..."
ws_count=$(sudo grep -c "location /api/v1/notifications/ws" "$NGINX_CONFIG")
if [ "$ws_count" -gt 1 ]; then
    echo "[警告] 发现 $ws_count 个 WebSocket location 块（应该只有 1 个）"
    echo "[信息] 需要手动删除重复的块"
else
    echo "[OK] WebSocket location 块数量正确: $ws_count"
fi

# 6. 测试 Nginx 配置
echo ""
echo ">>> [6] 测试 Nginx 配置..."
if sudo nginx -t 2>&1 | grep -q "syntax is ok"; then
    echo "[OK] Nginx 配置测试通过"
else
    echo "[错误] Nginx 配置测试失败"
    sudo nginx -t
    exit 1
fi

# 7. 重新加载 Nginx
echo ""
echo ">>> [7] 重新加载 Nginx..."
sudo systemctl reload nginx
if [ $? -eq 0 ]; then
    echo "[OK] Nginx 已重新加载"
else
    echo "[错误] Nginx 重新加载失败"
    exit 1
fi

# 8. 验证配置
echo ""
echo ">>> [8] 验证配置..."
echo ""
echo "WebSocket location 配置:"
sudo grep -A 12 "location /api/v1/notifications/ws" "$NGINX_CONFIG"

# 9. 测试后端 WebSocket 服务
echo ""
echo ">>> [9] 检查后端服务..."
if sudo systemctl is-active --quiet liaotian-backend; then
    echo "[OK] 后端服务正在运行"
else
    echo "[警告] 后端服务未运行"
    sudo systemctl status liaotian-backend --no-pager | head -5
fi

echo ""
echo "============================================================"
echo "修复完成！"
echo "============================================================"
echo ""
echo "下一步："
echo "1. 在浏览器中刷新页面（F5）"
echo "2. 检查浏览器控制台，WebSocket 错误应该消失"
echo "3. 如果仍有问题，检查后端日志："
echo "   sudo journalctl -u liaotian-backend -n 50 | grep -i websocket"

