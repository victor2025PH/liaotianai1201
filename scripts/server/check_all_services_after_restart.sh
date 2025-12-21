#!/bin/bash

# 檢查服務器重啟後所有服務的狀態
# 使用方法: bash scripts/server/check_all_services_after_restart.sh

set -e

echo "=========================================="
echo "🔍 檢查服務器重啟後所有服務狀態"
echo "時間: $(date)"
echo "=========================================="
echo ""

# 1. 檢查 Nginx
echo "1. 檢查 Nginx 服務..."
echo "----------------------------------------"
if systemctl is-active --quiet nginx; then
  echo "✅ Nginx 正在運行"
  NGINX_STATUS="running"
else
  echo "❌ Nginx 未運行"
  NGINX_STATUS="stopped"
fi

# 檢查 Nginx 監聽的端口
if [ "$NGINX_STATUS" = "running" ]; then
  if lsof -i :80 >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":80 "; then
    echo "✅ 端口 80 正在監聽"
  else
    echo "⚠️  端口 80 未監聽"
  fi
  
  if lsof -i :443 >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":443 "; then
    echo "✅ 端口 443 正在監聽"
  else
    echo "⚠️  端口 443 未監聽"
  fi
fi
echo ""

# 2. 檢查 PM2 服務
echo "2. 檢查 PM2 服務..."
echo "----------------------------------------"
if command -v pm2 >/dev/null 2>&1; then
  echo "✅ PM2 已安裝"
  
  # 檢查 PM2 守護進程
  if pm2 ping >/dev/null 2>&1; then
    echo "✅ PM2 守護進程正在運行"
  else
    echo "⚠️  PM2 守護進程未運行，嘗試啟動..."
    pm2 resurrect 2>/dev/null || pm2 startup systemd -u ubuntu --hp /home/ubuntu || true
  fi
  
  # 列出所有 PM2 進程
  echo ""
  echo "PM2 進程列表："
  pm2 list || echo "無法獲取 PM2 列表"
else
  echo "❌ PM2 未安裝"
fi
echo ""

# 3. 檢查各個前端服務
echo "3. 檢查前端服務..."
echo "----------------------------------------"

declare -A SERVICES=(
  ["saas-demo"]="3000"
  ["tgmini-frontend"]="3001"
  ["hongbao-frontend"]="3002"
  ["aizkw-frontend"]="3003"
)

for SERVICE_NAME in "${!SERVICES[@]}"; do
  PORT="${SERVICES[$SERVICE_NAME]}"
  echo "檢查 $SERVICE_NAME (端口 $PORT)..."
  
  # 檢查 PM2 狀態
  PM2_STATUS=$(pm2 list 2>/dev/null | grep "$SERVICE_NAME" || echo "")
  if [ -n "$PM2_STATUS" ]; then
    if echo "$PM2_STATUS" | grep -q "online"; then
      echo "  ✅ PM2 狀態: online"
    elif echo "$PM2_STATUS" | grep -q "errored\|stopped"; then
      echo "  ❌ PM2 狀態: $(echo "$PM2_STATUS" | awk '{print $10}')"
    else
      echo "  ⚠️  PM2 狀態: 未知"
    fi
  else
    echo "  ⚠️  未在 PM2 中找到"
  fi
  
  # 檢查端口
  if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "  ✅ 端口 $PORT 正在監聽"
    
    # 測試 HTTP 響應
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
      echo "  ✅ HTTP 響應正常 (HTTP $HTTP_CODE)"
    else
      echo "  ⚠️  HTTP 響應異常 (HTTP $HTTP_CODE)"
    fi
  else
    echo "  ❌ 端口 $PORT 未監聽"
  fi
  echo ""
done

# 4. 檢查後端服務
echo "4. 檢查後端服務..."
echo "----------------------------------------"
BACKEND_PORT=8000
if lsof -i :$BACKEND_PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$BACKEND_PORT "; then
  echo "✅ 後端端口 $BACKEND_PORT 正在監聽"
  
  # 檢查 PM2 中的 backend
  BACKEND_STATUS=$(pm2 list 2>/dev/null | grep "backend" || echo "")
  if [ -n "$BACKEND_STATUS" ]; then
    if echo "$BACKEND_STATUS" | grep -q "online"; then
      echo "✅ Backend 在 PM2 中狀態: online"
    else
      echo "⚠️  Backend 在 PM2 中狀態異常"
    fi
  fi
else
  echo "❌ 後端端口 $BACKEND_PORT 未監聽"
fi
echo ""

# 5. 檢查域名配置
echo "5. 檢查域名配置..."
echo "----------------------------------------"
DOMAINS=("tgmini.usdt2026.cc" "hongbao.usdt2026.cc" "aikz.usdt2026.cc" "aizkw.usdt2026.cc")

for DOMAIN in "${DOMAINS[@]}"; do
  NGINX_CONFIG="/etc/nginx/sites-available/$DOMAIN"
  NGINX_ENABLED="/etc/nginx/sites-enabled/$DOMAIN"
  
  if [ -f "$NGINX_CONFIG" ]; then
    echo "✅ $DOMAIN 配置文件存在"
    if [ -L "$NGINX_ENABLED" ]; then
      echo "  ✅ 已啟用"
    else
      echo "  ⚠️  未啟用"
    fi
  else
    echo "⚠️  $DOMAIN 配置文件不存在"
  fi
done
echo ""

# 6. 總結和修復建議
echo "=========================================="
echo "📊 診斷總結"
echo "=========================================="
echo ""

if [ "$NGINX_STATUS" != "running" ]; then
  echo "❌ Nginx 未運行"
  echo "   修復: sudo systemctl start nginx"
  echo ""
fi

# 檢查是否有 errored 的服務
ERRORED_SERVICES=$(pm2 list 2>/dev/null | grep "errored" || echo "")
if [ -n "$ERRORED_SERVICES" ]; then
  echo "❌ 發現 errored 的服務："
  echo "$ERRORED_SERVICES"
  echo ""
  echo "   修復步驟："
  echo "   1. 查看日誌: pm2 logs <service-name>"
  echo "   2. 重啟服務: pm2 restart <service-name>"
  echo "   3. 如果仍然失敗，運行完整修復腳本"
  echo ""
fi

echo "如果所有服務都正常，但網頁仍無法訪問，請檢查："
echo "1. 防火牆設置"
echo "2. 域名 DNS 配置"
echo "3. SSL 證書是否過期"
echo "4. 服務器網絡連接"
