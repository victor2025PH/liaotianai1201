#!/bin/bash
# 完整部署并测试 UPSERT 功能

set -e

LOG_FILE="/tmp/deploy_upsert_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================="
echo "完整部署并测试 UPSERT 功能"
echo "开始时间: $(date)"
echo "========================================="
echo ""

cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true

# 1. 检查文件是否包含 UPSERT 代码
echo "【步骤1】检查文件是否包含 UPSERT 代码..."
if grep -q "UPSERT 模式" app/api/group_ai/accounts.py; then
    echo "  ✓ 文件已包含 UPSERT 代码"
else
    echo "  ✗ 文件不包含 UPSERT 代码，需要上传修改后的文件"
    exit 1
fi
echo ""

# 2. 重启后端服务
echo "【步骤2】重启后端服务..."
pkill -f "uvicorn.*app.main:app" || true
sleep 2

echo "  启动后端服务..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 5

# 验证服务是否启动
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✓ 后端服务已启动"
else
    echo "  ✗ 后端服务启动失败，查看日志:"
    tail -30 /tmp/backend.log
    exit 1
fi
echo ""

# 3. 测试 UPSERT 功能
echo "【步骤3】测试 UPSERT 功能..."
echo "  3.1 登录获取token..."
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

echo "  3.2 测试 UPSERT - 创建新账号（账号不存在）..."
TEST_ACCOUNT_ID="639277358115"

# 先删除账号（如果存在），确保测试干净
echo "    清理：删除测试账号（如果存在）..."
curl -s -X DELETE "http://localhost:8000/api/v1/group-ai/accounts/$TEST_ACCOUNT_ID" \
  -H "Authorization: Bearer $TOKEN" > /dev/null 2>&1 || true
sleep 1

# 第一次调用：创建新账号
echo "    第一次 PUT 请求（创建新账号）..."
STATUS_CODE=$(curl -s -o /tmp/upsert_create.json -w '%{http_code}' -X PUT \
  "http://localhost:8000/api/v1/group-ai/accounts/$TEST_ACCOUNT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "test-script",
    "server_id": "computer_001"
  }')

echo "    HTTP 状态码: $STATUS_CODE"
if [ "$STATUS_CODE" = "200" ] || [ "$STATUS_CODE" = "201" ]; then
    echo "    ✓ UPSERT 成功（创建新账号），不再返回 404！"
    echo "    响应内容:"
    cat /tmp/upsert_create.json | python3 -m json.tool 2>/dev/null || cat /tmp/upsert_create.json
else
    echo "    ✗ UPSERT 失败，状态码: $STATUS_CODE"
    echo "    错误响应:"
    cat /tmp/upsert_create.json
    exit 1
fi
echo ""

echo "  3.3 验证账号已创建..."
ACCOUNT_EXISTS=$(curl -s "http://localhost:8000/api/v1/group-ai/accounts?page=1&page_size=100" \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -c "import sys, json; accounts=json.load(sys.stdin); print('YES' if any(acc.get('account_id') == '$TEST_ACCOUNT_ID' for acc in accounts) else 'NO')" 2>/dev/null || echo "NO")

if [ "$ACCOUNT_EXISTS" = "YES" ]; then
    echo "    ✓ 账号 $TEST_ACCOUNT_ID 已存在于数据库中"
else
    echo "    ✗ 账号 $TEST_ACCOUNT_ID 未找到"
    exit 1
fi
echo ""

echo "  3.4 测试 UPSERT - 更新已存在的账号..."
STATUS_CODE=$(curl -s -o /tmp/upsert_update.json -w '%{http_code}' -X PUT \
  "http://localhost:8000/api/v1/group-ai/accounts/$TEST_ACCOUNT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "updated-script",
    "server_id": "computer_001"
  }')

echo "    HTTP 状态码: $STATUS_CODE"
if [ "$STATUS_CODE" = "200" ]; then
    echo "    ✓ UPSERT 成功（更新已存在的账号）"
    echo "    响应内容:"
    cat /tmp/upsert_update.json | python3 -m json.tool 2>/dev/null || cat /tmp/upsert_update.json
else
    echo "    ✗ 更新失败，状态码: $STATUS_CODE"
    cat /tmp/upsert_update.json
    exit 1
fi
echo ""

echo "========================================="
echo "✓ 部署和测试完成！"
echo "完成时间: $(date)"
echo "========================================="
echo ""
echo "测试结果总结:"
echo "  - UPSERT 功能正常工作"
echo "  - 账号不存在时，不再返回 404，而是创建新记录"
echo "  - 账号存在时，正常更新记录"
echo ""
echo "完整日志已保存到: $LOG_FILE"
