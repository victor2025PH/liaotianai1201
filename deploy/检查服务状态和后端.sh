#!/bin/bash
# 检查服务状态和后端连接

echo "=========================================="
echo "检查服务状态和后端连接"
echo "=========================================="
echo

echo "[1] Nginx 服务状态..."
sudo systemctl status nginx --no-pager | head -10
echo

echo "[2] 后端服务状态..."
sudo systemctl status liaotian-backend --no-pager | head -10
echo

echo "[3] 检查后端端口监听..."
sudo netstat -tlnp 2>/dev/null | grep :8000 || sudo ss -tlnp 2>/dev/null | grep :8000 || echo "未找到端口 8000 监听"
echo

echo "[4] 测试后端 WebSocket 端点（直接连接）..."
curl -i -N -H 'Connection: Upgrade' -H 'Upgrade: websocket' -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: test' http://127.0.0.1:8000/api/v1/notifications/ws/test@example.com 2>&1 | head -15
echo

echo "[5] 后端日志（最近10条，WebSocket 相关）..."
sudo journalctl -u liaotian-backend -n 50 --no-pager | grep -i websocket | tail -10 || echo "未找到 WebSocket 相关日志"
echo

echo "[6] Nginx 错误日志（最近10条，WebSocket 相关）..."
sudo tail -50 /var/log/nginx/error.log | grep -i websocket | tail -10 || echo "未找到 WebSocket 相关错误"
echo

echo "=========================================="
echo "检查完成"
echo "=========================================="

