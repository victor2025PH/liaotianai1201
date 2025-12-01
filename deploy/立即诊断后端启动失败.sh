#!/bin/bash
# 立即診斷後端啟動失敗問題

echo "========================================="
echo "診斷後端啟動失敗問題"
echo "========================================="
echo ""

cd ~/liaotian/admin-backend

# 1. 查看錯誤日誌（最重要）
echo "【1】查看錯誤日誌..."
if [ -f "/tmp/backend.log" ]; then
    echo "最後 100 行："
    tail -100 /tmp/backend.log
    echo ""
    echo "錯誤關鍵詞："
    tail -100 /tmp/backend.log | grep -iE "error|exception|traceback|failed|fatal|import" | tail -10 || echo "  未發現明顯錯誤"
else
    echo "⚠ 日誌文件不存在: /tmp/backend.log"
fi
echo ""

# 2. 檢查虛擬環境和依賴
echo "【2】檢查環境..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✓ 虛擬環境已激活"
    echo "  Python: $(which python)"
    
    # 檢查關鍵依賴
    echo ""
    echo "關鍵依賴："
    for pkg in uvicorn fastapi sqlalchemy; do
        if pip list | grep -qi "^$pkg"; then
            echo "  ✓ $pkg: $(pip list | grep -i "^$pkg" | awk '{print $2}')"
        else
            echo "  ✗ $pkg: 未安裝"
        fi
    done
else
    echo "✗ 虛擬環境不存在"
fi
echo ""

# 3. 測試 Python 導入
echo "【3】測試 Python 導入..."
source .venv/bin/activate 2>/dev/null || true
python -c "from app.main import app; print('✓ 導入成功')" 2>&1 | head -30
echo ""

# 4. 檢查環境變量
echo "【4】檢查環境變量文件..."
if [ -f ".env" ]; then
    echo "✓ .env 存在"
else
    echo "✗ .env 不存在"
fi
echo ""

# 5. 檢查數據庫
echo "【5】檢查數據庫..."
if [ -f "admin.db" ]; then
    echo "✓ 數據庫文件存在"
else
    echo "⚠ 數據庫文件不存在"
fi
echo ""

echo "========================================="
echo "診斷完成 - 請查看上述錯誤信息"
echo "========================================="
