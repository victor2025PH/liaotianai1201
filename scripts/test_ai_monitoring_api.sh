#!/bin/bash
# 测试 AI 监控 API 端点

set -e

API_BASE_URL="${API_BASE_URL:-https://aiadmin.usdt2026.cc}"

echo "🧪 开始测试 AI 监控 API..."

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试函数
test_endpoint() {
    local endpoint=$1
    local description=$2
    
    echo -e "\n${YELLOW}测试: $description${NC}"
    echo "URL: $API_BASE_URL$endpoint"
    
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$API_BASE_URL$endpoint" || echo "HTTP_CODE:000")
    http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE/d')
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✅ 成功 (HTTP $http_code)${NC}"
        echo "响应: $body" | head -c 200
        echo "..."
        return 0
    else
        echo -e "${RED}❌ 失败 (HTTP $http_code)${NC}"
        echo "响应: $body"
        return 1
    fi
}

# 测试各个端点
echo "📡 测试 API 基础连接..."
test_endpoint "/api/v1/ai-monitoring/summary?days=7" "使用摘要"

test_endpoint "/api/v1/ai-monitoring/daily?days=7" "每日统计"

test_endpoint "/api/v1/ai-monitoring/providers?days=7" "提供商统计"

test_endpoint "/api/v1/ai-monitoring/recent-errors?limit=10" "最近错误"

# 测试会话统计（使用示例会话 ID）
test_endpoint "/api/v1/ai-monitoring/session/session_test_123?days=30" "会话统计"

echo -e "\n${GREEN}🎉 API 测试完成！${NC}"

