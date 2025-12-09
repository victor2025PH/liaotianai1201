#!/bin/bash
# 輕量級部署驗證腳本（避免內存問題）

set -e

echo "=========================================="
echo "輕量級部署驗證"
echo "=========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 檢查 PM2 服務（最簡單的檢查）
echo "1. 檢查 PM2 服務狀態"
echo "----------------------------------------"
if command -v pm2 >/dev/null 2>&1; then
    pm2 list 2>/dev/null | head -n 5 || echo "PM2 未運行或無進程"
else
    echo -e "${RED}✗ PM2 未安裝${NC}"
fi
echo ""

# 2. 檢查端口（輕量級）
echo "2. 檢查端口監聽"
echo "----------------------------------------"
if command -v ss >/dev/null 2>&1; then
    if ss -tln 2>/dev/null | grep -q ":8000"; then
        echo -e "${GREEN}✓ 端口 8000 (後端) 正在監聽${NC}"
    else
        echo -e "${RED}✗ 端口 8000 (後端) 未監聽${NC}"
    fi
    
    if ss -tln 2>/dev/null | grep -q ":3000"; then
        echo -e "${GREEN}✓ 端口 3000 (前端) 正在監聽${NC}"
    else
        echo -e "${RED}✗ 端口 3000 (前端) 未監聽${NC}"
    fi
else
    echo "ss 命令不可用，跳過端口檢查"
fi
echo ""

# 3. 簡單健康檢查（避免複雜的 JSON 解析）
echo "3. 檢查服務健康狀態"
echo "----------------------------------------"

# 後端健康檢查
echo -n "後端健康檢查: "
BACKEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ 正常 (HTTP 200)${NC}"
else
    echo -e "${RED}✗ 異常 (HTTP $BACKEND_RESPONSE)${NC}"
fi

# 前端健康檢查
echo -n "前端響應: "
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_RESPONSE" = "200" ] || [ "$FRONTEND_RESPONSE" = "301" ] || [ "$FRONTEND_RESPONSE" = "302" ]; then
    echo -e "${GREEN}✓ 正常 (HTTP $FRONTEND_RESPONSE)${NC}"
else
    echo -e "${RED}✗ 異常 (HTTP $FRONTEND_RESPONSE)${NC}"
fi
echo ""

# 4. 檢查環境變量（只檢查關鍵項，不讀取整個文件）
echo "4. 檢查關鍵環境變量"
echo "----------------------------------------"
cd /home/ubuntu/telegram-ai-system/admin-backend 2>/dev/null || cd admin-backend 2>/dev/null || { echo "無法找到 admin-backend 目錄"; exit 1; }

if [ -f ".env" ]; then
    # 只檢查關鍵變量，避免讀取整個文件
    JWT_SECRET=$(grep "^JWT_SECRET=" .env 2>/dev/null | cut -d'=' -f2- | head -c 50 || echo "")
    ADMIN_PASSWORD=$(grep "^ADMIN_DEFAULT_PASSWORD=" .env 2>/dev/null | cut -d'=' -f2- | head -c 50 || echo "")
    
    if [ -z "$JWT_SECRET" ] || [ "$JWT_SECRET" = "change_me" ]; then
        echo -e "${RED}⚠️  JWT_SECRET 使用默認值或為空${NC}"
    else
        echo -e "${GREEN}✓ JWT_SECRET 已配置${NC}"
    fi
    
    if [ -z "$ADMIN_PASSWORD" ] || [ "$ADMIN_PASSWORD" = "changeme123" ]; then
        echo -e "${RED}⚠️  ADMIN_DEFAULT_PASSWORD 使用默認值或為空${NC}"
    else
        echo -e "${GREEN}✓ ADMIN_DEFAULT_PASSWORD 已配置${NC}"
    fi
else
    echo -e "${RED}✗ .env 文件不存在${NC}"
fi
echo ""

# 5. 檢查 Nginx（簡單檢查）
echo "5. 檢查 Nginx 狀態"
echo "----------------------------------------"
if systemctl is-active --quiet nginx 2>/dev/null; then
    echo -e "${GREEN}✓ Nginx 服務運行中${NC}"
else
    echo -e "${YELLOW}⚠️  Nginx 服務未運行或無法檢查${NC}"
fi
echo ""

# 6. 檢查磁盤空間（簡單）
echo "6. 檢查磁盤空間"
echo "----------------------------------------"
df -h / 2>/dev/null | tail -n 1 | awk '{print "使用率: " $5 ", 可用: " $4}'
echo ""

echo "=========================================="
echo "驗證完成"
echo "=========================================="
echo ""
echo "如果發現問題，請："
echo "1. 查看 PM2 日誌: pm2 logs --lines 20"
echo "2. 檢查服務狀態: pm2 status"
echo "3. 重啟服務: pm2 restart all"
echo ""

