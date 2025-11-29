#!/bin/bash
# 测试 UPSERT 功能 - 在远程服务器 ubuntu@165.154.233.55 上执行

set -e

LOG_FILE="/tmp/test_upsert_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================="
echo "测试 UPSERT 功能"
echo "开始时间: $(date)"
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
else
    echo "  ✗ 登录失败: $LOGIN_RESPONSE"
    exit 1
fi
echo ""

# 2. 测试 UPSERT：创建新账号（账号不存在）
echo "【步骤2】测试 UPSERT - 创建新账号（账号不存在）..."
TEST_ACCOUNT_ID="639277358115"

# 先删除账号（如果存在），确保测试干净
echo "  清理：删除测试账号（如果存在）..."
curl -s -X DELETE "http://localhost:8000/api/v1/group-ai/accounts/$TEST_ACCOUNT_ID" \
  -H "Authorization: Bearer $TOKEN" > /dev/null 2>&1 || true
sleep 1

# 第一次调用：创建新账号
echo "  第一次 PUT 请求（创建新账号）..."
STATUS_CODE=$(curl -s -o /tmp/upsert_create.json -w '%{http_code}' -X PUT \
  "http://localhost:8000/api/v1/group-ai/accounts/$TEST_ACCOUNT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "test-script",
    "server_id": "computer_001"
  }')

echo "  HTTP 状态码: $STATUS_CODE"
if [ "$STATUS_CODE" = "200" ] || [ "$STATUS_CODE" = "201" ]; then
    echo "  ✓ UPSERT 成功（创建新账号）"
    echo "  响应内容:"
    cat /tmp/upsert_create.json | python3 -m json.tool 2>/dev/null || cat /tmp/upsert_create.json
else
    echo "  ✗ UPSERT 失败"
    echo "  错误响应:"
    cat /tmp/upsert_create.json
    exit 1
fi
echo ""

# 3. 验证账号已创建
echo "【步骤3】验证账号是否已创建..."
ACCOUNT_EXISTS=$(curl -s "http://localhost:8000/api/v1/group-ai/accounts?page=1&page_size=100" \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -c "import sys, json; accounts=json.load(sys.stdin); print('YES' if any(acc.get('account_id') == '$TEST_ACCOUNT_ID' for acc in accounts) else 'NO')" 2>/dev/null || echo "NO")

if [ "$ACCOUNT_EXISTS" = "YES" ]; then
    echo "  ✓ 账号 $TEST_ACCOUNT_ID 已存在于数据库中"
else
    echo "  ✗ 账号 $TEST_ACCOUNT_ID 未找到"
    exit 1
fi
echo ""

# 4. 测试更新已存在的账号
echo "【步骤4】测试 UPSERT - 更新已存在的账号..."
STATUS_CODE=$(curl -s -o /tmp/upsert_update.json -w '%{http_code}' -X PUT \
  "http://localhost:8000/api/v1/group-ai/accounts/$TEST_ACCOUNT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "updated-script",
    "server_id": "computer_001"
  }')

echo "  HTTP 状态码: $STATUS_CODE"
if [ "$STATUS_CODE" = "200" ]; then
    echo "  ✓ UPSERT 成功（更新已存在的账号）"
    echo "  响应内容:"
    cat /tmp/upsert_update.json | python3 -m json.tool 2>/dev/null || cat /tmp/upsert_update.json
    
    # 验证 script_id 是否已更新
    UPDATED_SCRIPT_ID=$(cat /tmp/upsert_update.json | python3 -c "import sys, json; print(json.load(sys.stdin).get('script_id', ''))" 2>/dev/null || echo "")
    if [ "$UPDATED_SCRIPT_ID" = "updated-script" ]; then
        echo "  ✓ script_id 已更新为: updated-script"
    else
        echo "  ⚠ script_id 未正确更新，当前值: $UPDATED_SCRIPT_ID"
    fi
else
    echo "  ✗ 更新失败"
    cat /tmp/upsert_update.json
    exit 1
fi
echo ""

# 5. 测试缺少 server_id 的情况
echo "【步骤5】测试缺少 server_id 的情况（应该返回 400）..."
TEST_ACCOUNT_ID_2="test_account_999"
STATUS_CODE=$(curl -s -o /tmp/upsert_no_server_id.json -w '%{http_code}' -X PUT \
  "http://localhost:8000/api/v1/group-ai/accounts/$TEST_ACCOUNT_ID_2" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "test-script"
  }')

echo "  HTTP 状态码: $STATUS_CODE"
if [ "$STATUS_CODE" = "400" ]; then
    echo "  ✓ 正确返回 400（缺少 server_id）"
    echo "  错误信息:"
    cat /tmp/upsert_no_server_id.json | python3 -m json.tool 2>/dev/null || cat /tmp/upsert_no_server_id.json
else
    echo "  ⚠ 预期返回 400，但实际返回: $STATUS_CODE"
    cat /tmp/upsert_no_server_id.json
fi
echo ""

echo "========================================="
echo "测试完成！"
echo "完成时间: $(date)"
echo "========================================="
echo ""
echo "完整日志已保存到: $LOG_FILE"
echo ""
