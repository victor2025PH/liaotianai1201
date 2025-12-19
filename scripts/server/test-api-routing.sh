#!/bin/bash
# ============================================================
# 测试 API 路由配置
# ============================================================

echo "=========================================="
echo "🧪 测试 API 路由配置"
echo "=========================================="
echo ""

# 1. 测试直接访问后端
echo "[1/4] 测试直接访问后端..."
echo "----------------------------------------"
echo "测试 /health:"
curl -s http://127.0.0.1:8000/health | head -3
echo ""
echo "测试 /api/v1 (根路径):"
curl -s http://127.0.0.1:8000/api/v1 2>&1 | head -3
echo ""
echo ""

# 2. 测试通过 Nginx 访问
echo "[2/4] 测试通过 Nginx 访问..."
echo "----------------------------------------"
echo "测试 /health (通过 Nginx):"
curl -s http://127.0.0.1/health | head -3
echo ""
echo "测试 /api/v1 (通过 Nginx):"
curl -s http://127.0.0.1/api/v1 2>&1 | head -3
echo ""
echo "测试 /api/v1/notifications/unread-count (通过 Nginx):"
curl -s -H "Authorization: Bearer test" http://127.0.0.1/api/v1/notifications/unread-count 2>&1 | head -5
echo ""
echo ""

# 3. 检查 Nginx 配置
echo "[3/4] 检查 Nginx 配置..."
echo "----------------------------------------"
NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
if [ -f "$NGINX_CONFIG" ]; then
    echo "Nginx 配置中的 /api/ 部分:"
    grep -A 10 "location /api/" "$NGINX_CONFIG" | head -15
else
    echo "❌ Nginx 配置文件不存在"
fi
echo ""

# 4. 检查后端路由
echo "[4/4] 检查后端路由..."
echo "----------------------------------------"
echo "测试后端 /docs (应该显示 API 文档):"
curl -s http://127.0.0.1:8000/docs 2>&1 | grep -o "<title>.*</title>" | head -1 || echo "无法访问 /docs"
echo ""
echo "测试后端 /openapi.json:"
curl -s http://127.0.0.1:8000/openapi.json 2>&1 | head -5
echo ""

echo "=========================================="
echo "✅ 测试完成"
echo "=========================================="
echo ""
echo "如果 /api/v1/notifications/unread-count 返回连接被拒绝，"
echo "请检查："
echo "1. Nginx 配置是否正确加载: sudo nginx -t"
echo "2. Nginx 是否正在运行: sudo systemctl status nginx"
echo "3. 后端服务是否正在运行: sudo -u ubuntu pm2 list"
echo ""

