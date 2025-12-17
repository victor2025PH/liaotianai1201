#!/bin/bash
# 修復後端服務 502 錯誤

echo "=========================================="
echo "修復後端服務 502 錯誤"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
SERVICE_NAME="luckyred-api"

# 1. 檢查後端服務狀態
echo "[1/6] 檢查後端服務狀態..."
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "  ✅ 後端服務正在運行"
    systemctl status $SERVICE_NAME --no-pager | head -5
else
    echo "  ❌ 後端服務未運行"
fi
echo ""

# 2. 檢查端口 8000
echo "[2/6] 檢查端口 8000..."
if ss -tlnp | grep -q ":8000"; then
    echo "  ✅ 端口 8000 正在監聽"
    ss -tlnp | grep ":8000"
else
    echo "  ❌ 端口 8000 未被監聽"
fi
echo ""

# 3. 測試後端健康檢查
echo "[3/6] 測試後端健康檢查..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "  ✅ 健康檢查通過 (HTTP $HEALTH_RESPONSE)"
    curl -s http://localhost:8000/health | head -3
else
    echo "  ❌ 健康檢查失敗 (HTTP $HEALTH_RESPONSE)"
fi
echo ""

# 4. 查看後端日誌（最近的錯誤）
echo "[4/6] 查看後端日誌（最近 20 行）..."
sudo journalctl -u $SERVICE_NAME -n 20 --no-pager | tail -15
echo ""

# 5. 嘗試修復
echo "[5/6] 嘗試修復..."
echo "  正在重啟後端服務..."
sudo systemctl restart $SERVICE_NAME

# 等待服務啟動
echo "  等待服務啟動（5秒）..."
sleep 5

# 檢查服務是否啟動成功
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "  ✅ 後端服務已重啟"
else
    echo "  ❌ 後端服務重啟失敗"
    echo "  查看詳細錯誤："
    sudo journalctl -u $SERVICE_NAME -n 30 --no-pager
    echo ""
    echo "  嘗試檢查依賴和配置..."
    
    # 檢查虛擬環境和依賴
    if [ -d "$BACKEND_DIR/venv" ]; then
        echo "  ✅ 找到虛擬環境"
        cd "$BACKEND_DIR"
        source venv/bin/activate
        echo "  檢查 Python 版本..."
        python --version
        echo "  檢查關鍵依賴..."
        pip list | grep -E "fastapi|uvicorn|sqlalchemy" || echo "  ⚠️ 缺少關鍵依賴"
    else
        echo "  ❌ 未找到虛擬環境: $BACKEND_DIR/venv"
    fi
fi
echo ""

# 6. 最終驗證
echo "[6/6] 最終驗證..."
sleep 2

if systemctl is-active --quiet $SERVICE_NAME; then
    FINAL_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
    if [ "$FINAL_HEALTH" = "200" ]; then
        echo "  ✅ 後端服務運行正常"
        echo "  ✅ 健康檢查通過"
        echo ""
        echo "=========================================="
        echo "✅ 修復完成！後端服務現在應該可以正常工作了"
        echo "=========================================="
    else
        echo "  ⚠️ 服務已運行，但健康檢查仍失敗 (HTTP $FINAL_HEALTH)"
        echo "  請檢查日誌以找出問題："
        echo "  sudo journalctl -u $SERVICE_NAME -f"
    fi
else
    echo "  ❌ 服務仍未運行"
    echo "  請手動檢查："
    echo "  sudo systemctl status $SERVICE_NAME"
    echo "  sudo journalctl -u $SERVICE_NAME -n 50"
fi
echo ""
