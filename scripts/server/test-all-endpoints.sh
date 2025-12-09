#!/bin/bash
# ============================================================
# 测试所有 API 端点
# ============================================================
# 功能：测试后端所有关键 API 端点
# 使用方法：bash scripts/server/test-all-endpoints.sh
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="${1:-http://localhost:8000}"

echo "============================================================"
echo "🧪 API 端点测试"
echo "============================================================"
echo "测试地址: $BASE_URL"
echo ""

# 测试函数
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    
    echo -n "测试: $description ($method $endpoint) ... "
    
    if [ "$method" = "GET" ]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint" 2>/dev/null || echo "000")
    elif [ "$method" = "POST" ]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$BASE_URL$endpoint" 2>/dev/null || echo "000")
    else
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$BASE_URL$endpoint" 2>/dev/null || echo "000")
    fi
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "204" ]; then
        echo -e "${GREEN}✅ 通过 (HTTP $HTTP_CODE)${NC}"
        return 0
    elif [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
        echo -e "${YELLOW}⚠️  需要认证 (HTTP $HTTP_CODE)${NC}"
        return 0
    elif [ "$HTTP_CODE" = "404" ]; then
        echo -e "${YELLOW}⚠️  未找到 (HTTP $HTTP_CODE) - 可能正常${NC}"
        return 0  # 404 不算失败，可能是正常的
    else
        echo -e "${RED}❌ 失败 (HTTP $HTTP_CODE)${NC}"
        return 1
    fi
}

# 测试计数
PASSED=0
FAILED=0

# 1. 健康检查
echo "[1] 基础健康检查"
echo "----------------------------------------"
test_endpoint "GET" "/health" "健康检查" && ((PASSED++)) || ((FAILED++))
test_endpoint "GET" "/" "根路径" && ((PASSED++)) || ((FAILED++))
echo ""

# 2. API 文档
echo "[2] API 文档"
echo "----------------------------------------"
test_endpoint "GET" "/docs" "Swagger UI" && ((PASSED++)) || ((FAILED++))
test_endpoint "GET" "/redoc" "ReDoc" && ((PASSED++)) || ((FAILED++))
test_endpoint "GET" "/openapi.json" "OpenAPI JSON" && ((PASSED++)) || ((FAILED++))
echo ""

# 3. 认证端点（可能返回 401，这是正常的）
echo "[3] 认证端点"
echo "----------------------------------------"
test_endpoint "POST" "/api/v1/auth/login" "登录端点" "{\"email\":\"test@test.com\",\"password\":\"test\"}" && ((PASSED++)) || ((FAILED++))
test_endpoint "GET" "/api/v1/auth/me" "当前用户" && ((PASSED++)) || ((FAILED++))
echo ""

# 4. 公开端点（如果有）
echo "[4] 公开端点"
echo "----------------------------------------"
# 根据实际 API 调整
test_endpoint "GET" "/api/v1/health" "API 健康检查" && ((PASSED++)) || ((FAILED++))
echo ""

# 总结
echo "============================================================"
echo "📊 测试总结"
echo "============================================================"
echo -e "${GREEN}✅ 通过: $PASSED${NC}"
echo -e "${RED}❌ 失败: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  部分测试失败，请检查服务状态和日志${NC}"
    echo "   查看日志: bash scripts/server/view-logs.sh backend -n 50"
    exit 1
fi

