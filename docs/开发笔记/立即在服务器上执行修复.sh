#!/bin/bash
# 立即在服務器上執行的修復命令

echo "========================================="
echo "拉取修復並重啟服務"
echo "========================================="
echo ""

cd ~/liaotian

# 1. 拉取最新代碼
echo "【1】拉取最新代碼..."
git pull origin main
echo ""

# 2. 停止舊服務
echo "【2】停止舊服務..."
pkill -9 -f 'uvicorn.*app.main:app' || true
sleep 2
echo ""

# 3. 清理緩存
echo "【3】清理緩存..."
cd admin-backend
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo ""

# 4. 啟動服務
echo "【4】啟動服務..."
source .venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 5
echo ""

# 5. 檢查
echo "【5】檢查服務..."
curl -s http://localhost:8000/health && echo "✓ 服務正常" || tail -20 /tmp/backend.log

echo ""
echo "完成！"
