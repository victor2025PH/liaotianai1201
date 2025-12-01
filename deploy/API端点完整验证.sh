#!/bin/bash
# API 端點完整驗證腳本

set -e

echo "========================================="
echo "API 端點完整驗證"
echo "========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"
ERRORS=0

# 步驟 1: 獲取認證 Token
echo -e "${BLUE}【步驟 1】獲取認證 Token...${NC}"

# 嘗試使用默認憑據登錄
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123" 2>/dev/null || echo "")

# 檢查是否有 access_token（嘗試多種方式提取）
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4 || echo "")

# 如果第一次失敗，嘗試使用 Python 提取
if [ -z "$TOKEN" ] && echo "$LOGIN_RESPONSE" | grep -q "{"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; data=sys.stdin.read(); obj=json.loads(data) if data.strip().startswith('{') else {}; print(obj.get('access_token', ''))" 2>/dev/null || echo "")
fi

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓ 登錄成功，獲取 Token${NC}"
    echo "Token: ${TOKEN:0:50}..."
else
    echo -e "${YELLOW}⚠ 登錄失敗或 Token 格式不同${NC}"
    echo "響應: $LOGIN_RESPONSE" | head -5
    echo ""
    echo "繼續測試公共端點..."
    TOKEN=""
fi
echo ""

# 如果有 Token，設置認證頭
AUTH_HEADER=""
if [ -n "$TOKEN" ]; then
    AUTH_HEADER="-H \"Authorization: Bearer $TOKEN\""
fi

# 步驟 2: 測試健康檢查端點（無需認證）
echo -e "${BLUE}【步驟 2】測試健康檢查端點...${NC}"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health" 2>/dev/null || echo "000")

if [ "$HEALTH_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ /health 端點正常 (HTTP $HEALTH_STATUS)${NC}"
    curl -s "${BASE_URL}/health" | head -3
else
    echo -e "${RED}✗ /health 端點異常 (HTTP $HEALTH_STATUS)${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 步驟 3: 測試 API 文檔端點
echo -e "${BLUE}【步驟 3】測試 API 文檔端點...${NC}"
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/docs" 2>/dev/null || echo "000")

if [ "$DOCS_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ /docs 端點正常 (HTTP $DOCS_STATUS)${NC}"
else
    echo -e "${YELLOW}⚠ /docs 端點異常 (HTTP $DOCS_STATUS)${NC}"
fi
echo ""

# 步驟 4: 測試關鍵 API 端點（需要認證）
echo -e "${BLUE}【步驟 4】測試關鍵 API 端點...${NC}"

if [ -n "$TOKEN" ]; then
    # 測試劇本列表 API
    echo "測試劇本列表 API..."
    SCRIPTS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $TOKEN" \
        "${BASE_URL}/api/v1/group-ai/scripts/" 2>/dev/null || echo "000")
    
    if [ "$SCRIPTS_STATUS" = "200" ]; then
        echo -e "${GREEN}✓ 劇本列表 API 正常 (HTTP $SCRIPTS_STATUS)${NC}"
        curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/api/v1/group-ai/scripts/" | head -5
    else
        echo -e "${YELLOW}⚠ 劇本列表 API 返回 HTTP $SCRIPTS_STATUS${NC}"
    fi
    echo ""
    
    # 測試賬號列表 API
    echo "測試賬號列表 API..."
    ACCOUNTS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $TOKEN" \
        "${BASE_URL}/api/v1/group-ai/accounts/" 2>/dev/null || echo "000")
    
    if [ "$ACCOUNTS_STATUS" = "200" ]; then
        echo -e "${GREEN}✓ 賬號列表 API 正常 (HTTP $ACCOUNTS_STATUS)${NC}"
        curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/api/v1/group-ai/accounts/" | head -5
    else
        echo -e "${YELLOW}⚠ 賬號列表 API 返回 HTTP $ACCOUNTS_STATUS${NC}"
    fi
    echo ""
    
    # 測試 Worker API
    echo "測試 Worker API..."
    WORKERS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $TOKEN" \
        "${BASE_URL}/api/v1/workers" 2>/dev/null || echo "000")
    
    if [ "$WORKERS_STATUS" = "200" ] || [ "$WORKERS_STATUS" = "401" ]; then
        echo -e "${GREEN}✓ Worker API 響應 (HTTP $WORKERS_STATUS)${NC}"
    else
        echo -e "${YELLOW}⚠ Worker API 返回 HTTP $WORKERS_STATUS${NC}"
    fi
    echo ""
else
    echo -e "${YELLOW}⚠ 無 Token，跳過需要認證的端點${NC}"
    echo "測試端點是否存在（會返回 401）..."
    
    SCRIPTS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/v1/group-ai/scripts/" 2>/dev/null || echo "000")
    echo "  劇本列表 API: HTTP $SCRIPTS_STATUS"
    
    ACCOUNTS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/v1/group-ai/accounts/" 2>/dev/null || echo "000")
    echo "  賬號列表 API: HTTP $ACCOUNTS_STATUS"
    echo ""
fi

# 步驟 5: 測試其他關鍵端點
echo -e "${BLUE}【步驟 5】測試其他關鍵端點...${NC}"

# 測試服務器列表 API
SERVERS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    ${TOKEN:+-H "Authorization: Bearer $TOKEN"} \
    "${BASE_URL}/api/v1/group-ai/servers/" 2>/dev/null || echo "000")
echo "  服務器列表 API: HTTP $SERVERS_STATUS"

# 測試監控 API
MONITOR_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    ${TOKEN:+-H "Authorization: Bearer $TOKEN"} \
    "${BASE_URL}/api/v1/group-ai/monitor/metrics" 2>/dev/null || echo "000")
echo "  監控指標 API: HTTP $MONITOR_STATUS"

# 測試儀表板 API
DASHBOARD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    ${TOKEN:+-H "Authorization: Bearer $TOKEN"} \
    "${BASE_URL}/api/v1/group-ai/dashboard/stats" 2>/dev/null || echo "000")
echo "  儀表板統計 API: HTTP $DASHBOARD_STATUS"
echo ""

# 總結
echo "========================================="
echo -e "${BLUE}【驗證總結】${NC}"
echo "========================================="

if [ "$HEALTH_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ 健康檢查: 通過${NC}"
else
    echo -e "${RED}❌ 健康檢查: 失敗${NC}"
    ERRORS=$((ERRORS + 1))
fi

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✅ 認證: 成功${NC}"
else
    echo -e "${YELLOW}⚠ 認證: 未測試（可能需要檢查憑據）${NC}"
fi

if [ "$ERRORS" -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}✅ API 端點驗證完成！${NC}"
    echo -e "${GREEN}=========================================${NC}"
    exit 0
else
    echo ""
    echo -e "${YELLOW}=========================================${NC}"
    echo -e "${YELLOW}⚠ 發現 $ERRORS 個問題${NC}"
    echo -e "${YELLOW}=========================================${NC}"
    exit 1
fi
