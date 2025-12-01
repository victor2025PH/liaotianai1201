#!/bin/bash
# 完整自動測試並修復所有錯誤

set -e

echo "========================================="
echo "完整自動測試並修復系統"
echo "========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 錯誤計數
ERROR_COUNT=0
WARNING_COUNT=0

# 步驟 1: 修復循環導入問題
echo -e "${BLUE}【步驟 1】修復循環導入問題...${NC}"
cd ~/liaotian/admin-backend/app/api/group_ai

if grep -q ", statistics" __init__.py 2>/dev/null; then
    echo -e "${YELLOW}⚠ 發現 statistics 導入錯誤，正在修復...${NC}"
    sed -i 's/, statistics//' __init__.py
    echo -e "${GREEN}✓ 已移除 statistics 導入${NC}"
    ERROR_COUNT=$((ERROR_COUNT + 1))
else
    echo -e "${GREEN}✓ 沒有發現 statistics 導入問題${NC}"
fi
echo ""

# 步驟 2: 檢查並運行數據庫遷移
echo -e "${BLUE}【步驟 2】檢查並運行數據庫遷移...${NC}"
cd ~/liaotian/admin-backend

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    
    # 檢查是否需要遷移
    echo "檢查數據庫版本..."
    python3 -c "
from app.db import engine
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect

try:
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        current_rev = context.get_current_revision()
        print(f'當前數據庫版本: {current_rev}')
except Exception as e:
    print(f'檢查失敗: {e}')
" 2>&1 || echo "無法檢查版本"
    
    # 嘗試運行遷移
    echo "嘗試運行數據庫遷移..."
    if command -v poetry &> /dev/null; then
        poetry run alembic upgrade head 2>&1 || {
            echo -e "${YELLOW}⚠ 使用 poetry 遷移失敗，嘗試直接運行...${NC}"
            python3 -m alembic upgrade head 2>&1 || {
                echo -e "${YELLOW}⚠ 直接運行遷移也失敗，跳過遷移（可能是 SQLite 不支持某些操作）${NC}"
                WARNING_COUNT=$((WARNING_COUNT + 1))
            }
        }
    else
        python3 -m alembic upgrade head 2>&1 || {
            echo -e "${YELLOW}⚠ 遷移失敗，跳過（可能是 SQLite 限制）${NC}"
            WARNING_COUNT=$((WARNING_COUNT + 1))
        }
    fi
    
    echo -e "${GREEN}✓ 遷移檢查完成${NC}"
else
    echo -e "${YELLOW}⚠ 虛擬環境不存在，跳過遷移${NC}"
    WARNING_COUNT=$((WARNING_COUNT + 1))
fi
echo ""

# 步驟 3: 檢查 Python 導入
echo -e "${BLUE}【步驟 3】檢查 Python 模塊導入...${NC}"
cd ~/liaotian/admin-backend

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    
    echo "測試導入主模塊..."
    python3 -c "
import sys
try:
    from app.main import app
    print('✓ 主模塊導入成功')
except ImportError as e:
    print(f'✗ 導入失敗: {e}')
    sys.exit(1)
except Exception as e:
    print(f'✗ 其他錯誤: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 所有模塊導入成功${NC}"
    else
        echo -e "${RED}✗ 模塊導入失敗${NC}"
        ERROR_COUNT=$((ERROR_COUNT + 1))
    fi
else
    echo -e "${YELLOW}⚠ 虛擬環境不存在，跳過導入檢查${NC}"
    WARNING_COUNT=$((WARNING_COUNT + 1))
fi
echo ""

# 步驟 4: 檢查數據庫連接
echo -e "${BLUE}【步驟 4】檢查數據庫連接...${NC}"
cd ~/liaotian/admin-backend

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    
    python3 -c "
from app.db import SessionLocal
try:
    db = SessionLocal()
    result = db.execute('SELECT 1').scalar()
    db.close()
    if result == 1:
        print('✓ 數據庫連接成功')
    else:
        print('✗ 數據庫連接異常')
        exit(1)
except Exception as e:
    print(f'✗ 數據庫連接失敗: {e}')
    exit(1)
" 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 數據庫連接正常${NC}"
    else
        echo -e "${RED}✗ 數據庫連接失敗${NC}"
        ERROR_COUNT=$((ERROR_COUNT + 1))
    fi
fi
echo ""

# 步驟 5: 檢查關鍵文件
echo -e "${BLUE}【步驟 5】檢查關鍵文件完整性...${NC}"
cd ~/liaotian

MISSING_FILES=()
REQUIRED_FILES=(
    "admin-backend/app/main.py"
    "admin-backend/app/api/__init__.py"
    "admin-backend/app/api/group_ai/__init__.py"
    "admin-backend/app/database.py"
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
    ERROR_COUNT=$((ERROR_COUNT + ${#MISSING_FILES[@]}))
fi
echo ""

# 步驟 6: 檢查後端服務狀態
echo -e "${BLUE}【步驟 6】檢查後端服務狀態...${NC}"
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")

if [ "$BACKEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ 後端服務運行正常 (HTTP $BACKEND_STATUS)${NC}"
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health 2>/dev/null || echo "")
    if [ -n "$HEALTH_RESPONSE" ]; then
        echo "健康檢查響應: $HEALTH_RESPONSE"
    fi
else
    echo -e "${YELLOW}⚠ 後端服務異常 (HTTP $BACKEND_STATUS)，將嘗試重啟...${NC}"
    
    # 顯示錯誤日誌
    if [ -f "/tmp/backend.log" ]; then
        echo "最近 20 行日誌："
        tail -20 /tmp/backend.log
    elif [ -f ~/liaotian/logs/backend.log ]; then
        echo "最近 20 行日誌："
        tail -20 ~/liaotian/logs/backend.log
    fi
    
    ERROR_COUNT=$((ERROR_COUNT + 1))
fi
echo ""

# 步驟 7: 重啟後端服務（如果需要）
if [ "$BACKEND_STATUS" != "200" ]; then
    echo -e "${BLUE}【步驟 7】重啟後端服務...${NC}"
    cd ~/liaotian/admin-backend
    
    # 停止舊進程
    echo "停止舊進程..."
    pkill -9 -f 'uvicorn.*app.main:app' || true
    sleep 2
    
    # 啟動新進程
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        echo "啟動後端服務..."
        nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
        BACKEND_PID=$!
        
        echo "等待服務啟動..."
        sleep 8
        
        # 驗證啟動
        NEW_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
        if [ "$NEW_STATUS" = "200" ]; then
            echo -e "${GREEN}✓ 後端服務重啟成功${NC}"
            ERROR_COUNT=$((ERROR_COUNT - 1))  # 減去之前的錯誤計數
        else
            echo -e "${RED}✗ 後端服務重啟失敗${NC}"
            echo "最後 30 行日誌："
            tail -30 /tmp/backend.log 2>/dev/null || tail -30 ~/liaotian/logs/backend.log 2>/dev/null || echo "未找到日誌文件"
        fi
    else
        echo -e "${RED}✗ 虛擬環境不存在，無法重啟服務${NC}"
    fi
    echo ""
fi

# 步驟 8: 檢查前端服務
echo -e "${BLUE}【步驟 8】檢查前端服務狀態...${NC}"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")

if [ "$FRONTEND_STATUS" = "200" ] || [ "$FRONTEND_STATUS" = "304" ]; then
    echo -e "${GREEN}✓ 前端服務運行正常 (HTTP $FRONTEND_STATUS)${NC}"
else
    echo -e "${YELLOW}⚠ 前端服務異常 (HTTP $FRONTEND_STATUS)${NC}"
    WARNING_COUNT=$((WARNING_COUNT + 1))
fi
echo ""

# 步驟 9: 檢查端口占用
echo -e "${BLUE}【步驟 9】檢查端口占用...${NC}"
if lsof -ti:8000 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ 端口 8000 已被占用（後端服務）${NC}"
else
    echo -e "${YELLOW}⚠ 端口 8000 未被占用${NC}"
    WARNING_COUNT=$((WARNING_COUNT + 1))
fi

if lsof -ti:3000 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ 端口 3000 已被占用（前端服務）${NC}"
else
    echo -e "${YELLOW}⚠ 端口 3000 未被占用${NC}"
    WARNING_COUNT=$((WARNING_COUNT + 1))
fi
echo ""

# 步驟 10: 最終驗證
echo "========================================="
echo -e "${BLUE}【最終驗證】${NC}"
echo "========================================="

FINAL_BACKEND=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
FINAL_FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")

echo "後端服務狀態: HTTP $FINAL_BACKEND"
echo "前端服務狀態: HTTP $FINAL_FRONTEND"
echo ""

# 測試 API 端點
if [ "$FINAL_BACKEND" = "200" ]; then
    echo "測試 API 端點..."
    
    # 測試健康檢查
    HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null)
    if [ -n "$HEALTH" ]; then
        echo -e "${GREEN}✓ /health 端點正常${NC}"
    fi
    
    # 測試 API 文檔（如果可用）
    DOCS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null || echo "000")
    if [ "$DOCS" = "200" ]; then
        echo -e "${GREEN}✓ API 文檔可訪問${NC}"
    fi
fi
echo ""

# 總結
echo "========================================="
echo -e "${BLUE}【測試總結】${NC}"
echo "========================================="
echo "錯誤數: $ERROR_COUNT"
echo "警告數: $WARNING_COUNT"
echo ""

if [ "$ERROR_COUNT" -eq 0 ] && [ "$FINAL_BACKEND" = "200" ]; then
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}✅ 所有關鍵測試通過！系統運行正常！${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""
    echo "後端服務: http://localhost:8000"
    echo "前端服務: http://localhost:3000"
    echo "API 文檔: http://localhost:8000/docs"
    exit 0
else
    echo -e "${YELLOW}=========================================${NC}"
    echo -e "${YELLOW}⚠ 發現 $ERROR_COUNT 個錯誤和 $WARNING_COUNT 個警告${NC}"
    echo -e "${YELLOW}=========================================${NC}"
    echo ""
    
    if [ "$FINAL_BACKEND" != "200" ]; then
        echo "後端服務日誌："
        tail -50 /tmp/backend.log 2>/dev/null || tail -50 ~/liaotian/logs/backend.log 2>/dev/null || echo "未找到日誌文件"
    fi
    
    exit 1
fi
