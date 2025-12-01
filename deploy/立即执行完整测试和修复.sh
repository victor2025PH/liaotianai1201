#!/bin/bash
# 立即執行完整測試和修復（簡化可靠版）

# 不使用 set -e，以便在遇到錯誤時繼續執行其他修復步驟

echo "========================================="
echo "全自動測試並修復系統"
echo "========================================="
echo ""

ERRORS=0

# 1. 修復循環導入
echo "【1】修復循環導入..."
cd ~/liaotian/admin-backend/app/api/group_ai
if grep -q ", statistics" __init__.py 2>/dev/null; then
    sed -i 's/, statistics//' __init__.py
    echo "✓ 已移除 statistics 導入"
fi

# 2. 驗證導入
echo ""
echo "【2】驗證模塊導入..."
cd ~/liaotian/admin-backend
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    
    if python3 -c "from app.main import app; print('✓ 所有模塊導入成功')" 2>&1; then
        echo "✓ 模塊導入成功"
    else
        echo "✗ 模塊導入失敗"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "✗ 虛擬環境不存在"
    ERRORS=$((ERRORS + 1))
fi

# 3. 檢查數據庫連接
echo ""
echo "【3】檢查數據庫連接..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    
    if python3 -c "from app.db import SessionLocal; db = SessionLocal(); print('✓ 數據庫連接成功'); db.close()" 2>&1; then
        echo "✓ 數據庫連接成功"
    else
        echo "✗ 數據庫連接失敗"
        ERRORS=$((ERRORS + 1))
    fi
fi

# 4. 停止舊服務
echo ""
echo "【4】停止舊服務..."
pkill -9 -f 'uvicorn.*app.main:app' || true
sleep 2

# 5. 啟動後端服務
echo ""
echo "【5】啟動後端服務..."
cd ~/liaotian/admin-backend
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
    sleep 8
else
    echo "✗ 虛擬環境不存在，無法啟動服務"
    ERRORS=$((ERRORS + 1))
fi

# 6. 驗證服務
echo ""
echo "【6】驗證服務狀態..."
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")

if [ "$HEALTH" = "200" ]; then
    echo "✓ 後端服務運行正常"
    curl -s http://localhost:8000/health
    echo ""
else
    echo "✗ 後端服務異常 (HTTP $HEALTH)"
    echo "最後 30 行日誌："
    tail -30 /tmp/backend.log 2>/dev/null || tail -30 ~/liaotian/logs/backend.log 2>/dev/null || echo "未找到日誌文件"
    ERRORS=$((ERRORS + 1))
fi

# 7. 最終總結
echo ""
echo "========================================="
if [ "$HEALTH" = "200" ] && [ "$ERRORS" -eq 0 ]; then
    echo "✅ 所有測試通過！系統運行正常！"
    echo ""
    echo "後端服務: http://localhost:8000"
    echo "API 文檔: http://localhost:8000/docs"
    exit 0
else
    echo "⚠ 發現 $ERRORS 個問題，請檢查上述輸出"
    if [ "$HEALTH" != "200" ]; then
        echo ""
        echo "後端服務日誌位置:"
        echo "  - /tmp/backend.log"
        echo "  - ~/liaotian/logs/backend.log"
    fi
    exit 1
fi
