#!/bin/bash
# 代碼質量自動檢查腳本

set -e

echo "=== 代碼質量檢查 ==="

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Python 代碼檢查
echo -e "${GREEN}[1/3] Python 代碼檢查...${NC}"
cd admin-backend

# Ruff 檢查
if poetry run ruff check group_ai_service/ app/api/group_ai/; then
    echo -e "${GREEN}✓ Ruff 檢查通過${NC}"
else
    echo -e "${RED}✗ Ruff 檢查失敗${NC}"
    exit 1
fi

# Black 格式化檢查
if poetry run black --check group_ai_service/ app/api/group_ai/; then
    echo -e "${GREEN}✓ Black 格式化檢查通過${NC}"
else
    echo -e "${YELLOW}⚠ 代碼格式不符合規範，運行 'black group_ai_service/ app/api/group_ai/' 修復${NC}"
fi

# MyPy 類型檢查
if poetry run mypy group_ai_service/ --ignore-missing-imports; then
    echo -e "${GREEN}✓ MyPy 類型檢查通過${NC}"
else
    echo -e "${YELLOW}⚠ MyPy 類型檢查有警告${NC}"
fi

# TypeScript 代碼檢查
echo -e "${GREEN}[2/3] TypeScript 代碼檢查...${NC}"
cd ../saas-demo
if npm run lint; then
    echo -e "${GREEN}✓ ESLint 檢查通過${NC}"
else
    echo -e "${RED}✗ ESLint 檢查失敗${NC}"
    exit 1
fi

# 文檔檢查
echo -e "${GREEN}[3/3] 文檔檢查...${NC}"
cd ..
if [ -f "docs/GROUP_AI_DEVELOPMENT_PLAN.md" ]; then
    echo -e "${GREEN}✓ 開發計劃文檔存在${NC}"
else
    echo -e "${YELLOW}⚠ 開發計劃文檔缺失${NC}"
fi

echo ""
echo -e "${GREEN}=== 代碼質量檢查完成 ===${NC}"

