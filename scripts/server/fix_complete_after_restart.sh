#!/bin/bash

# 完整修復服務器重啟後的所有問題
# 使用方法: sudo bash scripts/server/fix_complete_after_restart.sh

set -e

echo "=========================================="
echo "🔧 完整修復服務器重啟後的所有問題"
echo "時間: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"

# 1. 停止所有佔用端口 3000 的進程
echo "1. 停止端口 3000 上的所有進程..."
echo "----------------------------------------"
PORT=3000

if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
  echo "發現佔用端口 $PORT 的進程："
  PIDS=$(lsof -ti :$PORT 2>/dev/null || ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP "pid=\K\d+" || echo "")
  
  for PID in $PIDS; do
    if [ -n "$PID" ] && [ "$PID" != "N/A" ]; then
      PROCESS_INFO=$(ps -p $PID -o pid,cmd= 2>/dev/null || echo "無法獲取")
      echo "  PID $PID: $PROCESS_INFO"
      sudo kill -9 $PID 2>/dev/null || true
    fi
  done
  
  sleep 2
  
  # 再次檢查
  if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "⚠️  仍有進程佔用，強制停止..."
    sudo lsof -ti :$PORT 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
    sleep 2
  fi
fi

if ! lsof -i :$PORT >/dev/null 2>&1 && ! ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
  echo "✅ 端口 $PORT 已釋放"
else
  echo "❌ 端口 $PORT 仍被佔用"
fi
echo ""

# 2. 啟用所有域名的 Nginx 配置
echo "2. 啟用所有域名的 Nginx 配置..."
echo "----------------------------------------"
DOMAINS=("tgmini.usdt2026.cc" "hongbao.usdt2026.cc" "aikz.usdt2026.cc" "aizkw.usdt2026.cc")

for DOMAIN in "${DOMAINS[@]}"; do
  NGINX_CONFIG="/etc/nginx/sites-available/$DOMAIN"
  NGINX_ENABLED="/etc/nginx/sites-enabled/$DOMAIN"
  
  if [ -f "$NGINX_CONFIG" ]; then
    if [ ! -L "$NGINX_ENABLED" ]; then
      echo "啟用 $DOMAIN..."
      sudo ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"
      echo "  ✅ 已啟用"
    else
      echo "  ✅ $DOMAIN 已啟用"
    fi
  else
    echo "  ⚠️  $DOMAIN 配置文件不存在"
  fi
done
echo ""

# 3. 測試並重啟 Nginx
echo "3. 測試並重啟 Nginx..."
echo "----------------------------------------"
if sudo nginx -t 2>&1 | grep -q "test is successful"; then
  echo "✅ Nginx 配置測試通過"
  
  # 重啟 Nginx
  sudo systemctl restart nginx
  sleep 3
  
  if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 已重啟"
    
    # 檢查端口
    if lsof -i :80 >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":80 "; then
      echo "✅ 端口 80 正在監聽"
    else
      echo "⚠️  端口 80 未監聽，檢查 Nginx 配置..."
      sudo systemctl status nginx | head -20 || true
    fi
    
    if lsof -i :443 >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":443 "; then
      echo "✅ 端口 443 正在監聽"
    else
      echo "⚠️  端口 443 未監聽（可能是沒有 HTTPS 配置）"
    fi
  else
    echo "❌ Nginx 重啟失敗"
    sudo systemctl status nginx | head -30 || true
  fi
else
  echo "❌ Nginx 配置測試失敗"
  sudo nginx -t
  exit 1
fi
echo ""

# 4. 停止並重新啟動 saas-demo
echo "4. 重新啟動 saas-demo..."
echo "----------------------------------------"
SAAS_DEMO_DIR="$PROJECT_ROOT/saas-demo"

# 停止 PM2 中的 saas-demo
pm2 delete saas-demo 2>/dev/null || true
sleep 2

# 確保目錄存在
if [ ! -d "$SAAS_DEMO_DIR" ]; then
  echo "❌ saas-demo 目錄不存在: $SAAS_DEMO_DIR"
  exit 1
fi

cd "$SAAS_DEMO_DIR" || exit 1

# 檢查構建
if [ ! -d ".next" ]; then
  echo "構建 saas-demo..."
  npm run build || {
    echo "⚠️  構建失敗，但繼續嘗試啟動..."
  }
fi

# 確保日誌目錄存在
mkdir -p "$SAAS_DEMO_DIR/logs"

# 啟動 saas-demo
echo "啟動 saas-demo..."
pm2 start npm \
  --name saas-demo \
  --cwd "$SAAS_DEMO_DIR" \
  --error "$SAAS_DEMO_DIR/logs/saas-demo-error.log" \
  --output "$SAAS_DEMO_DIR/logs/saas-demo-out.log" \
  --merge-logs \
  --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
  -- start || {
  echo "⚠️  saas-demo 啟動失敗，查看日誌："
  pm2 logs saas-demo --lines 20 --nostream 2>/dev/null || true
}

pm2 save || true
echo ""

# 5. 等待服務啟動
echo "5. 等待服務啟動..."
echo "----------------------------------------"
sleep 10

# 6. 驗證所有服務
echo "6. 驗證所有服務..."
echo "----------------------------------------"

# 檢查 Nginx
if systemctl is-active --quiet nginx; then
  echo "✅ Nginx 運行中"
  if lsof -i :80 >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":80 "; then
    echo "✅ 端口 80 正在監聽"
  fi
  if lsof -i :443 >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":443 "; then
    echo "✅ 端口 443 正在監聽"
  fi
else
  echo "❌ Nginx 未運行"
fi

# 檢查 PM2 進程
echo ""
echo "PM2 進程狀態："
pm2 list || echo "無法獲取 PM2 列表"

# 檢查關鍵端口
echo ""
echo "檢查關鍵端口："
PORTS=(3000 3001 3002 3003 8000)
for PORT in "${PORTS[@]}"; do
  if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "✅ 端口 $PORT 正在監聽"
  else
    echo "⚠️  端口 $PORT 未監聽"
  fi
done

# 檢查 saas-demo 狀態
echo ""
SAAS_DEMO_STATUS=$(pm2 list 2>/dev/null | grep "saas-demo" || echo "")
if [ -n "$SAAS_DEMO_STATUS" ]; then
  if echo "$SAAS_DEMO_STATUS" | grep -q "online"; then
    echo "✅ saas-demo 狀態: online"
    
    # 測試 HTTP 響應
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
      echo "✅ saas-demo HTTP 響應正常 (HTTP $HTTP_CODE)"
    else
      echo "⚠️  saas-demo HTTP 響應異常 (HTTP $HTTP_CODE)"
    fi
  else
    echo "❌ saas-demo 狀態異常"
    echo "$SAAS_DEMO_STATUS"
    echo ""
    echo "查看日誌："
    pm2 logs saas-demo --lines 30 --nostream 2>/dev/null || true
  fi
else
  echo "❌ saas-demo 未在 PM2 中"
fi

echo ""
echo "=========================================="
echo "✅ 修復完成！"
echo "時間: $(date)"
echo "=========================================="
echo ""
echo "如果網頁仍然無法訪問，請檢查："
echo "1. 防火牆: sudo ufw status"
echo "2. Nginx 錯誤日誌: sudo tail -f /var/log/nginx/error.log"
echo "3. PM2 日誌: pm2 logs"
echo "4. 域名 DNS 配置"
