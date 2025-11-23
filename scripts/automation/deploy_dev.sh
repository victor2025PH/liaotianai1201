#!/bin/bash
# 開發環境自動部署腳本

set -e

echo "=== 開發環境自動部署 ==="

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ENV=${1:-dev}

echo -e "${GREEN}部署環境: ${ENV}${NC}"

# 1. 檢查環境
echo -e "${GREEN}[1/5] 檢查環境...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker 未安裝${NC}"
    exit 1
fi

# 2. 構建 Docker 鏡像
echo -e "${GREEN}[2/5] 構建 Docker 鏡像...${NC}"
docker build -t group-ai/backend:dev -f admin-backend/Dockerfile admin-backend/
docker build -t group-ai/frontend:dev -f saas-demo/Dockerfile saas-demo/

# 3. 運行數據庫遷移
echo -e "${GREEN}[3/5] 運行數據庫遷移...${NC}"
cd admin-backend
poetry run alembic upgrade head || echo -e "${YELLOW}⚠ 遷移失敗或無需遷移${NC}"

# 4. 啟動服務
echo -e "${GREEN}[4/5] 啟動服務...${NC}"
cd ..
if [ -f "deploy/docker-compose.dev.yml" ]; then
    docker compose -f deploy/docker-compose.dev.yml up -d
else
    echo -e "${YELLOW}⚠ docker-compose.dev.yml 不存在，跳過容器部署${NC}"
fi

# 5. 健康檢查
echo -e "${GREEN}[5/5] 健康檢查...${NC}"
sleep 5
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 後端服務健康${NC}"
else
    echo -e "${YELLOW}⚠ 後端服務未響應${NC}"
fi

echo ""
echo -e "${GREEN}=== 部署完成 ===${NC}"

