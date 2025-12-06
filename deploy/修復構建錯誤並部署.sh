#!/bin/bash
# 修復構建錯誤並部署前端

set -e

echo "=========================================="
echo "修復構建錯誤並部署前端"
echo "=========================================="

cd ~/liaotian || {
    echo "❌ 無法進入項目目錄"
    exit 1
}

# 1. 拉取最新代碼
echo ""
echo "=== 1. 拉取最新代碼 ==="
git pull origin main || git pull origin master

# 2. 進入前端目錄
echo ""
echo "=== 2. 進入前端目錄 ==="
cd ~/liaotian/saas-demo || {
    echo "❌ 無法進入前端目錄"
    exit 1
}

# 3. 修復語法錯誤（如果還沒修復）
echo ""
echo "=== 3. 修復語法錯誤 ==="
# 修復 nullish coalescing 運算符問題
sed -i 's/|| accountWithNodeId\.node_id ?? undefined/|| (accountWithNodeId.node_id ?? undefined)/g' src/app/group-ai/accounts/page.tsx
echo "✅ 語法錯誤已修復"

# 4. 安裝依賴（確保 jszip 已安裝）
echo ""
echo "=== 4. 安裝依賴 ==="
npm install
echo "✅ 依賴安裝完成"

# 5. 清理緩存
echo ""
echo "=== 5. 清理構建緩存 ==="
rm -rf .next
rm -rf node_modules/.cache
echo "✅ 緩存已清理"

# 6. 構建前端
echo ""
echo "=== 6. 構建前端 ==="
if npm run build; then
    echo "✅ 前端構建成功"
else
    echo "❌ 前端構建失敗"
    echo "查看詳細錯誤..."
    exit 1
fi

# 7. 清理舊進程
echo ""
echo "=== 7. 清理舊進程 ==="
pkill -f "next-server" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true
pkill -f "npm.*start" 2>/dev/null || true
sleep 3

# 檢查並清理端口 3000
if command -v ss > /dev/null; then
    PID=$(ss -tlnp | grep :3000 | grep -oP 'pid=\K[0-9]+' | head -1 || true)
    if [ -n "$PID" ]; then
        echo "終止佔用端口 3000 的進程: $PID"
        kill $PID 2>/dev/null || true
        sleep 2
    fi
fi

# 8. 啟動前端服務
echo ""
echo "=== 8. 啟動前端服務 ==="
nohup npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 前端服務已啟動，進程ID: $FRONTEND_PID"

# 9. 等待並驗證
echo ""
echo "=== 9. 驗證服務 ==="
sleep 10

if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "✅ 前端進程正在運行 (PID: $FRONTEND_PID)"
else
    echo "❌ 前端進程已退出"
    echo "查看日誌:"
    tail -50 /tmp/frontend.log
    exit 1
fi

# 檢查端口
if command -v ss > /dev/null; then
    if ss -tlnp | grep :3000 > /dev/null; then
        echo "✅ 端口 3000 正在監聽"
    else
        echo "⚠️  端口 3000 未監聽"
        echo "查看日誌:"
        tail -30 /tmp/frontend.log
    fi
fi

# 檢查 HTTP 響應
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✅ 前端服務響應正常 (HTTP $HTTP_CODE)"
else
    echo "⚠️  前端服務無響應 (HTTP $HTTP_CODE)"
    echo "查看日誌: tail -f /tmp/frontend.log"
fi

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo "前端訪問: http://localhost:3000"
echo "前端日誌: tail -f /tmp/frontend.log"
