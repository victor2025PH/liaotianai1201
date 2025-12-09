#!/bin/bash
# 部署驗證腳本
# 用於驗證系統在服務器上是否正常運行

set -e

echo "=========================================="
echo "部署驗證腳本"
echo "=========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查函數
check_service() {
    local service_name=$1
    local check_command=$2
    
    echo -n "檢查 $service_name... "
    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 正常${NC}"
        return 0
    else
        echo -e "${RED}✗ 異常${NC}"
        return 1
    fi
}

# 1. 檢查 PM2 服務
echo "1. 檢查 PM2 服務狀態"
echo "----------------------------------------"
pm2 status
echo ""

# 檢查後端服務
if pm2 list | grep -q "backend.*online"; then
    echo -e "${GREEN}✓ 後端服務運行中${NC}"
else
    echo -e "${RED}✗ 後端服務未運行${NC}"
fi

# 檢查前端服務
if pm2 list | grep -q "frontend.*online"; then
    echo -e "${GREEN}✓ 前端服務運行中${NC}"
else
    echo -e "${RED}✗ 前端服務未運行${NC}"
fi
echo ""

# 2. 檢查端口監聽
echo "2. 檢查端口監聽狀態"
echo "----------------------------------------"
if ss -tlnp | grep -q ":8000"; then
    echo -e "${GREEN}✓ 端口 8000 (後端) 正在監聽${NC}"
    ss -tlnp | grep ":8000"
else
    echo -e "${RED}✗ 端口 8000 (後端) 未監聽${NC}"
fi
echo ""

if ss -tlnp | grep -q ":3000"; then
    echo -e "${GREEN}✓ 端口 3000 (前端) 正在監聽${NC}"
    ss -tlnp | grep ":3000"
else
    echo -e "${RED}✗ 端口 3000 (前端) 未監聽${NC}"
fi
echo ""

# 3. 檢查健康狀態
echo "3. 檢查服務健康狀態"
echo "----------------------------------------"

# 後端健康檢查
echo "後端健康檢查:"
BACKEND_HEALTH=$(curl -s http://localhost:8000/health || echo "FAILED")
if [ "$BACKEND_HEALTH" != "FAILED" ]; then
    echo -e "${GREEN}✓ 後端健康檢查通過${NC}"
    echo "$BACKEND_HEALTH" | head -n 5
else
    echo -e "${RED}✗ 後端健康檢查失敗${NC}"
fi
echo ""

# 詳細健康檢查
echo "詳細健康檢查:"
DETAILED_HEALTH=$(curl -s "http://localhost:8000/health?detailed=true" || echo "FAILED")
if [ "$DETAILED_HEALTH" != "FAILED" ]; then
    echo -e "${GREEN}✓ 詳細健康檢查可用${NC}"
    echo "$DETAILED_HEALTH" | python3 -m json.tool 2>/dev/null | head -n 20 || echo "$DETAILED_HEALTH" | head -n 20
else
    echo -e "${RED}✗ 詳細健康檢查失敗${NC}"
fi
echo ""

# 前端健康檢查
echo "前端健康檢查:"
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "000")
if [ "$FRONTEND_HEALTH" = "200" ] || [ "$FRONTEND_HEALTH" = "301" ] || [ "$FRONTEND_HEALTH" = "302" ]; then
    echo -e "${GREEN}✓ 前端響應正常 (HTTP $FRONTEND_HEALTH)${NC}"
else
    echo -e "${RED}✗ 前端響應異常 (HTTP $FRONTEND_HEALTH)${NC}"
fi
echo ""

# 4. 檢查環境變量（安全）
echo "4. 檢查關鍵環境變量配置"
echo "----------------------------------------"
cd /home/ubuntu/telegram-ai-system/admin-backend 2>/dev/null || cd admin-backend 2>/dev/null || { echo "無法找到項目目錄"; exit 1; }

if [ -f ".env" ]; then
    JWT_SECRET=$(grep "^JWT_SECRET=" .env | cut -d'=' -f2 | tr -d '"' || echo "")
    ADMIN_PASSWORD=$(grep "^ADMIN_DEFAULT_PASSWORD=" .env | cut -d'=' -f2 | tr -d '"' || echo "")
    CORS_ORIGINS=$(grep "^CORS_ORIGINS=" .env | cut -d'=' -f2 | tr -d '"' || echo "")
    
    if [ "$JWT_SECRET" = "change_me" ] || [ -z "$JWT_SECRET" ]; then
        echo -e "${RED}⚠️  JWT_SECRET 使用默認值或為空，必須修改！${NC}"
    else
        echo -e "${GREEN}✓ JWT_SECRET 已配置${NC}"
    fi
    
    if [ "$ADMIN_PASSWORD" = "changeme123" ] || [ -z "$ADMIN_PASSWORD" ]; then
        echo -e "${RED}⚠️  ADMIN_DEFAULT_PASSWORD 使用默認值或為空，必須修改！${NC}"
    else
        echo -e "${GREEN}✓ ADMIN_DEFAULT_PASSWORD 已配置${NC}"
    fi
    
    if [ -z "$CORS_ORIGINS" ]; then
        echo -e "${YELLOW}⚠️  CORS_ORIGINS 未配置${NC}"
    else
        echo -e "${GREEN}✓ CORS_ORIGINS 已配置: ${CORS_ORIGINS:0:50}...${NC}"
    fi
else
    echo -e "${RED}✗ .env 文件不存在${NC}"
fi
echo ""

# 5. 檢查 Nginx 狀態
echo "5. 檢查 Nginx 狀態"
echo "----------------------------------------"
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx 服務運行中${NC}"
    
    # 檢查 Nginx 配置
    if sudo nginx -t 2>&1 | grep -q "syntax is ok"; then
        echo -e "${GREEN}✓ Nginx 配置語法正確${NC}"
    else
        echo -e "${RED}✗ Nginx 配置語法錯誤${NC}"
        sudo nginx -t
    fi
else
    echo -e "${RED}✗ Nginx 服務未運行${NC}"
fi
echo ""

# 6. 檢查磁盤空間
echo "6. 檢查磁盤空間"
echo "----------------------------------------"
df -h / | tail -n 1
echo ""

# 7. 檢查最近日誌錯誤
echo "7. 檢查最近日誌錯誤（最後20行）"
echo "----------------------------------------"
echo "後端錯誤日誌:"
pm2 logs backend --lines 20 --nostream --err 2>/dev/null | tail -n 10 || echo "無法讀取後端錯誤日誌"
echo ""

echo "前端錯誤日誌:"
pm2 logs frontend --lines 20 --nostream --err 2>/dev/null | tail -n 10 || echo "無法讀取前端錯誤日誌"
echo ""

# 8. 檢查緩存統計（如果可用）
echo "8. 檢查緩存統計"
echo "----------------------------------------"
CACHE_STATS=$(curl -s http://localhost:8000/api/v1/system/performance/cache/stats 2>/dev/null || echo "FAILED")
if [ "$CACHE_STATS" != "FAILED" ]; then
    echo -e "${GREEN}✓ 緩存統計可用${NC}"
    echo "$CACHE_STATS" | python3 -m json.tool 2>/dev/null | head -n 15 || echo "$CACHE_STATS" | head -n 15
else
    echo -e "${YELLOW}⚠️  緩存統計不可用（可能需要認證）${NC}"
fi
echo ""

# 總結
echo "=========================================="
echo "驗證完成"
echo "=========================================="
echo ""
echo "如果發現問題，請："
echo "1. 查看 PM2 日誌: pm2 logs"
echo "2. 查看 Nginx 日誌: sudo tail -f /var/log/nginx/error.log"
echo "3. 檢查服務狀態: pm2 status"
echo "4. 重啟服務: pm2 restart all"
echo ""

