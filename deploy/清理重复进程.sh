#!/bin/bash
# 清理重複進程腳本

set -e

echo "========================================="
echo "清理重複進程"
echo "========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. 檢查當前進程
echo -e "${BLUE}【1】檢查當前 uvicorn 進程...${NC}"
UVICORN_PROCESSES=$(ps aux | grep 'uvicorn.*app.main:app' | grep -v grep)

if [ -z "$UVICORN_PROCESSES" ]; then
    echo -e "${YELLOW}⚠ 未找到 uvicorn 進程${NC}"
    exit 0
fi

PROCESS_COUNT=$(echo "$UVICORN_PROCESSES" | wc -l)
echo "找到 $PROCESS_COUNT 個 uvicorn 進程："
echo "$UVICORN_PROCESSES"
echo ""

if [ "$PROCESS_COUNT" -le 1 ]; then
    echo -e "${GREEN}✓ 只有一個進程，無需清理${NC}"
    exit 0
fi

# 2. 確認操作
echo -e "${YELLOW}⚠ 發現多個進程，將停止所有進程並重新啟動單個服務${NC}"
echo ""

# 3. 停止所有進程
echo -e "${BLUE}【2】停止所有 uvicorn 進程...${NC}"
pkill -9 -f 'uvicorn.*app.main:app' || true
sleep 2

# 驗證進程已停止
REMAINING=$(ps aux | grep 'uvicorn.*app.main:app' | grep -v grep | wc -l)
if [ "$REMAINING" -eq 0 ]; then
    echo -e "${GREEN}✓ 所有進程已停止${NC}"
else
    echo -e "${RED}✗ 仍有 $REMAINING 個進程未停止${NC}"
    echo "剩餘進程："
    ps aux | grep 'uvicorn.*app.main:app' | grep -v grep
    exit 1
fi
echo ""

# 4. 啟動單個服務
echo -e "${BLUE}【3】啟動後端服務...${NC}"
cd ~/liaotian/admin-backend

if [ ! -f ".venv/bin/activate" ]; then
    echo -e "${RED}✗ 虛擬環境不存在${NC}"
    exit 1
fi

source .venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
NEW_PID=$!

echo "新進程 PID: $NEW_PID"
sleep 5
echo ""

# 5. 驗證服務
echo -e "${BLUE}【4】驗證服務狀態...${NC}"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")

if [ "$HEALTH" = "200" ]; then
    echo -e "${GREEN}✓ 服務啟動成功${NC}"
    curl -s http://localhost:8000/health
    echo ""
    
    # 檢查進程數
    FINAL_COUNT=$(ps aux | grep 'uvicorn.*app.main:app' | grep -v grep | wc -l)
    echo "當前進程數: $FINAL_COUNT"
    
    if [ "$FINAL_COUNT" -eq 1 ]; then
        echo -e "${GREEN}✓ 清理完成，只有一個進程運行${NC}"
    else
        echo -e "${YELLOW}⚠ 仍有 $FINAL_COUNT 個進程${NC}"
    fi
else
    echo -e "${RED}✗ 服務啟動失敗 (HTTP $HEALTH)${NC}"
    echo "最後 30 行日誌："
    tail -30 /tmp/backend.log 2>/dev/null || tail -30 ~/liaotian/logs/backend.log 2>/dev/null || echo "未找到日誌文件"
    exit 1
fi
echo ""

# 總結
echo "========================================="
echo -e "${GREEN}✅ 清理完成！${NC}"
echo "========================================="
echo "進程數: 從 $PROCESS_COUNT 個減少到 $FINAL_COUNT 個"
echo "服務狀態: HTTP $HEALTH"
echo ""
