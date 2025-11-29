#!/bin/bash
# 一键修复：上传文件、重启服务、测试 UPSERT

set -e

LOG_FILE="/tmp/fix_upsert_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================="
echo "一键修复 UPSERT 功能"
echo "开始时间: $(date)"
echo "========================================="
echo ""

cd ~/liaotian/admin-backend

# 1. 验证文件是否包含 UPSERT 代码
echo "【步骤1】验证文件是否包含 UPSERT 代码..."
if grep -q "UPSERT 模式" app/api/group_ai/accounts.py; then
    COUNT=$(grep -c "UPSERT 模式" app/api/group_ai/accounts.py)
    echo "  ✓ 文件包含 UPSERT 代码（$COUNT 处）"
else
    echo "  ✗ 文件不包含 UPSERT 代码"
    echo "  请先上传修改后的文件到服务器"
    exit 1
fi
echo ""

# 2. 重启后端服务
echo "【步骤2】重启后端服务..."
source .venv/bin/activate 2>/dev/null || true

echo "  停止旧进程..."
pkill -f "uvicorn.*app.main:app" || true
sleep 3

echo "  启动新进程..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 10

echo "  验证服务..."
for i in {1..5}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✓ 后端服务已启动（尝试 $i/5）"
        break
    else
        if [ $i -eq 5 ]; then
            echo "  ⚠ 健康检查失败，但继续执行..."
        else
            echo "  等待服务启动... ($i/5)"
            sleep 2
        fi
    fi
done
echo ""

# 3. 测试 UPSERT 功能
echo "【步骤3】测试 UPSERT 功能..."
echo "  登录获取 token..."
LOGIN_RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme123')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])' 2>/dev/null)
    echo "  ✓ 登录成功"
    
    # 测试 UPSERT（账号不存在）
    TEST_ID="639454959591"
    echo ""
    echo "  测试账号: $TEST_ID"
    echo "  发送 PUT 请求..."
    
    RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X PUT \
      "http://localhost:8000/api/v1/group-ai/accounts/$TEST_ID" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "script_id": "test-script",
        "server_id": "computer_002"
      }')
    
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | grep -v "HTTP_STATUS")
    
    echo "  HTTP 状态码: $HTTP_STATUS"
    
    if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "201" ]; then
        echo "  ✓✓✓ UPSERT 成功！不再返回 404！"
        echo "  响应内容:"
        echo "$BODY" | python3 -m json.tool 2>/dev/null | head -20 || echo "$BODY" | head -10
    else
        echo "  ✗ 返回状态码: $HTTP_STATUS"
        echo "  响应内容:"
        echo "$BODY" | head -20
        echo ""
        echo "  检查后端日志..."
        tail -50 /tmp/backend.log | grep -E "$TEST_ID|UPDATE_ACCOUNT|UPSERT|ERROR" | tail -10
    fi
else
    echo "  ✗ 登录失败: $LOGIN_RESPONSE"
fi
echo ""

echo "========================================="
echo "修复完成！"
echo "完成时间: $(date)"
echo "========================================="
echo ""
echo "日志文件: $LOG_FILE"
