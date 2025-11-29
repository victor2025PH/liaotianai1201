#!/bin/bash
# 验证 Nginx 配置修复结果

echo "============================================================"
echo "验证 Nginx 配置修复结果"
echo "============================================================"
echo ""

# 1. 检查 location 配置
echo ">>> [1] 检查 location 配置..."
echo ""
echo "WebSocket location:"
sudo grep -A 3 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc
echo ""
echo "API location:"
sudo grep -A 3 'location /api/' /etc/nginx/sites-available/aikz.usdt2026.cc
echo ""
echo "前端 location:"
sudo grep -A 3 'location / {' /etc/nginx/sites-available/aikz.usdt2026.cc | head -5
echo ""

# 2. 检查 proxy_pass 配置
echo ">>> [2] 检查 proxy_pass 配置..."
echo ""
echo "API proxy_pass:"
sudo grep 'proxy_pass.*8000' /etc/nginx/sites-available/aikz.usdt2026.cc | grep '/api/'
echo ""
echo "前端 proxy_pass:"
sudo grep 'proxy_pass.*3000' /etc/nginx/sites-available/aikz.usdt2026.cc
echo ""

# 3. 检查 location 数量
echo ">>> [3] 检查 location 数量..."
ws_count=$(sudo grep -c 'location /api/v1/notifications/ws' /etc/nginx/sites-available/aikz.usdt2026.cc)
api_count=$(sudo grep -c 'location /api/' /etc/nginx/sites-available/aikz.usdt2026.cc)
root_count=$(sudo grep -c 'location / {' /etc/nginx/sites-available/aikz.usdt2026.cc)
echo "WebSocket location: $ws_count (应该为 1)"
echo "API location: $api_count (应该为 1)"
echo "前端 location: $root_count (应该为 1)"
echo ""

# 4. 测试配置语法
echo ">>> [4] 测试配置语法..."
sudo nginx -t
echo ""

# 5. 检查 Nginx 状态
echo ">>> [5] 检查 Nginx 状态..."
sudo systemctl is-active nginx
echo ""

# 6. 测试 API 端点
echo ">>> [6] 测试 API 端点..."
echo -n "  /api/v1/dashboard: "
curl -s -o /dev/null -w '%{http_code}' http://localhost/api/v1/dashboard
echo ""
echo -n "  /api/v1/users/me: "
curl -s -o /dev/null -w '%{http_code}' http://localhost/api/v1/users/me
echo ""
echo ""

# 7. 检查后端服务
echo ">>> [7] 检查后端服务..."
sudo systemctl is-active liaotian-backend
echo ""

echo "============================================================"
echo "验证完成"
echo "============================================================"
echo ""
echo "如果所有检查都通过："
echo "1. 在前端浏览器中刷新页面（Ctrl+F5）"
echo "2. 打开开发者工具（F12）→ Network 标签"
echo "3. 检查 API 请求，应该返回 JSON 而不是 HTML"
echo "4. 检查 WebSocket 连接，应该看到状态码 101"
