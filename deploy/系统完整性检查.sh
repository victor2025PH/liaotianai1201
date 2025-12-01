#!/bin/bash
# 系統完整性檢查腳本

set -e

echo "========================================="
echo "系統完整性檢查"
echo "========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# 1. 檢查後端服務
echo -e "${BLUE}【1】檢查後端服務...${NC}"
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")

if [ "$BACKEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ 後端服務運行正常 (HTTP $BACKEND_STATUS)${NC}"
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health 2>/dev/null)
    echo "  響應: $HEALTH_RESPONSE"
else
    echo -e "${RED}✗ 後端服務異常 (HTTP $BACKEND_STATUS)${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 2. 檢查前端服務
echo -e "${BLUE}【2】檢查前端服務...${NC}"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")

if [ "$FRONTEND_STATUS" = "200" ] || [ "$FRONTEND_STATUS" = "304" ]; then
    echo -e "${GREEN}✓ 前端服務運行正常 (HTTP $FRONTEND_STATUS)${NC}"
else
    echo -e "${YELLOW}⚠ 前端服務異常 (HTTP $FRONTEND_STATUS)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 3. 檢查數據庫連接
echo -e "${BLUE}【3】檢查數據庫連接...${NC}"
cd ~/liaotian/admin-backend

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    
    if python3 -c "from app.db import SessionLocal; db = SessionLocal(); print('✓ 數據庫連接成功'); db.close()" 2>&1; then
        echo -e "${GREEN}✓ 數據庫連接正常${NC}"
    else
        echo -e "${RED}✗ 數據庫連接失敗${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}⚠ 虛擬環境不存在${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 4. 檢查關鍵 API 端點
echo -e "${BLUE}【4】檢查關鍵 API 端點...${NC}"

# 4.1 API 文檔
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null || echo "000")
if [ "$DOCS_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ API 文檔可訪問${NC}"
else
    echo -e "${YELLOW}⚠ API 文檔不可訪問 (HTTP $DOCS_STATUS)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# 4.2 劇本列表 API
SCRIPTS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/group-ai/scripts/ 2>/dev/null || echo "000")
if [ "$SCRIPTS_STATUS" = "200" ] || [ "$SCRIPTS_STATUS" = "401" ]; then
    echo -e "${GREEN}✓ 劇本列表 API 響應正常 (HTTP $SCRIPTS_STATUS)${NC}"
else
    echo -e "${YELLOW}⚠ 劇本列表 API 異常 (HTTP $SCRIPTS_STATUS)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# 4.3 Worker API
WORKERS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/workers 2>/dev/null || echo "000")
if [ "$WORKERS_STATUS" = "200" ] || [ "$WORKERS_STATUS" = "401" ]; then
    echo -e "${GREEN}✓ Worker API 響應正常 (HTTP $WORKERS_STATUS)${NC}"
else
    echo -e "${YELLOW}⚠ Worker API 異常 (HTTP $WORKERS_STATUS)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 5. 檢查服務進程
echo -e "${BLUE}【5】檢查服務進程...${NC}"
UVICORN_COUNT=$(ps aux | grep uvicorn | grep -v grep | wc -l)
NEXT_COUNT=$(ps aux | grep next | grep -v grep | wc -l)

if [ "$UVICORN_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ 後端進程運行中 (數量: $UVICORN_COUNT)${NC}"
    if [ "$UVICORN_COUNT" -gt 1 ]; then
        echo -e "${YELLOW}⚠ 發現多個後端進程，建議清理${NC}"
        ps aux | grep uvicorn | grep -v grep
    fi
else
    echo -e "${RED}✗ 後端進程未運行${NC}"
    ERRORS=$((ERRORS + 1))
fi

if [ "$NEXT_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ 前端進程運行中 (數量: $NEXT_COUNT)${NC}"
else
    echo -e "${YELLOW}⚠ 前端進程未運行${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 6. 檢查端口占用
echo -e "${BLUE}【6】檢查端口占用...${NC}"
PORT_8000=$(lsof -ti:8000 2>/dev/null | wc -l)
PORT_3000=$(lsof -ti:3000 2>/dev/null | wc -l)

if [ "$PORT_8000" -gt 0 ]; then
    echo -e "${GREEN}✓ 端口 8000 已被占用 (後端服務)${NC}"
else
    echo -e "${RED}✗ 端口 8000 未被占用${NC}"
    ERRORS=$((ERRORS + 1))
fi

if [ "$PORT_3000" -gt 0 ]; then
    echo -e "${GREEN}✓ 端口 3000 已被占用 (前端服務)${NC}"
else
    echo -e "${YELLOW}⚠ 端口 3000 未被占用${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 7. 檢查關鍵文件
echo -e "${BLUE}【7】檢查關鍵文件...${NC}"
cd ~/liaotian

MISSING_FILES=()
REQUIRED_FILES=(
    "admin-backend/app/main.py"
    "admin-backend/app/api/__init__.py"
    "admin-backend/app/api/group_ai/__init__.py"
    "admin-backend/app/db.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ 所有關鍵文件存在${NC}"
else
    echo -e "${RED}✗ 缺少以下文件:${NC}"
    printf '%s\n' "${MISSING_FILES[@]}"
    ERRORS=$((ERRORS + ${#MISSING_FILES[@]}))
fi
echo ""

# 8. 檢查環境變量
echo -e "${BLUE}【8】檢查環境變量配置...${NC}"
cd ~/liaotian/admin-backend

if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env 文件存在${NC}"
    
    # 檢查關鍵變量
    if grep -q "JWT_SECRET=" .env && ! grep -q "JWT_SECRET=change_me" .env; then
        echo -e "${GREEN}✓ JWT_SECRET 已配置${NC}"
    else
        echo -e "${YELLOW}⚠ JWT_SECRET 使用默認值，建議修改${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠ .env 文件不存在${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 總結
echo "========================================="
echo -e "${BLUE}【檢查總結】${NC}"
echo "========================================="
echo "錯誤數: $ERRORS"
echo "警告數: $WARNINGS"
echo ""

if [ "$ERRORS" -eq 0 ] && [ "$BACKEND_STATUS" = "200" ]; then
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}✅ 系統完整性檢查通過！${NC}"
    echo -e "${GREEN}=========================================${NC}"
    
    if [ "$WARNINGS" -gt 0 ]; then
        echo -e "${YELLOW}⚠ 有 $WARNINGS 個警告，建議處理${NC}"
    fi
    
    exit 0
else
    echo -e "${RED}=========================================${NC}"
    echo -e "${RED}✗ 發現 $ERRORS 個錯誤${NC}"
    echo -e "${RED}=========================================${NC}"
    
    if [ "$WARNINGS" -gt 0 ]; then
        echo -e "${YELLOW}⚠ 還有 $WARNINGS 個警告${NC}"
    fi
    
    exit 1
fi
