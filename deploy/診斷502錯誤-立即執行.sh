#!/bin/bash
# 診斷 502 Bad Gateway 錯誤

set -e

echo "=== 502 Bad Gateway 診斷 ==="
echo ""

echo "【步驟 1】檢查後端服務狀態..."
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo "✅ 後端進程正在運行"
    ps aux | grep "uvicorn.*app.main:app" | grep -v grep
else
    echo "❌ 後端進程未運行"
fi

echo ""
echo "【步驟 2】檢查端口 8000..."
if lsof -i :8000 > /dev/null 2>&1; then
    echo "✅ 端口 8000 正在監聽"
    lsof -i :8000
else
    echo "❌ 端口 8000 未監聽"
fi

echo ""
echo "【步驟 3】測試後端健康檢查..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 後端健康檢查通過"
    curl -s http://localhost:8000/health | head -5
else
    echo "❌ 後端健康檢查失敗"
    echo "嘗試連接..."
    curl -v http://localhost:8000/health 2>&1 | head -20
fi

echo ""
echo "【步驟 4】檢查 Nginx 配置..."
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    echo "檢查 Nginx 配置中的 proxy_pass..."
    grep -A 5 "proxy_pass" /etc/nginx/sites-enabled/default | head -10 || echo "未找到 proxy_pass 配置"
fi

if [ -f "/etc/nginx/nginx.conf" ]; then
    echo "檢查 Nginx 主配置..."
    grep -A 5 "proxy_pass" /etc/nginx/nginx.conf | head -10 || echo "未找到 proxy_pass 配置"
fi

echo ""
echo "【步驟 5】檢查 Nginx 錯誤日誌..."
if [ -f "/var/log/nginx/error.log" ]; then
    echo "最近的 Nginx 錯誤:"
    tail -20 /var/log/nginx/error.log | grep -i "502\|bad gateway\|upstream" || echo "未找到相關錯誤"
fi

echo ""
echo "【步驟 6】檢查後端日誌..."
if [ -f "/tmp/backend_final2.log" ]; then
    echo "最近的後端日誌:"
    tail -20 /tmp/backend_final2.log
elif [ -f "/tmp/backend.log" ]; then
    echo "最近的後端日誌:"
    tail -20 /tmp/backend.log
else
    echo "未找到後端日誌文件"
fi

echo ""
echo "=== 診斷完成 ==="
echo ""
echo "建議："
echo "1. 如果後端未運行，啟動後端服務"
echo "2. 如果端口未監聽，檢查後端配置"
echo "3. 如果 Nginx 配置錯誤，修復 proxy_pass 指向正確的後端地址"
