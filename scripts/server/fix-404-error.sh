#!/bin/bash
# 修復 404 錯誤

echo "=========================================="
echo "修復 404 錯誤"
echo "=========================================="
echo ""

# 1. 禁用 default 站點（如果存在）
echo "[1/5] 禁用 default 站點..."
echo "----------------------------------------"
if [ -L "/etc/nginx/sites-enabled/default" ]; then
  sudo rm /etc/nginx/sites-enabled/default
  echo "✅ default 站點已禁用"
else
  echo "ℹ️  default 站點未啟用"
fi
echo ""

# 2. 確保自定義站點已啟用
echo "[2/5] 確保自定義站點已啟用..."
echo "----------------------------------------"
DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"

if [ ! -f "$NGINX_CONFIG" ]; then
  echo "❌ 配置文件不存在: $NGINX_CONFIG"
  echo "請先執行: sudo bash scripts/server/create-nginx-config.sh"
  exit 1
fi

if [ ! -L "$NGINX_ENABLED" ]; then
  sudo ln -s "$NGINX_CONFIG" "$NGINX_ENABLED"
  echo "✅ 站點已啟用"
else
  echo "✅ 站點已啟用（符號鏈接已存在）"
fi
echo ""

# 3. 檢查並修復 server_name 配置
echo "[3/5] 檢查 server_name 配置..."
echo "----------------------------------------"
if sudo grep -q "server_name.*${DOMAIN}" "$NGINX_CONFIG"; then
  echo "✅ server_name 配置正確"
else
  echo "⚠️  server_name 配置可能有問題"
  echo "當前配置:"
  sudo grep "server_name" "$NGINX_CONFIG"
fi
echo ""

# 4. 測試前端和後端服務
echo "[4/5] 測試前端和後端服務..."
echo "----------------------------------------"
FRONTEND_OK=false
BACKEND_OK=false

# 測試前端
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ | grep -qE "200|304"; then
  echo "✅ 前端服務正常 (localhost:3000)"
  FRONTEND_OK=true
else
  echo "❌ 前端服務無響應 (localhost:3000)"
  echo "   檢查前端服務: sudo systemctl status liaotian-frontend"
fi

# 測試後端
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
  echo "✅ 後端服務正常 (localhost:8000)"
  BACKEND_OK=true
else
  echo "❌ 後端服務無響應 (localhost:8000)"
  echo "   檢查後端服務: sudo systemctl status luckyred-api"
fi
echo ""

# 5. 重載 Nginx
echo "[5/5] 重載 Nginx..."
echo "----------------------------------------"
if sudo nginx -t; then
  echo "✅ 配置語法正確"
  sudo systemctl reload nginx
  if [ $? -eq 0 ]; then
    echo "✅ Nginx 已重載"
  else
    echo "⚠️  重載失敗，嘗試重啟..."
    sudo systemctl restart nginx
  fi
else
  echo "❌ 配置語法錯誤，請檢查配置文件"
  exit 1
fi
echo ""

# 6. 最終測試
echo "=========================================="
echo "最終測試"
echo "=========================================="
echo ""
sleep 2

echo "測試本地訪問（帶 Host 頭）:"
TEST_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: ${DOMAIN}" http://localhost/ 2>&1)
echo "狀態碼: $TEST_STATUS"

if [ "$TEST_STATUS" = "200" ] || [ "$TEST_STATUS" = "304" ]; then
  echo "✅ 本地測試成功！"
  echo ""
  echo "現在應該可以通過以下方式訪問網站："
  echo "  http://${DOMAIN}"
  echo ""
  if [ "$FRONTEND_OK" != "true" ] || [ "$BACKEND_OK" != "true" ]; then
    echo "⚠️  但部分服務可能異常，請檢查服務狀態"
  fi
else
  echo "⚠️  本地測試失敗（狀態碼: $TEST_STATUS）"
  echo ""
  echo "可能的原因："
  if [ "$FRONTEND_OK" != "true" ]; then
    echo "  - 前端服務未正常響應"
    echo "    解決: sudo systemctl restart liaotian-frontend"
  fi
  if [ "$BACKEND_OK" != "true" ]; then
    echo "  - 後端服務未正常響應"
    echo "    解決: sudo systemctl restart luckyred-api"
  fi
  echo "  - Nginx 配置問題"
  echo "    檢查: sudo nginx -t"
  echo "    查看日誌: sudo tail -20 /var/log/nginx/error.log"
fi
echo ""
echo "查看詳細日誌："
echo "  sudo journalctl -u liaotian-frontend -n 20 --no-pager"
echo "  sudo journalctl -u luckyred-api -n 20 --no-pager"
echo "  sudo tail -20 /var/log/nginx/error.log"
