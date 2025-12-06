#!/bin/bash
# 完整的前端部署腳本（包含清理緩存和修復）

set -e

echo "=========================================="
echo "完整前端部署流程"
echo "=========================================="

# 1. 進入項目目錄
cd ~/liaotian || {
    echo "❌ 無法進入項目目錄"
    exit 1
}

echo ""
echo "=== 1. 拉取最新代碼 ==="
git pull

# 2. 清理端口 3000
echo ""
echo "=== 2. 清理端口 3000 ==="
if command -v ss > /dev/null; then
    PID=$(ss -tlnp | grep :3000 | grep -oP 'pid=\K[0-9]+' | head -1 || true)
    if [ -n "$PID" ]; then
        echo "終止佔用端口 3000 的進程: $PID"
        kill $PID 2>/dev/null || true
        sleep 2
    fi
fi

# 清理舊的前端進程
pkill -f "node.*next" 2>/dev/null || true
sleep 2

# 3. 進入前端目錄
echo ""
echo "=== 3. 清理構建緩存 ==="
cd ~/liaotian/saas-demo || {
    echo "❌ 無法進入前端目錄"
    exit 1
}

# 清理 Next.js 緩存
rm -rf .next
rm -rf node_modules/.cache
echo "✅ 緩存已清理"

# 4. 檢查 Node.js
echo ""
echo "=== 4. 檢查環境 ==="
if ! command -v node > /dev/null; then
    echo "❌ Node.js 未安裝"
    exit 1
fi
echo "✅ Node.js 版本: $(node --version)"

# 5. 安裝依賴
echo ""
echo "=== 5. 安裝依賴 ==="
npm install

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

# 7. 啟動前端服務
echo ""
echo "=== 7. 啟動前端服務 ==="
nohup npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 前端服務已啟動，進程ID: $FRONTEND_PID"
echo "   日誌文件: /tmp/frontend.log"

# 8. 等待並驗證
echo ""
echo "=== 8. 驗證服務 ==="
sleep 5

if ps -p $FRONTEND_PID > /dev/null; then
    echo "✅ 前端進程正在運行"
else
    echo "❌ 前端進程已退出"
    echo "查看日誌:"
    tail -30 /tmp/frontend.log
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
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ 前端服務響應正常"
else
    echo "⚠️  前端服務無響應，請檢查日誌: tail -f /tmp/frontend.log"
fi

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo "前端訪問: http://localhost:3000"
echo "前端日誌: tail -f /tmp/frontend.log"
echo "停止服務: kill $FRONTEND_PID"
