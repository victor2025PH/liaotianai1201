#!/bin/bash
# 完成前端部署流程

set -e

echo "=========================================="
echo "完成前端部署"
echo "=========================================="

cd ~/liaotian || {
    echo "❌ 無法進入項目目錄"
    exit 1
}

# 1. 確認代碼已更新
echo ""
echo "=== 1. 確認代碼版本 ==="
echo "最新提交:"
git log --oneline -1

# 2. 檢查 TypeScript 文件是否已修復
echo ""
echo "=== 2. 檢查 TypeScript 修復 ==="
if grep -q "selectedAccountForRole?.node_id" saas-demo/src/app/group-ai/accounts/page.tsx 2>/dev/null; then
    echo "✅ TypeScript 修復已應用（使用可選鏈）"
else
    echo "⚠️  未找到修復，可能需要手動修復"
    echo "檢查文件..."
    grep -n "node_id" saas-demo/src/app/group-ai/accounts/page.tsx | head -5
fi

# 3. 清理舊進程
echo ""
echo "=== 3. 清理舊進程 ==="
pkill -f "next-server" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true
pkill -f "npm.*start" 2>/dev/null || true
sleep 3

# 4. 檢查並清理端口 3000
if command -v ss > /dev/null; then
    PID=$(ss -tlnp | grep :3000 | grep -oP 'pid=\K[0-9]+' | head -1 || true)
    if [ -n "$PID" ]; then
        echo "終止佔用端口 3000 的進程: $PID"
        kill $PID 2>/dev/null || true
        sleep 2
    fi
fi

# 5. 進入前端目錄
echo ""
echo "=== 4. 進入前端目錄 ==="
cd ~/liaotian/saas-demo || {
    echo "❌ 無法進入前端目錄"
    exit 1
}

# 6. 清理構建緩存
echo ""
echo "=== 5. 清理構建緩存 ==="
rm -rf .next
rm -rf node_modules/.cache
echo "✅ 緩存已清理"

# 7. 安裝依賴
echo ""
echo "=== 6. 安裝依賴 ==="
npm install

# 8. 構建前端
echo ""
echo "=== 7. 構建前端 ==="
if npm run build; then
    echo "✅ 前端構建成功"
else
    echo "❌ 前端構建失敗"
    echo ""
    echo "查看詳細錯誤："
    tail -30 /tmp/build.log 2>/dev/null || echo "日誌文件不存在"
    exit 1
fi

# 9. 啟動前端服務
echo ""
echo "=== 8. 啟動前端服務 ==="
nohup npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 前端服務已啟動，進程ID: $FRONTEND_PID"

# 10. 等待並驗證
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
        ss -tlnp | grep :3000
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

# 11. 檢查後端服務
echo ""
echo "=== 10. 檢查後端服務 ==="
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 後端服務正常運行"
    curl -s http://localhost:8000/health
else
    echo "⚠️  後端服務無響應"
fi

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "服務狀態："
echo "  後端: http://localhost:8000"
echo "  前端: http://localhost:3000"
echo ""
echo "日誌查看："
echo "  前端日誌: tail -f /tmp/frontend.log"
echo "  後端日誌: tail -f /tmp/backend.log"
echo ""
echo "停止服務："
echo "  前端: kill $FRONTEND_PID"
echo "  後端: pkill -f uvicorn"
echo ""
echo "檢查服務狀態："
echo "  ps aux | grep -E 'node|uvicorn' | grep -v grep"
echo "  ss -tlnp | grep -E ':3000|:8000'"
