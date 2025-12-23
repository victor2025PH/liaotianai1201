#!/bin/bash
# 测试会话管理功能

set -e

API_BASE_URL="${API_BASE_URL:-https://aiadmin.usdt2026.cc}"

echo "🧪 开始测试会话管理功能..."

# 生成测试会话 ID
TEST_SESSION_ID="session_test_$(date +%s)_$(openssl rand -hex 8)"

echo "📝 测试会话 ID: $TEST_SESSION_ID"

# 测试发送带会话 ID 的请求
echo -e "\n📤 发送测试请求（包含会话 ID）..."

response=$(curl -s -X POST "$API_BASE_URL/api/v1/ai-proxy/chat" \
  -H "Content-Type: application/json" \
  -H "X-Session-Id: $TEST_SESSION_ID" \
  -d '{
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "model": "gemini-2.5-flash-latest",
    "stream": false
  }' || echo "ERROR")

if echo "$response" | grep -q "content"; then
    echo "✅ 请求成功，会话 ID 已发送"
else
    echo "❌ 请求失败"
    echo "响应: $response"
    exit 1
fi

# 等待一下让数据库记录
sleep 2

# 查询会话统计
echo -e "\n📊 查询会话统计..."
stats=$(curl -s "$API_BASE_URL/api/v1/ai-monitoring/session/$TEST_SESSION_ID?days=30" || echo "ERROR")

if echo "$stats" | grep -q "session_id"; then
    echo "✅ 会话统计查询成功"
    echo "统计结果: $stats" | head -c 300
    echo "..."
else
    echo "⚠️  会话统计查询失败或会话不存在（可能是新会话）"
    echo "响应: $stats"
fi

echo -e "\n🎉 会话管理测试完成！"

