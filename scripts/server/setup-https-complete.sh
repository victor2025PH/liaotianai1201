#!/bin/bash
# 完整配置 HTTPS

echo "=========================================="
echo "配置 HTTPS 支持"
echo "=========================================="
echo ""

DOMAIN="aikz.usdt2026.cc"

# 1. 檢查 DNS 解析
echo "[1/6] 檢查 DNS 解析..."
echo "----------------------------------------"
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null)
DNS_IP=$(nslookup ${DOMAIN} 2>/dev/null | grep -A 1 "Name:" | tail -1 | awk '{print $2}' || echo "")

echo "服務器公網 IP: $SERVER_IP"
echo "DNS 解析 IP: $DNS_IP"

if [ -n "$DNS_IP" ] && [ "$DNS_IP" = "$SERVER_IP" ]; then
  echo "✅ DNS 解析正確"
  DNS_OK=true
else
  echo "⚠️  DNS 解析可能不正確或未解析"
  echo "   請確保 DNS A 記錄指向: $SERVER_IP"
  DNS_OK=false
fi
echo ""

# 2. 檢查端口 80 是否開放
echo "[2/6] 檢查防火牆..."
echo "----------------------------------------"
if command -v ufw &> /dev/null; then
  UFW_STATUS=$(sudo ufw status | grep -c "80.*ALLOW" || echo "0")
  if [ "$UFW_STATUS" -gt 0 ]; then
    echo "✅ 端口 80 已開放"
  else
    echo "⚠️  端口 80 可能未開放，嘗試開放..."
    sudo ufw allow 80/tcp
    echo "✅ 端口 80 已開放"
  fi
  
  UFW_STATUS_443=$(sudo ufw status | grep -c "443.*ALLOW" || echo "0")
  if [ "$UFW_STATUS_443" -gt 0 ]; then
    echo "✅ 端口 443 已開放"
  else
    echo "⚠️  端口 443 未開放，嘗試開放..."
    sudo ufw allow 443/tcp
    echo "✅ 端口 443 已開放"
  fi
else
  echo "ℹ️  未檢測到 UFW 防火牆"
fi
echo ""

# 3. 確保 Nginx 正在運行
echo "[3/6] 確保 Nginx 正在運行..."
echo "----------------------------------------"
if sudo systemctl is-active --quiet nginx; then
  echo "✅ Nginx 正在運行"
else
  echo "⚠️  Nginx 未運行，啟動中..."
  sudo systemctl start nginx
  sleep 2
  if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx 已啟動"
  else
    echo "❌ Nginx 啟動失敗"
    exit 1
  fi
fi
echo ""

# 4. 確保端口 80 正在監聽
echo "[4/6] 檢查端口監聽..."
echo "----------------------------------------"
if sudo ss -tlnp | grep -q ":80"; then
  echo "✅ 端口 80 正在監聽"
else
  echo "❌ 端口 80 未監聽，請檢查 Nginx 配置"
  exit 1
fi
echo ""

# 5. 嘗試獲取 SSL 證書
echo "[5/6] 獲取 SSL 證書..."
echo "----------------------------------------"
if ! command -v certbot &> /dev/null; then
  echo "⚠️  Certbot 未安裝，正在安裝..."
  sudo apt-get update -qq
  sudo apt-get install -y certbot python3-certbot-nginx
fi

echo "嘗試使用 Certbot 獲取證書..."
echo ""

# 使用非交互模式，如果失敗會顯示錯誤
sudo certbot --nginx -d ${DOMAIN} --non-interactive --agree-tos --email admin@${DOMAIN} --redirect 2>&1 | tee /tmp/certbot.log

CERTBOT_EXIT_CODE=${PIPESTATUS[0]}

if [ $CERTBOT_EXIT_CODE -eq 0 ]; then
  echo ""
  echo "✅ SSL 證書已成功配置"
  HTTPS_OK=true
else
  echo ""
  echo "⚠️  Certbot 配置失敗（退出碼: $CERTBOT_EXIT_CODE）"
  echo ""
  echo "可能的問題："
  
  if grep -q "No such authorization" /tmp/certbot.log 2>/dev/null; then
    echo "  - 域名驗證失敗"
    if [ "$DNS_OK" != "true" ]; then
      echo "    → DNS 未正確解析到此服務器"
      echo "    → 請檢查 DNS A 記錄是否指向: $SERVER_IP"
    else
      echo "    → 可能是臨時 DNS 傳播問題，請稍後重試"
    fi
  fi
  
  if grep -q "Connection refused" /tmp/certbot.log 2>/dev/null; then
    echo "  - 無法連接到服務器"
    echo "    → 請確保端口 80 對外開放"
  fi
  
  echo ""
  echo "查看完整錯誤日誌："
  echo "  cat /tmp/certbot.log"
  
  HTTPS_OK=false
fi
echo ""

# 6. 驗證 HTTPS 配置
echo "[6/6] 驗證 HTTPS 配置..."
echo "----------------------------------------"
if [ "$HTTPS_OK" = "true" ]; then
  # 檢查 443 端口是否監聽
  if sudo ss -tlnp | grep -q ":443"; then
    echo "✅ 端口 443 正在監聽"
  else
    echo "⚠️  端口 443 未監聽，但證書已配置"
  fi
  
  # 檢查 Nginx 配置是否包含 HTTPS
  if sudo grep -q "listen 443 ssl" /etc/nginx/sites-available/${DOMAIN} 2>/dev/null; then
    echo "✅ Nginx 配置包含 HTTPS"
  else
    echo "⚠️  Nginx 配置中未找到 HTTPS 配置"
  fi
  
  # 測試 HTTPS 訪問
  echo ""
  echo "測試 HTTPS 訪問..."
  sleep 2
  HTTPS_TEST=$(curl -s -o /dev/null -w "%{http_code}" -k https://localhost/ 2>&1 || echo "000")
  if [ "$HTTPS_TEST" = "200" ] || [ "$HTTPS_TEST" = "301" ] || [ "$HTTPS_TEST" = "302" ]; then
    echo "✅ HTTPS 本地測試成功（狀態碼: $HTTPS_TEST）"
  else
    echo "⚠️  HTTPS 本地測試失敗（狀態碼: $HTTPS_TEST）"
  fi
else
  echo "⚠️  跳過 HTTPS 驗證（證書未配置）"
fi
echo ""

echo "=========================================="
echo "配置完成"
echo "=========================================="
echo ""

if [ "$HTTPS_OK" = "true" ]; then
  echo "✅ HTTPS 已成功配置！"
  echo ""
  echo "現在可以使用以下方式訪問網站："
  echo "  HTTP:  http://${DOMAIN}"
  echo "  HTTPS: https://${DOMAIN}"
else
  echo "⚠️  HTTPS 配置未完成"
  echo ""
  echo "當前可以使用 HTTP 訪問："
  echo "  http://${DOMAIN}"
  echo ""
  if [ "$DNS_OK" != "true" ]; then
    echo "請先修復 DNS 配置："
    echo "  1. 登錄您的域名管理後台"
    echo "  2. 添加或修改 A 記錄："
    echo "     名稱: @ 或 aikz"
    echo "     值: $SERVER_IP"
    echo "  3. 等待 DNS 傳播（通常幾分鐘到幾小時）"
    echo "  4. 然後重新運行此腳本"
  else
    echo "DNS 解析正確，但證書獲取失敗。"
    echo "請檢查："
    echo "  1. 端口 80 是否對外開放"
    echo "  2. 防火牆是否允許 Let's Encrypt 驗證"
    echo "  3. 域名是否被封鎖"
    echo ""
    echo "暫時可以使用 HTTP 訪問：http://${DOMAIN}"
  fi
fi
