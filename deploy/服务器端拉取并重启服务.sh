#!/bin/bash
# 服務器端：拉取最新代碼並重啟服務

set -e

echo "========================================="
echo "拉取最新代碼並重啟服務"
echo "開始時間: $(date)"
echo "========================================="
echo ""

cd ~/liaotian

# 步驟 1: 拉取最新代碼
echo "【步驟1】拉取最新代碼..."
git pull origin main
if [ $? -eq 0 ]; then
    echo "  ✓ 代碼拉取成功"
    echo "  最新提交: $(git log --oneline -1)"
else
    echo "  ✗ 代碼拉取失敗"
    exit 1
fi
echo ""

# 步驟 2: 停止舊服務
echo "【步驟2】停止舊服務..."
pkill -9 -f 'uvicorn.*app.main:app' || true
pkill -9 -f 'python.*uvicorn.*app.main' || true
sleep 3
echo "  ✓ 舊服務已停止"
echo ""

# 步驟 3: 清理緩存
echo "【步驟3】清理 Python 緩存..."
cd ~/liaotian/admin-backend
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "  ✓ 緩存已清理"
echo ""

# 步驟 4: 激活虛擬環境
echo "【步驟4】激活虛擬環境..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "  ✓ 虛擬環境已激活"
else
    echo "  ✗ 虛擬環境不存在"
    exit 1
fi
echo ""

# 步驟 5: 啟動服務
echo "【步驟5】啟動後端服務..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "  後端進程 PID: $BACKEND_PID"
echo ""

# 步驟 6: 等待服務啟動
echo "【步驟6】等待服務啟動..."
STARTED=0
for i in {1..15}; do
    sleep 2
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✓ 後端服務已啟動（等待了 $((i*2)) 秒）"
        STARTED=1
        break
    fi
done

if [ $STARTED -eq 0 ]; then
    echo "  ⚠ 服務啟動超時，查看日誌..."
    tail -30 /tmp/backend.log
    exit 1
fi
echo ""

# 步驟 7: 驗證服務
echo "【步驟7】驗證服務..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_RESPONSE" | grep -q "ok\|healthy"; then
    echo "  ✓ 後端服務正常運行"
    echo "  健康檢查響應: $HEALTH_RESPONSE"
else
    echo "  ⚠ 健康檢查響應異常: $HEALTH_RESPONSE"
    echo "  查看日誌:"
    tail -20 /tmp/backend.log
fi
echo ""

echo "========================================="
echo "完成！"
echo "完成時間: $(date)"
echo "========================================="
echo ""
echo "服務狀態："
echo "  PID: $BACKEND_PID"
echo "  日誌: /tmp/backend.log"
echo ""
echo "查看日誌："
echo "  tail -f /tmp/backend.log"
echo ""
