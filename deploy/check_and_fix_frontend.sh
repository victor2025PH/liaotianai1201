#!/bin/bash
# 檢查服務狀態和部署前端

set -e

echo "=========================================="
echo "檢查服務狀態和部署前端"
echo "=========================================="

# 1. 檢查後端服務狀態
echo ""
echo "=== 1. 檢查後端服務狀態 ==="
if ps aux | grep -v grep | grep uvicorn > /dev/null; then
    echo "✅ 後端服務正在運行"
    BACKEND_PID=$(ps aux | grep -v grep | grep uvicorn | awk '{print $2}' | head -1)
    echo "   進程ID: $BACKEND_PID"
else
    echo "❌ 後端服務未運行"
fi

# 檢查後端健康狀態
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 後端健康檢查通過"
    curl -s http://localhost:8000/health
else
    echo "❌ 後端健康檢查失敗"
fi

# 2. 檢查端口 3000 是否被佔用
echo ""
echo "=== 2. 檢查端口 3000 狀態 ==="

# 使用 ss 命令（現代替代 netstat）
if command -v ss > /dev/null; then
    PORT_3000=$(ss -tlnp | grep :3000 || true)
    if [ -n "$PORT_3000" ]; then
        echo "⚠️  端口 3000 已被佔用:"
        echo "$PORT_3000"
        echo ""
        echo "查找佔用端口的進程..."
        PID=$(ss -tlnp | grep :3000 | grep -oP 'pid=\K[0-9]+' | head -1)
        if [ -n "$PID" ]; then
            echo "進程ID: $PID"
            ps aux | grep $PID | grep -v grep
            echo ""
            read -p "是否要終止此進程？(y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                kill $PID
                echo "✅ 已終止進程 $PID"
                sleep 2
            fi
        fi
    else
        echo "✅ 端口 3000 可用"
    fi
else
    echo "⚠️  ss 命令未找到，嘗試使用 lsof..."
    if command -v lsof > /dev/null; then
        lsof -i :3000 || echo "✅ 端口 3000 可用"
    else
        echo "⚠️  無法檢查端口狀態（需要安裝 ss 或 lsof）"
    fi
fi

# 3. 進入前端目錄並構建
echo ""
echo "=== 3. 構建前端應用 ==="
cd ~/liaotian/saas-demo || {
    echo "❌ 無法進入前端目錄"
    exit 1
}

echo "當前目錄: $(pwd)"

# 檢查 Node.js
if ! command -v node > /dev/null; then
    echo "❌ Node.js 未安裝"
    exit 1
fi
echo "✅ Node.js 版本: $(node --version)"

# 安裝依賴（如果需要）
if [ ! -d "node_modules" ]; then
    echo "正在安裝依賴..."
    npm install
fi

# 構建前端
echo "正在構建前端..."
if npm run build; then
    echo "✅ 前端構建成功"
else
    echo "❌ 前端構建失敗"
    exit 1
fi

# 4. 啟動前端服務
echo ""
echo "=== 4. 啟動前端服務 ==="

# 檢查是否已經有前端進程在運行
if ps aux | grep -v grep | grep "node.*next" > /dev/null; then
    echo "⚠️  前端服務已在運行，正在重啟..."
    pkill -f "node.*next" || true
    sleep 2
fi

# 啟動前端服務
echo "正在啟動前端服務..."
nohup npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 前端服務已啟動，進程ID: $FRONTEND_PID"
echo "   日誌文件: /tmp/frontend.log"

# 等待服務啟動
sleep 5

# 5. 驗證前端服務
echo ""
echo "=== 5. 驗證前端服務 ==="
if ps -p $FRONTEND_PID > /dev/null; then
    echo "✅ 前端進程正在運行"
else
    echo "❌ 前端進程已退出"
    echo "查看日誌:"
    tail -20 /tmp/frontend.log
    exit 1
fi

# 檢查端口
if ss -tlnp | grep :3000 > /dev/null; then
    echo "✅ 端口 3000 正在監聽"
else
    echo "⚠️  端口 3000 未監聽，請檢查日誌"
    tail -20 /tmp/frontend.log
fi

# 檢查 HTTP 響應
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ 前端服務響應正常"
else
    echo "⚠️  前端服務無響應，請檢查日誌"
    tail -20 /tmp/frontend.log
fi

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo "後端: http://localhost:8000"
echo "前端: http://localhost:3000"
echo "前端日誌: tail -f /tmp/frontend.log"
