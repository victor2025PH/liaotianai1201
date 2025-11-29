#!/bin/bash
# 最终修复 - 完整流程

set -e

echo "========================================="
echo "最终修复 UPSERT 功能"
echo "开始时间: $(date)"
echo "========================================="
echo ""

cd ~/liaotian/admin-backend/app/api/group_ai

# 步骤1: 检查文件
echo "【步骤1】检查文件..."
if grep -q "UPSERT 模式" accounts.py; then
    UPSERT_COUNT=$(grep -c "UPSERT 模式" accounts.py)
    echo "  ✓ 文件包含 UPSERT 代码（$UPSERT_COUNT 处）"
    
    # 显示 UPSERT 代码位置
    UPSERT_LINE=$(grep -n "UPSERT 模式" accounts.py | head -1 | cut -d: -f1)
    echo "  UPSERT 代码在第 $UPSERT_LINE 行"
    
    # 显示代码片段
    echo ""
    echo "  代码片段："
    sed -n "$((UPSERT_LINE-1)),$((UPSERT_LINE+3))p" accounts.py | head -5
else
    echo "  ✗ 文件不包含 UPSERT 代码"
    echo "  请先上传修改后的文件"
    exit 1
fi
echo ""

# 步骤2: 重启后端服务
echo "【步骤2】重启后端服务..."
cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true

echo "  停止所有 uvicorn 进程..."
pkill -9 -f 'uvicorn.*app.main:app' || true
pkill -9 -f 'python.*uvicorn.*app.main' || true
sleep 5

echo "  启动后端服务..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

echo "  等待服务启动..."
for i in {1..10}; do
    sleep 2
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✓ 后端服务已启动（等待了 $((i*2)) 秒）"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "  ⚠ 服务启动较慢，但继续执行..."
    fi
done

# 验证进程
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "  ✓ 后端进程正在运行 (PID: $BACKEND_PID)"
else
    echo "  ✗ 后端进程未运行，查看日志:"
    tail -50 /tmp/backend.log
    exit 1
fi
echo ""

# 步骤3: 测试 UPSERT
echo "【步骤3】测试 UPSERT 功能..."
echo "  登录..."
LOGIN_RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme123')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])' 2>/dev/null)
    echo "  ✓ 登录成功"
    
    echo ""
    echo "  测试账号: 639454959591"
    echo "  发送 PUT 请求（应该创建新账号，不再返回 404）..."
    
    RESPONSE=$(curl -s -w "\n\nHTTP_STATUS:%{http_code}" -X PUT \
      "http://localhost:8000/api/v1/group-ai/accounts/639454959591" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"script_id": "test-script", "server_id": "computer_002"}' 2>&1)
    
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | grep -v "HTTP_STATUS")
    
    echo ""
    echo "  HTTP 状态码: $HTTP_STATUS"
    
    if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "201" ]; then
        echo "  ✓✓✓ 成功！UPSERT 功能正常工作，不再返回 404！"
        echo ""
        echo "  响应内容:"
        echo "$BODY" | python3 -m json.tool 2>/dev/null | head -30 || echo "$BODY" | head -15
    else
        echo "  ✗ 仍然返回错误状态码: $HTTP_STATUS"
        echo ""
        echo "  响应内容:"
        echo "$BODY" | head -20
        echo ""
        echo "  查看后端日志（最近的相关日志）:"
        tail -100 /tmp/backend.log | grep -E "639454959591|UPDATE_ACCOUNT|UPSERT|ERROR" | tail -15
    fi
else
    echo "  ✗ 登录失败"
    echo "  响应: $LOGIN_RESPONSE" | head -5
fi
echo ""

echo "========================================="
echo "修复完成！"
echo "完成时间: $(date)"
echo "========================================="
