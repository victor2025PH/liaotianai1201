#!/bin/bash
# 立即診斷和修復 502 錯誤

set -e

echo "=== 502 Bad Gateway 診斷和修復 ==="
echo ""

# 診斷
echo "【診斷】檢查後端服務狀態..."
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo "✅ 後端進程正在運行"
    PID=$(pgrep -f "uvicorn.*app.main:app" | head -1)
    echo "  進程 ID: $PID"
else
    echo "❌ 後端進程未運行"
fi

echo ""
echo "【診斷】檢查端口 8000..."
if lsof -i :8000 > /dev/null 2>&1; then
    echo "✅ 端口 8000 正在監聽"
else
    echo "❌ 端口 8000 未監聽"
fi

echo ""
echo "【診斷】測試後端健康檢查..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 後端健康檢查通過"
    curl -s http://localhost:8000/health
else
    echo "❌ 後端健康檢查失敗"
fi

echo ""
echo "【診斷】檢查 Nginx 錯誤日誌..."
if [ -f "/var/log/nginx/error.log" ]; then
    echo "最近的 Nginx 錯誤:"
    tail -10 /var/log/nginx/error.log | grep -i "502\|bad gateway\|upstream" || echo "未找到相關錯誤"
fi

echo ""
echo "=== 開始修復 ==="
echo ""

# 如果後端未運行，啟動後端
if ! pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo "【修復】啟動後端服務..."
    cd /home/ubuntu/liaotian/deployment-package/admin-backend
    source /home/ubuntu/liaotian/admin-backend/.venv/bin/activate
    export PYTHONPATH=/home/ubuntu/liaotian/deployment-package
    export JWT_SECRET='kLZdZJCzq8qev_isfbrxjSshcHGiMDMA8Uok8f55RXc'
    export ADMIN_DEFAULT_PASSWORD='Along2021!!!'
    
    # 停止舊進程（如果存在）
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    sleep 2
    
    # 啟動新進程
    nohup /home/ubuntu/liaotian/admin-backend/.venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final2.log 2>&1 &
    
    echo "✅ 後端服務已啟動"
    echo "等待服務啟動..."
    sleep 5
    
    # 驗證啟動
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 後端服務啟動成功"
    else
        echo "⚠️ 後端服務可能啟動失敗，請檢查日誌: /tmp/backend_final2.log"
    fi
else
    echo "✅ 後端服務已在運行"
fi

echo ""
echo "【驗證】最終檢查..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 後端服務正常"
    echo ""
    echo "如果網頁仍顯示 502，請檢查："
    echo "1. Nginx 配置中的 proxy_pass 是否指向 http://127.0.0.1:8000"
    echo "2. Nginx 是否重載配置: sudo nginx -s reload"
    echo "3. 防火牆是否允許連接"
else
    echo "❌ 後端服務仍有問題"
    echo "請查看日誌: tail -50 /tmp/backend_final2.log"
fi

echo ""
echo "=== 診斷和修復完成 ==="
