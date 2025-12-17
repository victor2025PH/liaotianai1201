#!/bin/bash
# 檢查並修復網頁無法打開的問題

echo "========================================="
echo "檢查並修復服務狀態"
echo "========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 1. 檢查後端服務
echo "[1/5] 檢查後端服務 (luckyred-api)..."
if sudo systemctl is-active --quiet luckyred-api; then
    echo "✅ 後端服務正在運行"
else
    echo "❌ 後端服務未運行，正在啟動..."
    sudo systemctl start luckyred-api
    sleep 3
    if sudo systemctl is-active --quiet luckyred-api; then
        echo "✅ 後端服務已啟動"
    else
        echo "❌ 後端服務啟動失敗，查看錯誤："
        sudo systemctl status luckyred-api --no-pager -l | head -20
        echo ""
        echo "查看詳細日誌："
        sudo journalctl -u luckyred-api -n 30 --no-pager
    fi
fi
echo ""

# 2. 檢查前端服務
echo "[2/5] 檢查前端服務 (liaotian-frontend)..."
if sudo systemctl is-active --quiet liaotian-frontend; then
    echo "✅ 前端服務正在運行"
else
    echo "❌ 前端服務未運行，正在啟動..."
    sudo systemctl start liaotian-frontend
    sleep 5
    if sudo systemctl is-active --quiet liaotian-frontend; then
        echo "✅ 前端服務已啟動"
    else
        echo "❌ 前端服務啟動失敗，查看錯誤："
        sudo systemctl status liaotian-frontend --no-pager -l | head -20
        echo ""
        echo "查看詳細日誌："
        sudo journalctl -u liaotian-frontend -n 30 --no-pager
    fi
fi
echo ""

# 3. 檢查 Nginx
echo "[3/5] 檢查 Nginx..."
if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx 正在運行"
    sudo nginx -t && echo "✅ Nginx 配置正確" || echo "❌ Nginx 配置有錯誤"
else
    echo "❌ Nginx 未運行，正在啟動..."
    sudo systemctl start nginx
fi
echo ""

# 4. 檢查端口監聽
echo "[4/5] 檢查端口監聽..."
BACKEND_PORT=$(sudo ss -tlnp | grep :8000 | wc -l)
FRONTEND_PORT=$(sudo ss -tlnp | grep :3000 | wc -l)
NGINX_443=$(sudo ss -tlnp | grep :443 | wc -l)

if [ "$BACKEND_PORT" -gt 0 ]; then
    echo "✅ 後端端口 8000 正在監聽"
else
    echo "❌ 後端端口 8000 未監聽"
fi

if [ "$FRONTEND_PORT" -gt 0 ]; then
    echo "✅ 前端端口 3000 正在監聽"
else
    echo "❌ 前端端口 3000 未監聽"
fi

if [ "$NGINX_443" -gt 0 ]; then
    echo "✅ Nginx HTTPS 端口 443 正在監聽"
else
    echo "❌ Nginx HTTPS 端口 443 未監聽"
fi
echo ""

# 5. 測試健康檢查
echo "[5/5] 測試服務健康檢查..."
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")

if [ "$BACKEND_HEALTH" = "200" ]; then
    echo "✅ 後端健康檢查成功 (HTTP $BACKEND_HEALTH)"
else
    echo "❌ 後端健康檢查失敗 (HTTP $BACKEND_HEALTH)"
fi

if [ "$FRONTEND_HEALTH" = "200" ] || [ "$FRONTEND_HEALTH" = "304" ]; then
    echo "✅ 前端服務響應正常 (HTTP $FRONTEND_HEALTH)"
else
    echo "❌ 前端服務響應異常 (HTTP $FRONTEND_HEALTH)"
fi
echo ""

# 6. 如果服務有問題，嘗試重啟
if ! sudo systemctl is-active --quiet luckyred-api || ! sudo systemctl is-active --quiet liaotian-frontend; then
    echo "========================================="
    echo "嘗試重啟服務..."
    echo "========================================="
    
    cd "$PROJECT_DIR" || exit 1
    
    # 檢查 Python 語法
    echo "檢查後端代碼語法..."
    cd admin-backend
    source venv/bin/activate
    python -m py_compile app/api/workers.py && echo "✅ 後端代碼語法正確" || echo "❌ 後端代碼有語法錯誤"
    cd ..
    
    # 重啟服務
    echo ""
    echo "重啟所有服務..."
    sudo systemctl restart luckyred-api
    sudo systemctl restart liaotian-frontend
    sudo systemctl restart nginx
    
    sleep 5
    
    echo ""
    echo "檢查重啟後狀態..."
    sudo systemctl status luckyred-api --no-pager | head -5
    sudo systemctl status liaotian-frontend --no-pager | head -5
fi

echo ""
echo "========================================="
echo "檢查完成"
echo "========================================="
echo ""
echo "如果問題仍然存在，請查看詳細日誌："
echo "  後端: sudo journalctl -u luckyred-api -n 50 --no-pager"
echo "  前端: sudo journalctl -u liaotian-frontend -n 50 --no-pager"
echo "  Nginx: sudo tail -50 /var/log/nginx/error.log"
