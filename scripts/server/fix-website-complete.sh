#!/bin/bash
# 完整修復網站訪問問題

echo "=========================================="
echo "完整修復網站訪問問題"
echo "=========================================="
echo ""

# 1. 創建並啟用 Nginx 配置
echo "[步驟 1/4] 創建並啟用 Nginx 配置..."
echo "----------------------------------------"
cd /home/ubuntu/telegram-ai-system
if [ -f "scripts/server/create-nginx-config.sh" ]; then
  chmod +x scripts/server/create-nginx-config.sh
  bash scripts/server/create-nginx-config.sh
else
  echo "⚠️  腳本不存在，手動執行配置創建..."
  # 這裡可以調用之前創建的配置邏輯
fi
echo ""

# 2. 測試 HTTP 訪問
echo "[步驟 2/4] 測試 HTTP 訪問..."
echo "----------------------------------------"
sleep 3
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "000" ]; then
  echo "✅ HTTP 訪問測試完成（狀態碼: $HTTP_STATUS）"
else
  echo "⚠️  HTTP 訪問返回狀態碼: $HTTP_STATUS"
fi
echo ""

# 3. 檢查服務狀態
echo "[步驟 3/4] 檢查所有服務狀態..."
echo "----------------------------------------"
SERVICES_OK=true

if sudo systemctl is-active --quiet liaotian-frontend; then
  echo "✅ 前端服務運行中"
else
  echo "❌ 前端服務未運行"
  SERVICES_OK=false
fi

if sudo systemctl is-active --quiet luckyred-api; then
  echo "✅ 後端服務運行中"
else
  echo "❌ 後端服務未運行"
  SERVICES_OK=false
fi

if sudo systemctl is-active --quiet nginx; then
  echo "✅ Nginx 運行中"
else
  echo "❌ Nginx 未運行"
  SERVICES_OK=false
fi
echo ""

# 4. 最終診斷報告
echo "[步驟 4/4] 最終診斷報告..."
echo "----------------------------------------"
echo "端口監聽狀態:"
PORTS_OK=true

if sudo ss -tlnp | grep -q ":80"; then
  echo "  ✅ 端口 80 (HTTP) 正在監聽"
else
  echo "  ❌ 端口 80 未監聽"
  PORTS_OK=false
fi

if sudo ss -tlnp | grep -q ":443"; then
  echo "  ✅ 端口 443 (HTTPS) 正在監聽"
else
  echo "  ⚠️  端口 443 未監聽（HTTPS 未配置）"
fi

if sudo ss -tlnp | grep -q ":3000"; then
  echo "  ✅ 端口 3000 (前端) 正在監聽"
else
  echo "  ❌ 端口 3000 未監聽"
  PORTS_OK=false
fi

if sudo ss -tlnp | grep -q ":8000"; then
  echo "  ✅ 端口 8000 (後端) 正在監聽"
else
  echo "  ❌ 端口 8000 未監聽"
  PORTS_OK=false
fi
echo ""

echo "=========================================="
echo "修復完成！"
echo "=========================================="
echo ""

if [ "$SERVICES_OK" = "true" ] && [ "$PORTS_OK" = "true" ]; then
  echo "✅ 所有服務和端口正常"
  echo ""
  echo "現在可以使用以下方式訪問網站："
  echo "  HTTP:  http://aikz.usdt2026.cc"
  echo ""
  if sudo ss -tlnp | grep -q ":443"; then
    echo "  HTTPS: https://aikz.usdt2026.cc"
  else
    echo "  ⚠️  HTTPS 尚未配置"
    echo ""
    echo "要配置 HTTPS，請執行："
    echo "  sudo certbot --nginx -d aikz.usdt2026.cc"
    echo ""
    echo "如果 Certbot 驗證失敗，請檢查："
    echo "  1. DNS 是否正確解析: nslookup aikz.usdt2026.cc"
    echo "  2. 域名是否指向此服務器 IP: $(curl -s ifconfig.me)"
    echo "  3. 端口 80 是否對外開放"
  fi
else
  echo "⚠️  仍有問題需要解決："
  if [ "$SERVICES_OK" != "true" ]; then
    echo "  - 部分服務未運行，請檢查服務日誌"
  fi
  if [ "$PORTS_OK" != "true" ]; then
    echo "  - 部分端口未監聽，請檢查服務狀態"
  fi
  echo ""
  echo "查看日誌："
  echo "  sudo journalctl -u liaotian-frontend -n 30 --no-pager"
  echo "  sudo journalctl -u luckyred-api -n 30 --no-pager"
  echo "  sudo journalctl -u nginx -n 30 --no-pager"
fi
