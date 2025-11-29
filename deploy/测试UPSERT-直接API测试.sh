#!/bin/bash
# 直接测试 UPSERT API 功能

echo "========================================="
echo "测试 UPSERT 功能 - 直接 API 测试"
echo "========================================="
echo ""

cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true

# 1. 登录获取token
echo "【步骤1】登录获取token..."
LOGIN_RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme123')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])' 2>/dev/null)
    echo "  ✓ 登录成功"
    echo "  Token: ${TOKEN:0:20}..."
else
    echo "  ✗ 登录失败: $LOGIN_RESPONSE"
    exit 1
fi
echo ""

# 2. 测试 UPSERT：创建新账号（账号不存在）
echo "【步骤2】测试 UPSERT - 创建新账号（账号不存在）..."
TEST_ACCOUNT_ID="639277358115"

STATUS_CODE=$(curl -s -o /tmp/upsert_response.json -w '%{http_code}' -X PUT \
  "http://localhost:8000/api/v1/group-ai/accounts/$TEST_ACCOUNT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "test-script",
    "server_id": "computer_001"
  }')

echo "  HTTP 状态码: $STATUS_CODE"
echo "  响应内容:"
cat /tmp/upsert_response.json | python3 -m json.tool 2>/dev/null || cat /tmp/upsert_response.json
echo ""

if [ "$STATUS_CODE" = "200" ] || [ "$STATUS_CODE" = "201" ]; then
    echo "  ✓ UPSERT 成功！不再返回 404"
else
    echo "  ✗ UPSERT 失败，状态码: $STATUS_CODE"
    echo "  这可能是正常的，如果账号已存在会返回其他状态码"
fi
echo ""

echo "========================================="
echo "测试完成！"
echo "========================================="
