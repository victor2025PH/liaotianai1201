#!/bin/bash
# 部署状态检查脚本

echo "=== 服务状态检查 ==="
if systemctl is-active --quiet smart-tg-backend 2>/dev/null; then
    echo "BACKEND_RUNNING"
    systemctl status smart-tg-backend --no-pager -l | head -n 3
else
    echo "BACKEND_STOPPED"
fi

if systemctl is-active --quiet smart-tg-frontend 2>/dev/null; then
    echo "FRONTEND_RUNNING"
    systemctl status smart-tg-frontend --no-pager -l | head -n 3
else
    echo "FRONTEND_STOPPED"
fi

echo ""
echo "=== 端口检查 ==="
sudo netstat -tlnp 2>/dev/null | grep -E ':8000|:3000' || echo "端口未被占用"

echo ""
echo "=== 健康检查 ==="
curl -s http://localhost:8000/health 2>/dev/null || echo "后端健康检查失败"
curl -s http://localhost:3000 >/dev/null 2>&1 && echo "前端可访问" || echo "前端不可访问"

echo ""
echo "=== 目录检查 ==="
PROJECT_PATH="${1:-/opt/smart-tg}"
[ -d "$PROJECT_PATH/admin-backend" ] && echo "BACKEND_DIR_EXISTS" || echo "BACKEND_DIR_MISSING"
[ -d "$PROJECT_PATH/saas-demo" ] && echo "FRONTEND_DIR_EXISTS" || echo "FRONTEND_DIR_MISSING"

