#!/bin/bash
# 安全檢查腳本
# 檢查生產環境安全配置

set -e

echo "=========================================="
echo "安全配置檢查"
echo "=========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd /home/ubuntu/telegram-ai-system/admin-backend 2>/dev/null || cd admin-backend 2>/dev/null || { echo "無法找到項目目錄"; exit 1; }

if [ ! -f ".env" ]; then
    echo -e "${RED}✗ .env 文件不存在${NC}"
    exit 1
fi

echo "檢查環境變量配置..."
echo ""

# 讀取環境變量
JWT_SECRET=$(grep "^JWT_SECRET=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "")
ADMIN_PASSWORD=$(grep "^ADMIN_DEFAULT_PASSWORD=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "")
CORS_ORIGINS=$(grep "^CORS_ORIGINS=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "")

# 檢查 JWT_SECRET
echo "1. JWT_SECRET 檢查"
if [ -z "$JWT_SECRET" ]; then
    echo -e "${RED}✗ JWT_SECRET 未設置${NC}"
elif [ "$JWT_SECRET" = "change_me" ]; then
    echo -e "${RED}✗ JWT_SECRET 使用默認值 'change_me'，必須修改！${NC}"
    echo "   建議: 使用強隨機字符串，至少32字符"
elif [ ${#JWT_SECRET} -lt 32 ]; then
    echo -e "${YELLOW}⚠️  JWT_SECRET 長度較短 (${#JWT_SECRET}字符)，建議至少32字符${NC}"
else
    echo -e "${GREEN}✓ JWT_SECRET 已配置 (長度: ${#JWT_SECRET}字符)${NC}"
fi
echo ""

# 檢查 ADMIN_DEFAULT_PASSWORD
echo "2. ADMIN_DEFAULT_PASSWORD 檢查"
if [ -z "$ADMIN_PASSWORD" ]; then
    echo -e "${RED}✗ ADMIN_DEFAULT_PASSWORD 未設置${NC}"
elif [ "$ADMIN_PASSWORD" = "changeme123" ]; then
    echo -e "${RED}✗ ADMIN_DEFAULT_PASSWORD 使用默認值 'changeme123'，必須修改！${NC}"
    echo "   建議: 使用強密碼，至少12字符，包含大小寫字母、數字和特殊字符"
elif [ ${#ADMIN_PASSWORD} -lt 12 ]; then
    echo -e "${YELLOW}⚠️  ADMIN_DEFAULT_PASSWORD 長度較短 (${#ADMIN_PASSWORD}字符)，建議至少12字符${NC}"
else
    echo -e "${GREEN}✓ ADMIN_DEFAULT_PASSWORD 已配置 (長度: ${#ADMIN_PASSWORD}字符)${NC}"
fi
echo ""

# 檢查 CORS_ORIGINS
echo "3. CORS_ORIGINS 檢查"
if [ -z "$CORS_ORIGINS" ]; then
    echo -e "${YELLOW}⚠️  CORS_ORIGINS 未配置，將使用默認值${NC}"
elif echo "$CORS_ORIGINS" | grep -q "localhost"; then
    echo -e "${YELLOW}⚠️  CORS_ORIGINS 包含 localhost，生產環境建議移除${NC}"
    echo "   當前配置: $CORS_ORIGINS"
else
    echo -e "${GREEN}✓ CORS_ORIGINS 已配置${NC}"
    echo "   配置: $CORS_ORIGINS"
fi
echo ""

# 檢查數據庫配置
echo "4. 數據庫配置檢查"
DATABASE_URL=$(grep "^DATABASE_URL=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "")
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠️  DATABASE_URL 未配置${NC}"
elif echo "$DATABASE_URL" | grep -q "sqlite"; then
    echo -e "${GREEN}✓ 使用 SQLite 數據庫${NC}"
    echo "   注意: 生產環境建議使用 PostgreSQL"
elif echo "$DATABASE_URL" | grep -q "postgresql"; then
    echo -e "${GREEN}✓ 使用 PostgreSQL 數據庫${NC}"
else
    echo -e "${YELLOW}⚠️  數據庫配置: $DATABASE_URL${NC}"
fi
echo ""

# 總結
echo "=========================================="
echo "安全檢查總結"
echo "=========================================="

ISSUES=0
if [ "$JWT_SECRET" = "change_me" ] || [ -z "$JWT_SECRET" ]; then
    ISSUES=$((ISSUES + 1))
fi
if [ "$ADMIN_PASSWORD" = "changeme123" ] || [ -z "$ADMIN_PASSWORD" ]; then
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ 所有關鍵安全配置已正確設置${NC}"
else
    echo -e "${RED}✗ 發現 $ISSUES 個安全問題，請立即修復！${NC}"
    echo ""
    echo "修復步驟:"
    echo "1. 編輯 .env 文件: nano admin-backend/.env"
    echo "2. 修改 JWT_SECRET 為強隨機值（至少32字符）"
    echo "3. 修改 ADMIN_DEFAULT_PASSWORD 為強密碼（至少12字符）"
    echo "4. 保存後重啟服務: pm2 restart backend"
fi
echo ""

