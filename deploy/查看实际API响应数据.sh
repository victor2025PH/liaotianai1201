#!/bin/bash
# 查看實際 API 響應數據

set -e

echo "========================================="
echo "查看實際 API 響應數據"
echo "========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"

# 步驟 1: 獲取 Token
echo -e "${BLUE}【步驟 1】獲取認證 Token...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; d=sys.stdin.read(); j=json.loads(d) if d.strip().startswith('{') else {}; print(j.get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Token 獲取失敗"
    echo "響應: $LOGIN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Token 獲取成功${NC}"
echo ""

# 步驟 2: 查看劇本列表
echo -e "${BLUE}【步驟 2】劇本列表 API 響應...${NC}"
echo "端點: GET /api/v1/group-ai/scripts/?limit=3"
echo "響應:"
curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/api/v1/group-ai/scripts/?limit=3" | \
python3 -m json.tool 2>/dev/null | head -50 || \
curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/api/v1/group-ai/scripts/?limit=3" | head -20
echo ""
echo ""

# 步驟 3: 查看賬號列表
echo -e "${BLUE}【步驟 3】賬號列表 API 響應...${NC}"
echo "端點: GET /api/v1/group-ai/accounts/?limit=3"
echo "響應:"
curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/api/v1/group-ai/accounts/?limit=3" | \
python3 -m json.tool 2>/dev/null | head -50 || \
curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/api/v1/group-ai/accounts/?limit=3" | head -20
echo ""
echo ""

# 步驟 4: 查看服務器列表
echo -e "${BLUE}【步驟 4】服務器列表 API 響應...${NC}"
echo "端點: GET /api/v1/group-ai/servers/"
echo "響應:"
curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/api/v1/group-ai/servers/" | \
python3 -m json.tool 2>/dev/null | head -50 || \
curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/api/v1/group-ai/servers/" | head -20
echo ""
echo ""

# 步驟 5: 查看 Worker 列表（修正路徑）
echo -e "${BLUE}【步驟 5】Worker 列表 API 響應（修正路徑）...${NC}"
echo "端點: GET /api/v1/workers/"
echo "響應:"
curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/api/v1/workers/" | \
python3 -m json.tool 2>/dev/null | head -50 || \
curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/api/v1/workers/" | head -20
echo ""
echo ""

# 步驟 6: 查看儀表板統計（修正路徑）
echo -e "${BLUE}【步驟 6】儀表板統計 API 響應（修正路徑）...${NC}"
echo "端點: GET /api/v1/group-ai/dashboard/"
echo "響應:"
curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/api/v1/group-ai/dashboard/" | \
python3 -m json.tool 2>/dev/null | head -50 || \
curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/api/v1/group-ai/dashboard/" | head -20
echo ""
echo ""

echo "========================================="
echo -e "${GREEN}✅ API 響應數據查看完成${NC}"
echo "========================================="
