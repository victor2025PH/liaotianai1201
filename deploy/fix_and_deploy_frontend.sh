#!/bin/bash
# 修復端口佔用並部署前端

set -e

echo "=========================================="
echo "修復端口佔用並部署前端"
echo "=========================================="

# 1. 進入項目目錄
cd ~/liaotian || {
    echo "❌ 無法進入項目目錄"
    exit 1
}

# 2. 拉取最新代碼
echo ""
echo "=== 1. 拉取最新代碼 ==="
git pull

# 3. 清理所有舊的前端進程和端口
echo ""
echo "=== 2. 清理舊進程和端口 ==="

# 終止所有 next 相關進程
pkill -f "next-server" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true
pkill -f "npm.*start" 2>/dev/null || true
sleep 3

# 檢查並終止佔用端口 3000 的進程
if command -v ss > /dev/null; then
    PORT_INFO=$(ss -tlnp | grep :3000 || true)
    if [ -n "$PORT_INFO" ]; then
        echo "發現端口 3000 被佔用:"
        echo "$PORT_INFO"
        
        # 提取 PID（支持多種格式）
        PID=$(echo "$PORT_INFO" | grep -oP 'pid=\K[0-9]+' | head -1 || true)
        
        if [ -z "$PID" ]; then
            # 嘗試其他方式提取 PID
            PID=$(echo "$PORT_INFO" | grep -oP 'users:\(\([^,]*pid=\K[0-9]+' | head -1 || true)
        fi
        
        if [ -n "$PID" ]; then
            echo "終止進程 PID: $PID"
            kill $PID 2>/dev/null || true
            sleep 2
            
            # 如果還在運行，強制終止
            if ps -p $PID > /dev/null 2>&1; then
                echo "進程仍在運行，強制終止..."
                kill -9 $PID 2>/dev/null || true
                sleep 1
            fi
            echo "✅ 進程已終止"
        else
            echo "⚠️  無法提取 PID，嘗試使用 lsof..."
            if command -v lsof > /dev/null; then
                PID=$(lsof -ti :3000 || true)
                if [ -n "$PID" ]; then
                    echo "終止進程 PID: $PID"
                    kill -9 $PID 2>/dev/null || true
                    sleep 2
                fi
            fi
        fi
    else
        echo "✅ 端口 3000 可用"
    fi
else
    echo "⚠️  ss 命令不可用，使用 lsof..."
    if command -v lsof > /dev/null; then
        PID=$(lsof -ti :3000 || true)
        if [ -n "$PID" ]; then
            echo "終止佔用端口 3000 的進程: $PID"
            kill -9 $PID 2>/dev/null || true
            sleep 2
        else
            echo "✅ 端口 3000 可用"
        fi
    else
        echo "⚠️  無法檢查端口（需要安裝 ss 或 lsof）"
    fi
fi

# 再次確認端口已釋放
sleep 2
if command -v ss > /dev/null; then
    if ss -tlnp | grep :3000 > /dev/null; then
        echo "⚠️  警告：端口 3000 仍被佔用"
        ss -tlnp | grep :3000
    else
        echo "✅ 確認：端口 3000 已釋放"
    fi
fi

# 4. 進入前端目錄
echo ""
echo "=== 3. 進入前端目錄 ==="
cd ~/liaotian/saas-demo || {
    echo "❌ 無法進入前端目錄"
    exit 1
}

echo "當前目錄: $(pwd)"

# 5. 檢查目錄結構
echo ""
echo "=== 4. 檢查目錄結構 ==="
if [ ! -d "src/app" ]; then
    echo "❌ 錯誤：找不到 src/app 目錄"
    echo "當前目錄內容:"
    ls -la
    exit 1
fi
echo "✅ 目錄結構正確"

# 6. 清理構建緩存
echo ""
echo "=== 5. 清理構建緩存 ==="
rm -rf .next
rm -rf node_modules/.cache
echo "✅ 緩存已清理"

# 7. 檢查 Node.js
echo ""
echo "=== 6. 檢查環境 ==="
if ! command -v node > /dev/null; then
    echo "❌ Node.js 未安裝"
    exit 1
fi
echo "✅ Node.js 版本: $(node --version)"
echo "✅ npm 版本: $(npm --version)"

# 8. 安裝依賴
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
    echo "請查看上方錯誤信息"
    exit 1
fi

# 10. 啟動前端服務
echo ""
echo "=== 9. 啟動前端服務 ==="
nohup npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 前端服務已啟動，進程ID: $FRONTEND_PID"
echo "   日誌文件: /tmp/frontend.log"

# 11. 等待服務啟動
echo ""
echo "=== 10. 等待服務啟動 ==="
sleep 10

# 12. 驗證服務
echo ""
echo "=== 11. 驗證服務 ==="
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
echo "停止服務: kill $FRONTEND_PID"
echo ""
echo "檢查服務狀態:"
echo "  ps aux | grep $FRONTEND_PID"
echo "  ss -tlnp | grep :3000"
echo "  curl http://localhost:3000"
