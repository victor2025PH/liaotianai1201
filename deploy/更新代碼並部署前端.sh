#!/bin/bash
# 更新代碼並部署前端（確保拉取最新修復）

set -e

echo "=========================================="
echo "更新代碼並部署前端"
echo "=========================================="

cd ~/liaotian || {
    echo "❌ 無法進入項目目錄"
    exit 1
}

# 1. 拉取最新代碼（確保有最新修復）
echo ""
echo "=== 1. 拉取最新代碼 ==="
git fetch origin
git pull origin main || git pull origin master

# 2. 確認代碼已更新
echo ""
echo "=== 2. 檢查最新提交 ==="
git log --oneline -3

# 3. 檢查 TypeScript 文件是否有修復
echo ""
echo "=== 3. 檢查關鍵文件 ==="
if grep -q "selectedAccountForRole?.node_id" saas-demo/src/app/group-ai/accounts/page.tsx 2>/dev/null; then
    echo "✅ 已找到修復（使用可選鏈）"
else
    echo "⚠️  未找到修復，可能需要手動修復"
fi

# 4. 清理舊進程
echo ""
echo "=== 4. 清理舊進程 ==="
pkill -f "next-server" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true
pkill -f "npm.*start" 2>/dev/null || true
sleep 3

# 5. 檢查並清理端口 3000
if command -v ss > /dev/null; then
    PID=$(ss -tlnp | grep :3000 | grep -oP 'pid=\K[0-9]+' | head -1 || true)
    if [ -n "$PID" ]; then
        echo "終止佔用端口 3000 的進程: $PID"
        kill $PID 2>/dev/null || true
        sleep 2
    fi
fi

# 6. 進入前端目錄
echo ""
echo "=== 5. 進入前端目錄 ==="
cd ~/liaotian/saas-demo || {
    echo "❌ 無法進入前端目錄"
    exit 1
}

echo "當前目錄: $(pwd)"

# 7. 清理緩存
echo ""
echo "=== 6. 清理構建緩存 ==="
rm -rf .next
rm -rf node_modules/.cache
echo "✅ 緩存已清理"

# 8. 安裝依賴（如果需要）
echo ""
echo "=== 7. 安裝依賴 ==="
npm install

# 9. 構建前端
echo ""
echo "=== 8. 構建前端 ==="
if npm run build; then
    echo "✅ 前端構建成功"
else
    echo "❌ 前端構建失敗"
    echo ""
    echo "如果仍然有 TypeScript 錯誤，請執行："
    echo "  cd ~/liaotian"
    echo "  git pull origin main"
    echo "  然後重新構建"
    exit 1
fi

# 10. 啟動前端服務
echo ""
echo "=== 9. 啟動前端服務 ==="
nohup npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 前端服務已啟動，進程ID: $FRONTEND_PID"

# 11. 等待並驗證
echo ""
echo "=== 10. 驗證服務 ==="
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
echo "停止服務: kill $FRONTEND_PID"
