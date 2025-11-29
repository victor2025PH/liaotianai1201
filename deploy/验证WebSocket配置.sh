#!/bin/bash
# 验证 WebSocket 配置

echo "=========================================="
echo "验证 WebSocket 配置"
echo "=========================================="
echo

NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

echo "[1] 检查 WebSocket location 配置..."
if sudo grep -q "location /api/v1/notifications/ws" "$NGINX_CONFIG"; then
    echo "✓ WebSocket location 存在"
    echo
    echo "配置内容："
    sudo grep -A 15 "location /api/v1/notifications/ws" "$NGINX_CONFIG"
    echo
    
    # 检查关键配置
    if sudo grep -A 15 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | grep -q "Upgrade"; then
        echo "✓ Upgrade header 已配置"
    else
        echo "✗ Upgrade header 缺失"
    fi
    
    if sudo grep -A 15 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | grep -q "Connection.*upgrade"; then
        echo "✓ Connection header 已配置"
    else
        echo "✗ Connection header 缺失"
    fi
    
    if sudo grep -A 15 "location /api/v1/notifications/ws" "$NGINX_CONFIG" | grep -q "proxy_pass.*127.0.0.1:8000"; then
        echo "✓ proxy_pass 指向后端 (127.0.0.1:8000)"
    else
        echo "✗ proxy_pass 配置错误"
    fi
else
    echo "✗ WebSocket location 不存在"
fi

echo
echo "[2] 检查 Nginx 配置语法..."
if sudo nginx -t 2>&1 | grep -q "syntax is ok"; then
    echo "✓ Nginx 配置语法正确"
else
    echo "✗ Nginx 配置语法错误"
    sudo nginx -t
fi

echo
echo "[3] 检查服务状态..."
echo "Nginx: $(sudo systemctl is-active nginx)"
echo "后端: $(sudo systemctl is-active liaotian-backend)"

echo
echo "[4] 检查后端 WebSocket 端点..."
if sudo systemctl is-active --quiet liaotian-backend; then
    echo "后端服务运行中"
    # 检查后端日志中是否有 WebSocket 相关错误
    echo "最近的后端日志（WebSocket 相关）："
    sudo journalctl -u liaotian-backend -n 20 --no-pager | grep -i websocket || echo "无 WebSocket 相关日志"
else
    echo "✗ 后端服务未运行"
fi

echo
echo "=========================================="
echo "验证完成"
echo "=========================================="

