#!/bin/bash
# 群組 AI 系統自動化測試腳本

set -e

echo "=== 群組 AI 系統自動化測試 ==="

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 單元測試
echo -e "${GREEN}[1/4] 運行單元測試...${NC}"
cd admin-backend
if poetry run pytest group_ai_service/tests/unit/ -v --cov=group_ai_service --cov-report=term-missing; then
    echo -e "${GREEN}✓ 單元測試通過${NC}"
else
    echo -e "${RED}✗ 單元測試失敗${NC}"
    exit 1
fi

# 2. 集成測試
echo -e "${GREEN}[2/4] 運行集成測試...${NC}"
if poetry run pytest group_ai_service/tests/integration/ -v; then
    echo -e "${GREEN}✓ 集成測試通過${NC}"
else
    echo -e "${RED}✗ 集成測試失敗${NC}"
    exit 1
fi

# 3. E2E 測試
echo -e "${GREEN}[3/4] 運行 E2E 測試...${NC}"
if poetry run pytest group_ai_service/tests/e2e/ -v; then
    echo -e "${GREEN}✓ E2E 測試通過${NC}"
else
    echo -e "${YELLOW}⚠ E2E 測試失敗（可能缺少測試環境）${NC}"
fi

# 4. 生成測試報告
echo -e "${GREEN}[4/4] 生成測試報告...${NC}"
poetry run pytest group_ai_service/tests/ -v --cov=group_ai_service --cov-report=html --cov-report=xml
echo -e "${GREEN}✓ 測試報告已生成: htmlcov/index.html${NC}"

echo ""
echo -e "${GREEN}=== 測試完成 ===${NC}"

