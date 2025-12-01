#!/bin/bash
# 重新部署後端並測試修復
set -e

echo "========================================="
echo "重新部署後端並測試修復"
echo "========================================="
echo ""

# 項目根目錄
PROJECT_DIR="/opt/group-ai"
BACKEND_DIR="$PROJECT_DIR/admin-backend"

# 進入項目目錄
cd "$PROJECT_DIR" || {
    echo "❌ 無法進入項目目錄: $PROJECT_DIR"
    exit 1
}

echo "【1】檢查 Git 狀態..."
cd "$PROJECT_DIR"
git status --short || echo "⚠️ Git 狀態檢查失敗（可能是非 Git 目錄）"

echo ""
echo "【2】拉取最新代碼..."
if [ -d ".git" ]; then
    git pull origin main || git pull origin master || echo "⚠️ Git pull 失敗，繼續使用當前代碼"
else
    echo "⚠️ 不是 Git 目錄，跳過拉取"
fi

echo ""
echo "【3】檢查後端服務狀態..."
if systemctl is-active --quiet smart-tg-backend.service; then
    echo "✅ 後端服務正在運行"
    echo "正在停止服務..."
    sudo systemctl stop smart-tg-backend.service
    sleep 2
else
    echo "ℹ️ 後端服務未運行"
fi

echo ""
echo "【4】檢查後端進程..."
UVICORN_PIDS=$(pgrep -f "uvicorn.*app.main:app" || true)
if [ -n "$UVICORN_PIDS" ]; then
    echo "發現後端進程: $UVICORN_PIDS"
    echo "正在停止..."
    pkill -f "uvicorn.*app.main:app" || true
    sleep 2
else
    echo "✅ 沒有運行中的後端進程"
fi

echo ""
echo "【5】啟動後端服務..."
if systemctl list-unit-files | grep -q "smart-tg-backend.service"; then
    echo "使用 systemd 啟動服務..."
    sudo systemctl start smart-tg-backend.service
    echo "等待服務啟動（10秒）..."
    sleep 10
    
    if systemctl is-active --quiet smart-tg-backend.service; then
        echo "✅ 後端服務已啟動"
    else
        echo "⚠️ 後端服務啟動可能失敗，檢查狀態..."
        sudo systemctl status smart-tg-backend.service --no-pager -l || true
    fi
else
    echo "⚠️ systemd 服務未找到，嘗試手動啟動..."
    cd "$BACKEND_DIR" || exit 1
    
    # 檢查虛擬環境
    if [ -d "$PROJECT_DIR/.venv" ]; then
        source "$PROJECT_DIR/.venv/bin/activate"
    elif [ -d "$BACKEND_DIR/.venv" ]; then
        source "$BACKEND_DIR/.venv/bin/activate"
    fi
    
    # 啟動後端（後台運行）
    nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
    echo "後端服務已在後台啟動 (PID: $!)"
    echo "等待服務啟動（5秒）..."
    sleep 5
fi

echo ""
echo "【6】檢查後端健康狀態..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 後端服務正常運行"
        break
    else
        if [ $i -eq 10 ]; then
            echo "⚠️ 後端服務可能未正常啟動，請檢查日誌"
        else
            echo "等待後端啟動... ($i/10)"
            sleep 2
        fi
    fi
done

echo ""
echo "【7】測試賬號狀態端點..."
echo "========================================="

# 獲取 Token
echo "獲取認證 Token..."
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123" | \
  python3 -c "import sys, json; print(json.loads(sys.stdin.read()).get('access_token', ''))" 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
    echo "❌ 無法獲取 Token，請檢查認證配置"
    exit 1
fi

echo "✅ Token 獲取成功"
echo ""

# 測試賬號詳情端點
echo "【測試 1】查看賬號詳情..."
ACCOUNT_DETAIL=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/group-ai/accounts/639454959591" | \
  python3 -m json.tool 2>/dev/null || echo "")

if [ -n "$ACCOUNT_DETAIL" ]; then
    echo "✅ 賬號詳情獲取成功"
    echo "$ACCOUNT_DETAIL" | head -15
else
    echo "⚠️ 賬號詳情獲取失敗"
fi

echo ""
echo "【測試 2】查看賬號狀態（修復後）..."
STATUS_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/group-ai/accounts/639454959591/status")

HTTP_STATUS=$(echo "$STATUS_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
STATUS_BODY=$(echo "$STATUS_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ 賬號狀態端點正常（HTTP 200）"
    echo "$STATUS_BODY" | python3 -m json.tool 2>/dev/null || echo "$STATUS_BODY"
    echo ""
    echo "✅ 修復驗證成功！"
elif [ "$HTTP_STATUS" = "404" ]; then
    echo "❌ 賬號狀態端點仍返回 404"
    echo "響應: $STATUS_BODY"
    echo ""
    echo "⚠️ 可能需要檢查代碼是否已更新"
else
    echo "⚠️ 賬號狀態端點返回 HTTP $HTTP_STATUS"
    echo "響應: $STATUS_BODY"
fi

echo ""
echo "========================================="
echo "部署和測試完成"
echo "========================================="
