#!/bin/bash
# ============================================================
# 测试通知 API 端点
# ============================================================

echo "=========================================="
echo "🧪 测试通知 API 端点"
echo "=========================================="
echo ""

# 1. 测试直接访问后端
echo "[1/4] 测试直接访问后端..."
echo "----------------------------------------"
echo "测试 /api/v1/notifications (列表，需要认证):"
curl -s -w "\nHTTP Status: %{http_code}\n" http://127.0.0.1:8000/api/v1/notifications 2>&1 | head -5
echo ""

echo "测试 /api/v1/notifications/unread-count (需要认证):"
curl -s -w "\nHTTP Status: %{http_code}\n" http://127.0.0.1:8000/api/v1/notifications/unread-count 2>&1 | head -5
echo ""

# 2. 测试通过 Nginx 访问
echo "[2/4] 测试通过 Nginx 访问..."
echo "----------------------------------------"
echo "测试 /api/v1/notifications (通过 Nginx):"
curl -s -w "\nHTTP Status: %{http_code}\n" http://127.0.0.1/api/v1/notifications 2>&1 | head -5
echo ""

echo "测试 /api/v1/notifications/unread-count (通过 Nginx):"
curl -s -w "\nHTTP Status: %{http_code}\n" http://127.0.0.1/api/v1/notifications/unread-count 2>&1 | head -5
echo ""

# 3. 检查后端路由注册
echo "[3/4] 检查后端路由注册..."
echo "----------------------------------------"
echo "查看后端 OpenAPI 文档中的通知相关路由:"
curl -s http://127.0.0.1:8000/openapi.json 2>/dev/null | python3 -m json.tool 2>/dev/null | grep -A 2 "/api/v1/notifications" | head -20 || echo "无法解析 OpenAPI JSON"
echo ""

# 4. 测试认证端点（用于获取 token）
echo "[4/4] 测试认证端点..."
echo "----------------------------------------"
echo "测试 /api/v1/auth/login (登录端点):"
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' 2>&1 | head -5
echo ""

echo "=========================================="
echo "📊 测试结果分析"
echo "=========================================="
echo ""
echo "如果返回 401 Unauthorized，说明端点存在但需要认证"
echo "如果返回 404 Not Found，说明路由未注册"
echo "如果返回 422 Validation Error，说明请求格式有问题"
echo ""
echo "前端请求 /api/v1/notifications/unread-count 时，"
echo "需要确保："
echo "1. 请求包含 Authorization header"
echo "2. Token 有效且未过期"
echo "3. 用户有相应权限"
echo ""

