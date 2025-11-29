#!/bin/bash
# 检查 WebSocket 配置是否已修复

echo "============================================================"
echo "检查 WebSocket 配置"
echo "============================================================"

NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

echo ""
echo ">>> [1] 检查 WebSocket location 是否存在..."
if sudo grep -q "location /api/v1/notifications/ws" "$NGINX_CONFIG"; then
    echo "[OK] WebSocket location 已存在"
    echo ""
    echo "配置内容："
    sudo grep -A 15 "location /api/v1/notifications/ws" "$NGINX_CONFIG"
else
    echo "[错误] WebSocket location 不存在！"
    exit 1
fi

echo ""
echo ">>> [2] 检查配置是否正确..."
has_upgrade=$(sudo grep -A 15 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | grep -q "Upgrade" && echo "是" || echo "否")
has_connection=$(sudo grep -A 15 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | grep -q "Connection.*upgrade" && echo "是" || echo "否")
proxy_pass_correct=$(sudo grep -A 5 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | grep "proxy_pass" | grep -q "http://127.0.0.1:8000" && echo "是" || echo "否")

echo "Upgrade header: $has_upgrade"
echo "Connection header: $has_connection"
echo "proxy_pass 正确: $proxy_pass_correct"

if [ "$has_upgrade" = "是" ] && [ "$has_connection" = "是" ] && [ "$proxy_pass_correct" = "是" ]; then
    echo "[OK] WebSocket 配置正确"
else
    echo "[错误] WebSocket 配置不完整！"
    exit 1
fi

echo ""
echo ">>> [3] 检查是否有重复的 location 块..."
ws_count=$(sudo grep -c "location /api/v1/notifications/ws" "$NGINX_CONFIG")
echo "WebSocket location 块数量: $ws_count"
if [ "$ws_count" -eq 1 ]; then
    echo "[OK] 没有重复的 location 块"
else
    echo "[警告] 发现 $ws_count 个 WebSocket location 块（应该只有 1 个）"
fi

echo ""
echo ">>> [4] 检查 Nginx 配置语法..."
if sudo nginx -t 2>&1 | grep -q "syntax is ok"; then
    echo "[OK] Nginx 配置语法正确"
else
    echo "[错误] Nginx 配置语法错误"
    sudo nginx -t
    exit 1
fi

echo ""
echo ">>> [5] 检查 Nginx 服务状态..."
if sudo systemctl is-active --quiet nginx; then
    echo "[OK] Nginx 服务正在运行"
else
    echo "[错误] Nginx 服务未运行"
    sudo systemctl status nginx --no-pager | head -5
fi

echo ""
echo ">>> [6] 检查后端服务状态..."
if sudo systemctl is-active --quiet liaotian-backend; then
    echo "[OK] 后端服务正在运行"
else
    echo "[警告] 后端服务未运行"
    sudo systemctl status liaotian-backend --no-pager | head -5
fi

echo ""
echo ">>> [7] 检查后端日志（WebSocket 相关）..."
echo "最近 20 条日志中包含 'websocket' 或 'ws' 的条目："
sudo journalctl -u liaotian-backend -n 100 --no-pager | grep -i "websocket\|ws" | tail -5 || echo "未找到相关日志"

echo ""
echo "============================================================"
echo "检查完成"
echo "============================================================"

