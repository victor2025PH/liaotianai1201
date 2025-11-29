#!/bin/bash
# 完整诊断404错误的脚本

cd ~/liaotian

echo "========================================="
echo "完整诊断404错误流程"
echo "========================================="
echo ""

echo "【1】检查后端服务状态..."
if ps aux | grep uvicorn | grep -v grep > /dev/null; then
    echo "  ✓ 后端服务正在运行"
    ps aux | grep uvicorn | grep -v grep
else
    echo "  ✗ 后端服务未运行，正在启动..."
    cd admin-backend
    source .venv/bin/activate
    pkill -f 'uvicorn.*app.main:app' || true
    sleep 2
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 &
    sleep 5
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "  ✓ 后端服务已启动"
    else
        echo "  ✗ 后端服务启动失败"
        exit 1
    fi
fi
echo ""

echo "【2】测试后端健康检查..."
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "  ✓ 后端健康检查通过"
else
    echo "  ✗ 后端健康检查失败"
    curl -s http://localhost:8000/health
fi
echo ""

echo "【3】测试登录API..."
LOGIN_RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme123')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])' 2>/dev/null)
    echo "  ✓ 登录成功"
    echo "  Token: ${TOKEN:0:30}..."
else
    echo "  ✗ 登录失败: $LOGIN_RESPONSE"
    exit 1
fi
echo ""

echo "【4】测试PUT端点路由..."
cd admin-backend
source .venv/bin/activate

python3 << EOF
from app.main import app

# 查找PUT accounts路由
routes_found = []
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        if 'PUT' in route.methods and 'account' in route.path.lower():
            routes_found.append(route.path)

if routes_found:
    print("  找到PUT accounts路由:")
    for r in routes_found:
        print(f"    PUT {r}")
else:
    print("  ✗ 未找到PUT accounts路由")
EOF

echo ""

echo "【5】测试PUT请求到后端..."
PUT_RESPONSE=$(curl -s -X PUT "http://localhost:8000/api/v1/group-ai/accounts/639277358115" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"script_id":"test-script","server_id":"computer_001"}')

echo "  响应状态码: $(curl -s -o /dev/null -w '%{http_code}' -X PUT 'http://localhost:8000/api/v1/group-ai/accounts/639277358115' -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"script_id":"test-script","server_id":"computer_001"}')"
echo "  响应内容: ${PUT_RESPONSE:0:200}..."
echo ""

echo "【6】查看后端日志（最近20行）..."
tail -20 /tmp/backend_final.log 2>/dev/null | grep -E "UPDATE_ACCOUNT|PUT|404|639277358115" || echo "  未找到相关日志"
echo ""

echo "========================================="
echo "诊断完成"
echo "========================================="
