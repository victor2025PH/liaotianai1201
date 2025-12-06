#!/bin/bash
# 簡化版前端部署腳本

set -e

echo "=========================================="
echo "前端部署流程"
echo "=========================================="

# 確保在項目根目錄
cd ~/liaotian || {
    echo "❌ 無法進入項目目錄 ~/liaotian"
    exit 1
}

echo "當前目錄: $(pwd)"

# 拉取代碼
echo ""
echo "=== 1. 拉取最新代碼 ==="
git pull

# 清理舊進程
echo ""
echo "=== 2. 清理舊進程 ==="
pkill -f "node.*next" 2>/dev/null || true
pkill -f "npm.*start" 2>/dev/null || true
sleep 2

# 檢查並清理端口 3000
if command -v ss > /dev/null; then
    PID=$(ss -tlnp | grep :3000 | grep -oP 'pid=\K[0-9]+' | head -1 || true)
    if [ -n "$PID" ]; then
        echo "終止佔用端口 3000 的進程: $PID"
        kill $PID 2>/dev/null || true
        sleep 2
    fi
fi

# 進入前端目錄
echo ""
echo "=== 3. 進入前端目錄 ==="
cd ~/liaotian/saas-demo || {
    echo "❌ 無法進入前端目錄 ~/liaotian/saas-demo"
    echo "請確認目錄是否存在: ls -la ~/liaotian/"
    exit 1
}

echo "當前目錄: $(pwd)"
echo "目錄內容:"
ls -la | head -10

# 檢查是否有 app 或 pages 目錄
if [ ! -d "src/app" ] && [ ! -d "pages" ]; then
    echo "❌ 錯誤：找不到 app 或 pages 目錄"
    echo "當前目錄結構:"
    ls -la
    exit 1
fi

# 檢查 Node.js
echo ""
echo "=== 4. 檢查環境 ==="
if ! command -v node > /dev/null; then
    echo "❌ Node.js 未安裝"
    exit 1
fi
echo "✅ Node.js 版本: $(node --version)"
echo "✅ npm 版本: $(npm --version)"

# 安裝依賴
echo ""
echo "=== 5. 安裝依賴 ==="
npm install

# 清理緩存
echo ""
echo "=== 6. 清理構建緩存 ==="
rm -rf .next
rm -rf node_modules/.cache
echo "✅ 緩存已清理"

# 構建前端
echo ""
echo "=== 7. 構建前端 ==="
echo "當前目錄: $(pwd)"
if npm run build; then
    echo "✅ 前端構建成功"
else
    echo "❌ 前端構建失敗"
    echo "請檢查錯誤信息"
    exit 1
fi

# 啟動前端服務
echo ""
echo "=== 8. 啟動前端服務 ==="
nohup npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 前端服務已啟動，進程ID: $FRONTEND_PID"

# 等待服務啟動
sleep 8

# 驗證服務
echo ""
echo "=== 9. 驗證服務 ==="
if ps -p $FRONTEND_PID > /dev/null; then
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
sleep 2
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200\|301\|302"; then
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
