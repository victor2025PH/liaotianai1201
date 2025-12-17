#!/bin/bash
# 診斷 404 錯誤問題

echo "=========================================="
echo "診斷 404 錯誤問題"
echo "=========================================="
echo ""

# 1. 測試直接訪問前端
echo "[1/6] 測試直接訪問前端 (localhost:3000)..."
echo "----------------------------------------"
FRONTEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ 2>&1)
echo "前端響應狀態碼: $FRONTEND_TEST"
if [ "$FRONTEND_TEST" = "200" ] || [ "$FRONTEND_TEST" = "304" ]; then
  echo "✅ 前端服務正常響應"
else
  echo "⚠️  前端服務響應異常（狀態碼: $FRONTEND_TEST）"
fi
echo ""

# 2. 測試直接訪問後端
echo "[2/6] 測試直接訪問後端 (localhost:8000)..."
echo "----------------------------------------"
BACKEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>&1)
echo "後端健康檢查狀態碼: $BACKEND_TEST"
if [ "$BACKEND_TEST" = "200" ]; then
  echo "✅ 後端服務正常響應"
else
  echo "⚠️  後端服務響應異常（狀態碼: $BACKEND_TEST）"
fi
echo ""

# 3. 檢查 Nginx 配置中啟用的站點
echo "[3/6] 檢查啟用的 Nginx 站點..."
echo "----------------------------------------"
echo "啟用的站點配置:"
ls -la /etc/nginx/sites-enabled/ 2>/dev/null
echo ""

# 檢查是否有 default 站點在干擾
if [ -L "/etc/nginx/sites-enabled/default" ]; then
  echo "⚠️  發現 default 站點已啟用，可能會干擾自定義配置"
  echo "建議禁用: sudo rm /etc/nginx/sites-enabled/default"
fi
echo ""

# 4. 檢查 Nginx 訪問日誌
echo "[4/6] 檢查最近的 Nginx 訪問日誌..."
echo "----------------------------------------"
if [ -f "/var/log/nginx/access.log" ]; then
  echo "最近的訪問記錄（最後 5 條）:"
  sudo tail -5 /var/log/nginx/access.log
else
  echo "⚠️  訪問日誌文件不存在"
fi
echo ""

# 5. 檢查 Nginx 錯誤日誌
echo "[5/6] 檢查最近的 Nginx 錯誤日誌..."
echo "----------------------------------------"
if [ -f "/var/log/nginx/error.log" ]; then
  echo "最近的錯誤記錄（最後 10 條）:"
  sudo tail -10 /var/log/nginx/error.log
else
  echo "⚠️  錯誤日誌文件不存在"
fi
echo ""

# 6. 檢查實際的 Nginx 配置（測試請求如何被路由）
echo "[6/6] 測試 Nginx 代理..."
echo "----------------------------------------"
echo "測試通過 Nginx 訪問前端:"
NGINX_FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: aikz.usdt2026.cc" http://localhost/ 2>&1)
echo "Nginx 代理前端狀態碼: $NGINX_FRONTEND"

echo ""
echo "測試通過 Nginx 訪問後端 API:"
NGINX_BACKEND=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: aikz.usdt2026.cc" http://localhost/api/v1/health 2>&1)
echo "Nginx 代理後端狀態碼: $NGINX_BACKEND"
echo ""

# 7. 檢查 Nginx 配置文件的實際內容
echo "[7/7] 檢查 Nginx 配置文件內容..."
echo "----------------------------------------"
NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
if [ -f "$NGINX_CONFIG" ]; then
  echo "配置文件前 30 行:"
  sudo head -30 "$NGINX_CONFIG"
else
  echo "❌ 配置文件不存在"
fi
echo ""

echo "=========================================="
echo "診斷完成"
echo "=========================================="
echo ""
echo "建議修復步驟："
echo "1. 如果前端直接訪問失敗，檢查前端服務狀態"
echo "2. 如果 default 站點已啟用，禁用它"
echo "3. 檢查 Nginx 配置中的 server_name 是否正確"
echo "4. 檢查 Nginx 錯誤日誌中的具體錯誤信息"
echo ""
echo "快速修復命令："
echo "  # 禁用 default 站點"
echo "  sudo rm /etc/nginx/sites-enabled/default"
echo "  sudo nginx -t && sudo systemctl reload nginx"
echo ""
echo "  # 檢查前端服務"
echo "  curl -v http://localhost:3000/"
echo ""
echo "  # 查看完整 Nginx 配置"
echo "  sudo cat /etc/nginx/sites-available/aikz.usdt2026.cc"
