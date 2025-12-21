#!/bin/bash

# 修復服務器重啟後所有服務
# 使用方法: bash scripts/server/fix_all_services_after_restart.sh

set -e

echo "=========================================="
echo "🔧 修復服務器重啟後所有服務"
echo "時間: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"

# 1. 啟動 Nginx
echo "1. 啟動 Nginx..."
echo "----------------------------------------"
if ! systemctl is-active --quiet nginx; then
  echo "啟動 Nginx..."
  sudo systemctl start nginx
  sleep 2
fi

if systemctl is-active --quiet nginx; then
  echo "✅ Nginx 已啟動"
  
  # 測試配置
  if sudo nginx -t 2>&1 | grep -q "test is successful"; then
    echo "✅ Nginx 配置正確"
  else
    echo "⚠️  Nginx 配置有問題，但服務已啟動"
    sudo nginx -t || true
  fi
else
  echo "❌ Nginx 啟動失敗"
  sudo systemctl status nginx | head -20 || true
fi
echo ""

# 2. 啟動 PM2 守護進程
echo "2. 啟動 PM2 守護進程..."
echo "----------------------------------------"
if command -v pm2 >/dev/null 2>&1; then
  if ! pm2 ping >/dev/null 2>&1; then
    echo "啟動 PM2 守護進程..."
    pm2 resurrect 2>/dev/null || {
      echo "嘗試設置 PM2 開機自啟..."
      pm2 startup systemd -u ubuntu --hp /home/ubuntu || true
    }
  fi
  echo "✅ PM2 守護進程已運行"
else
  echo "❌ PM2 未安裝"
  exit 1
fi
echo ""

# 3. 恢復 PM2 進程
echo "3. 恢復 PM2 進程..."
echo "----------------------------------------"
pm2 resurrect 2>/dev/null || {
  echo "PM2 進程列表為空，需要手動啟動服務"
}

# 檢查並啟動各個服務
declare -A SERVICES=(
  ["backend"]="8000"
  ["frontend"]="3001"
  ["saas-demo"]="3000"
  ["tgmini-frontend"]="3001"
  ["hongbao-frontend"]="3002"
  ["aizkw-frontend"]="3003"
)

for SERVICE_NAME in "${!SERVICES[@]}"; do
  PORT="${SERVICES[$SERVICE_NAME]}"
  
  # 檢查服務是否在 PM2 中
  SERVICE_EXISTS=$(pm2 list 2>/dev/null | grep "$SERVICE_NAME" || echo "")
  
  if [ -z "$SERVICE_EXISTS" ]; then
    echo "⚠️  $SERVICE_NAME 未在 PM2 中，跳過..."
    continue
  fi
  
  # 檢查服務狀態
  SERVICE_STATUS=$(pm2 list 2>/dev/null | grep "$SERVICE_NAME" | awk '{print $10}' || echo "")
  
  if [ "$SERVICE_STATUS" = "online" ]; then
    echo "✅ $SERVICE_NAME 已在運行"
  elif [ "$SERVICE_STATUS" = "errored" ] || [ "$SERVICE_STATUS" = "stopped" ]; then
    echo "重啟 $SERVICE_NAME..."
    pm2 restart "$SERVICE_NAME" || {
      echo "⚠️  $SERVICE_NAME 重啟失敗，查看日誌："
      pm2 logs "$SERVICE_NAME" --lines 10 --nostream 2>/dev/null || true
    }
  fi
done

pm2 save || true
echo ""

# 4. 特別處理 saas-demo（因為之前有問題）
echo "4. 特別處理 saas-demo..."
echo "----------------------------------------"
SAAS_DEMO_DIR="$PROJECT_ROOT/saas-demo"

# 檢查端口 3000 是否被其他服務佔用
if lsof -i :3000 >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":3000 "; then
  LISTENING_PID=$(lsof -ti :3000 2>/dev/null | head -1 || ss -tlnp 2>/dev/null | grep ":3000 " | grep -oP "pid=\K\d+" | head -1 || echo "")
  if [ -n "$LISTENING_PID" ]; then
    PROCESS_CWD=$(readlink -f /proc/$LISTENING_PID/cwd 2>/dev/null || echo "")
    if ! echo "$PROCESS_CWD" | grep -q "saas-demo"; then
      echo "⚠️  端口 3000 被其他服務佔用 (PID: $LISTENING_PID)"
      echo "   停止該進程..."
      sudo kill -9 $LISTENING_PID 2>/dev/null || true
      sleep 2
    fi
  fi
fi

# 檢查 saas-demo 狀態
SAAS_DEMO_STATUS=$(pm2 list 2>/dev/null | grep "saas-demo" || echo "")
if [ -n "$SAAS_DEMO_STATUS" ]; then
  if echo "$SAAS_DEMO_STATUS" | grep -q "errored"; then
    echo "saas-demo 狀態異常，重新啟動..."
    pm2 delete saas-demo 2>/dev/null || true
    
    # 確保目錄和構建存在
    if [ -d "$SAAS_DEMO_DIR" ] && [ -f "$SAAS_DEMO_DIR/package.json" ]; then
      cd "$SAAS_DEMO_DIR" || exit 1
      
      # 檢查構建
      if [ ! -d ".next" ]; then
        echo "構建 saas-demo..."
        npm run build || {
          echo "⚠️  構建失敗，但繼續嘗試啟動..."
        }
      fi
      
      # 啟動
      mkdir -p "$SAAS_DEMO_DIR/logs"
      pm2 start npm \
        --name saas-demo \
        --cwd "$SAAS_DEMO_DIR" \
        --error "$SAAS_DEMO_DIR/logs/saas-demo-error.log" \
        --output "$SAAS_DEMO_DIR/logs/saas-demo-out.log" \
        --merge-logs \
        --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
        -- start || {
        echo "⚠️  saas-demo 啟動失敗"
        pm2 logs saas-demo --lines 20 --nostream 2>/dev/null || true
      }
    fi
  fi
fi

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
PORTS=(80 443 3000 3001 3002 3003 8000)
for PORT in "${PORTS[@]}"; do
  if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "✅ 端口 $PORT 正在監聽"
  else
    echo "⚠️  端口 $PORT 未監聽"
  fi
done

echo ""
echo "=========================================="
echo "✅ 修復完成！"
echo "時間: $(date)"
echo "=========================================="
echo ""
echo "如果網頁仍然無法訪問，請："
echo "1. 檢查防火牆: sudo ufw status"
echo "2. 檢查域名 DNS 配置"
echo "3. 查看 Nginx 錯誤日誌: sudo tail -f /var/log/nginx/error.log"
echo "4. 查看 PM2 日誌: pm2 logs"
