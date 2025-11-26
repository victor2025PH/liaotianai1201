#!/bin/bash
# 最终部署状态检查

echo "=== 服务状态 ==="
systemctl is-active smart-tg-backend 2>/dev/null && echo "✓ 后端服务运行中" || echo "✗ 后端服务未运行"
systemctl is-active smart-tg-frontend 2>/dev/null && echo "✓ 前端服务运行中" || echo "✗ 前端服务未运行"

echo ""
echo "=== 健康检查 ==="
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null)
if [ -n "$HEALTH" ]; then
    echo "✓ 后端健康检查: $HEALTH"
else
    echo "✗ 后端健康检查失败"
fi

FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)
if [ "$FRONTEND" = "200" ]; then
    echo "✓ 前端服务可访问"
else
    echo "✗ 前端服务不可访问 (HTTP $FRONTEND)"
fi

