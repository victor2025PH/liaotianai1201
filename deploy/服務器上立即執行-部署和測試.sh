#!/bin/bash
# 在服務器上立即執行 - 重新部署並測試
# 這個腳本可以直接在服務器上執行，無需先拉取代碼

echo "========================================="
echo "重新部署後端並測試修復"
echo "========================================="
echo ""

# 項目目錄（根據實際情況調整）
PROJECT_DIR="/opt/group-ai"
if [ ! -d "$PROJECT_DIR" ]; then
    PROJECT_DIR="/opt/smart-tg"
fi

BACKEND_DIR="$PROJECT_DIR/admin-backend"

echo "項目目錄: $PROJECT_DIR"
echo "後端目錄: $BACKEND_DIR"
echo ""

# 檢查目錄是否存在
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ 後端目錄不存在: $BACKEND_DIR"
    echo "請檢查項目路徑"
    exit 1
fi

echo "【1】檢查並重啟後端服務..."
echo ""

# 方法1: 使用 systemd 服務
if systemctl list-unit-files | grep -q "smart-tg-backend.service"; then
    echo "使用 systemd 重啟服務..."
    if systemctl is-active --quiet smart-tg-backend.service; then
        echo "停止服務..."
        sudo systemctl stop smart-tg-backend.service
        sleep 3
    fi
    
    echo "啟動服務..."
    sudo systemctl start smart-tg-backend.service
    sleep 5
    
    if systemctl is-active --quiet smart-tg-backend.service; then
        echo "✅ 服務已重啟"
    else
        echo "⚠️ 服務啟動可能失敗，檢查狀態..."
        sudo systemctl status smart-tg-backend.service --no-pager -l | head -20
    fi
# 方法2: 手動重啟 uvicorn 進程
else
    echo "使用手動方式重啟..."
    
    # 停止現有進程
    UVICORN_PIDS=$(pgrep -f "uvicorn.*app.main:app" || true)
    if [ -n "$UVICORN_PIDS" ]; then
        echo "停止現有進程: $UVICORN_PIDS"
        pkill -f "uvicorn.*app.main:app" || true
        sleep 3
    fi
    
    # 啟動新進程
    cd "$BACKEND_DIR" || exit 1
    
    # 查找虛擬環境
    if [ -d "$PROJECT_DIR/.venv" ]; then
        VENV_PATH="$PROJECT_DIR/.venv"
    elif [ -d "$BACKEND_DIR/.venv" ]; then
        VENV_PATH="$BACKEND_DIR/.venv"
    else
        echo "⚠️ 未找到虛擬環境，使用系統 Python"
        VENV_PATH=""
    fi
    
    if [ -n "$VENV_PATH" ]; then
        source "$VENV_PATH/bin/activate"
        echo "已激活虛擬環境: $VENV_PATH"
    fi
    
    echo "啟動後端服務..."
    nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_$(date +%Y%m%d_%H%M%S).log 2>&1 &
    BACKEND_PID=$!
    echo "後端服務已啟動 (PID: $BACKEND_PID)"
    sleep 5
fi

echo ""
echo "【2】檢查後端健康狀態..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 後端服務正常運行"
        break
    else
        if [ $i -eq 10 ]; then
            echo "⚠️ 後端服務可能未正常啟動"
            echo "檢查日誌:"
            if systemctl list-unit-files | grep -q "smart-tg-backend.service"; then
                sudo journalctl -u smart-tg-backend.service -n 20 --no-pager
            else
                ls -lt /tmp/backend_*.log 2>/dev/null | head -1 | awk '{print $NF}' | xargs tail -20 2>/dev/null || echo "無法查看日誌"
            fi
        else
            echo "等待後端啟動... ($i/10)"
            sleep 2
        fi
    fi
done

echo ""
echo "【3】測試修復後的賬號狀態端點..."
echo "========================================="

# 獲取 Token
echo "獲取認證 Token..."
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123")

TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; data = json.loads(sys.stdin.read()); print(data.get('access_token', ''))" 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
    echo "❌ 無法獲取 Token"
    echo "響應: $TOKEN_RESPONSE"
    exit 1
fi

echo "✅ Token 獲取成功"
echo ""

# 測試賬號詳情（對照）
echo "【測試 1】查看賬號詳情（對照測試）..."
echo "端點: GET /api/v1/group-ai/accounts/639454959591"
ACCOUNT_DETAIL=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/group-ai/accounts/639454959591")

HTTP_STATUS_1=$(echo "$ACCOUNT_DETAIL" | grep "HTTP_STATUS" | cut -d: -f2)
ACCOUNT_BODY=$(echo "$ACCOUNT_DETAIL" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS_1" = "200" ]; then
    echo "✅ HTTP 200 - 賬號詳情獲取成功"
    echo "$ACCOUNT_BODY" | python3 -m json.tool 2>/dev/null | head -10 || echo "$ACCOUNT_BODY" | head -5
else
    echo "⚠️ HTTP $HTTP_STATUS_1"
    echo "$ACCOUNT_BODY" | head -5
fi

echo ""
echo "【測試 2】查看賬號狀態（修復驗證）..."
echo "端點: GET /api/v1/group-ai/accounts/639454959591/status"
STATUS_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/group-ai/accounts/639454959591/status")

HTTP_STATUS=$(echo "$STATUS_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
STATUS_BODY=$(echo "$STATUS_RESPONSE" | sed '/HTTP_STATUS/d')

echo "HTTP 狀態碼: $HTTP_STATUS"
echo ""

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ 修復成功！賬號狀態端點正常（HTTP 200）"
    echo ""
    echo "響應內容:"
    echo "$STATUS_BODY" | python3 -m json.tool 2>/dev/null || echo "$STATUS_BODY"
    echo ""
    echo "========================================="
    echo "✅ 修復驗證通過！"
    echo "========================================="
elif [ "$HTTP_STATUS" = "404" ]; then
    echo "❌ 仍返回 404 - 修復可能未生效"
    echo ""
    echo "響應內容:"
    echo "$STATUS_BODY"
    echo ""
    echo "可能原因:"
    echo "1. 代碼未更新（需要拉取最新代碼）"
    echo "2. 服務未重啟（需要重啟服務）"
    echo "3. 代碼緩存問題"
    echo ""
    echo "建議執行:"
    echo "cd $PROJECT_DIR && git pull && sudo systemctl restart smart-tg-backend.service"
else
    echo "⚠️ 返回 HTTP $HTTP_STATUS"
    echo ""
    echo "響應內容:"
    echo "$STATUS_BODY"
fi

echo ""
echo "========================================="
echo "測試完成"
echo "========================================="
