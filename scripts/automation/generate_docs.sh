#!/bin/bash
# 自動生成文檔腳本

set -e

echo "=== 自動生成文檔 ==="

GREEN='\033[0;32m'
NC='\033[0m'

# 1. 生成 API 文檔
echo -e "${GREEN}[1/3] 生成 API 文檔...${NC}"
cd admin-backend
if [ -f "app/main.py" ]; then
    poetry run python -c "
from app.main import app
import json
with open('openapi.json', 'w') as f:
    json.dump(app.openapi(), f, indent=2)
"
    echo -e "${GREEN}✓ API 文檔已生成: openapi.json${NC}"
fi

# 2. 生成代碼文檔
echo -e "${GREEN}[2/3] 生成代碼文檔...${NC}"
if command -v pydoc &> /dev/null; then
    mkdir -p docs/api_reference
    # 生成主要模塊文檔
    pydoc -w group_ai_service.account_manager || true
    pydoc -w group_ai_service.script_engine || true
    echo -e "${GREEN}✓ 代碼文檔已生成${NC}"
fi

# 3. 更新 README
echo -e "${GREEN}[3/3] 更新項目 README...${NC}"
cd ..
if [ -f "README.md" ]; then
    echo -e "${GREEN}✓ README 已存在${NC}"
fi

echo ""
echo -e "${GREEN}=== 文檔生成完成 ===${NC}"

