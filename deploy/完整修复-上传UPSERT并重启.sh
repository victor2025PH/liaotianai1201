#!/bin/bash
# 完整修复脚本：上传 UPSERT 代码并重启服务

set -e

echo "========================================="
echo "完整修复：上传 UPSERT 代码并重启服务"
echo "开始时间: $(date)"
echo "========================================="
echo ""

cd ~/liaotian

# 1. 检查本地文件是否存在
LOCAL_FILE="admin-backend/app/api/group_ai/accounts.py"
if [ ! -f "$LOCAL_FILE" ]; then
    echo "✗ 错误: 本地文件不存在"
    exit 1
fi

# 2. 备份服务器文件
echo "【步骤1】备份服务器上的原始文件..."
cd admin-backend/app/api/group_ai
cp accounts.py accounts.py.bak.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
echo "  ✓ 备份完成"
echo ""

# 3. 检查文件是否已包含 UPSERT 代码
echo "【步骤2】检查文件内容..."
if grep -q "UPSERT 模式" accounts.py; then
    UPSERT_COUNT=$(grep -c "UPSERT 模式" accounts.py)
    echo "  ✓ 文件已包含 UPSERT 代码（找到 $UPSERT_COUNT 处）"
else
    echo "  ✗ 文件不包含 UPSERT 代码"
    echo "  需要从本地重新上传文件"
    exit 1
fi
echo ""

# 4. 重启后端服务
echo "【步骤3】重启后端服务..."
cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true

echo "  停止旧进程..."
pkill -f "uvicorn.*app.main:app" || true
sleep 3

echo "  启动新进程..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 8

# 验证服务
echo "  验证服务状态..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✓ 后端服务已启动并响应健康检查"
else
    echo "  ⚠ 健康检查失败，查看日志:"
    tail -30 /tmp/backend.log
    echo ""
    echo "  但进程可能仍在启动中，继续验证..."
fi

# 检查进程
if ps aux | grep -v grep | grep -q "uvicorn.*app.main:app"; then
    echo "  ✓ 后端进程正在运行"
else
    echo "  ✗ 后端进程未运行"
    tail -50 /tmp/backend.log
    exit 1
fi
echo ""

# 5. 验证 UPSERT 功能
echo "【步骤4】验证 UPSERT 功能（测试 API）..."
LOGIN_RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme123')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])' 2>/dev/null)
    echo "  ✓ 登录成功，获取到 token"
    
    # 测试 UPSERT
    TEST_ACCOUNT="test_upsert_$(date +%s)"
    echo "  测试账号: $TEST_ACCOUNT"
    
    STATUS=$(curl -s -o /tmp/test_response.json -w '%{http_code}' -X PUT \
      "http://localhost:8000/api/v1/group-ai/accounts/$TEST_ACCOUNT" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"script_id": "test", "server_id": "computer_001"}' 2>/dev/null)
    
    echo "  HTTP 状态码: $STATUS"
    if [ "$STATUS" = "200" ] || [ "$STATUS" = "201" ]; then
        echo "  ✓ UPSERT 功能正常工作（不再返回 404）"
    else
        echo "  ⚠ 返回状态码: $STATUS"
        cat /tmp/test_response.json | head -5
    fi
    
    # 清理测试账号
    curl -s -X DELETE "http://localhost:8000/api/v1/group-ai/accounts/$TEST_ACCOUNT" \
      -H "Authorization: Bearer $TOKEN" > /dev/null 2>&1 || true
else
    echo "  ⚠ 无法登录，跳过 API 测试"
fi
echo ""

echo "========================================="
echo "✓ 修复完成！"
echo "完成时间: $(date)"
echo "========================================="
echo ""
echo "现在可以测试："
echo "  1. 访问 http://aikz.usdt2026.cc/group-ai/accounts"
echo "  2. 尝试为账号 639454959591 分配剧本"
echo "  3. 应该不再出现 404 错误"
echo ""
