#!/bin/bash
# 快速健康檢查腳本
# 用於快速驗證服務是否正常

echo "=========================================="
echo "快速健康檢查"
echo "=========================================="
echo ""

# 檢查 PM2 服務
echo "PM2 服務狀態:"
pm2 list | grep -E "backend|frontend" | head -n 2
echo ""

# 檢查端口
echo "端口監聽狀態:"
ss -tlnp | grep -E ":8000|:3000" | head -n 2
echo ""

# 健康檢查
echo "後端健康檢查:"
curl -s http://localhost:8000/health | head -n 3 || echo "失敗"
echo ""

echo "前端響應:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✓ 前端正常 (HTTP $HTTP_CODE)"
else
    echo "✗ 前端異常 (HTTP $HTTP_CODE)"
fi
echo ""

echo "檢查完成！"

