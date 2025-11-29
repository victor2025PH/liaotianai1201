#!/bin/bash
# 快速诊断 API 404 错误

echo "============================================================"
echo "诊断 API 404 错误"
echo "============================================================"
echo ""

# 1. 检查后端服务
echo ">>> [1] 后端服务状态："
sudo systemctl status liaotian-backend --no-pager | head -10
echo ""

# 2. 检查端口
echo ">>> [2] 端口监听："
sudo ss -tlnp | grep -E ':8000|:80'
echo ""

# 3. 测试后端 API（直接访问）
echo ">>> [3] 测试后端 API（localhost:8000）："
echo -n "  /health: "
curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health
echo ""
echo -n "  /api/v1/dashboard: "
curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/v1/dashboard
echo ""
echo -n "  /api/v1/users/me: "
curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/v1/users/me
echo ""
echo ""

# 4. 测试通过 Nginx
echo ">>> [4] 测试通过 Nginx："
echo -n "  /api/v1/health: "
curl -s -o /dev/null -w '%{http_code}' http://localhost/api/v1/health
echo ""
echo ""

# 5. 检查 Nginx 配置
echo ">>> [5] Nginx API 路由配置："
sudo grep -A 5 'location /api/' /etc/nginx/sites-available/aikz.usdt2026.cc | head -10
echo ""

# 6. 后端日志
echo ">>> [6] 后端日志（最近 5 行）："
sudo journalctl -u liaotian-backend -n 5 --no-pager
echo ""

echo "============================================================"
echo "诊断完成"
echo "============================================================"

