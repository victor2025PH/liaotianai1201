#!/bin/bash

# 修復 saas-demo 端口問題：停止錯誤服務並正確啟動 saas-demo
# 使用方法: bash scripts/server/fix_saas_demo_port.sh

set -e

echo "=========================================="
echo "🔧 修復 saas-demo 端口問題"
echo "時間: $(date)"
echo "=========================================="
echo ""

PORT=3000
SAAS_DEMO_DIR="/home/ubuntu/telegram-ai-system/saas-demo"

# 1. 檢查端口 3000 返回的內容
echo "1. 檢查端口 3000 當前狀態..."
echo "----------------------------------------"
HTTP_CODE=$(curl -s -o /tmp/current_response.html -w "%{http_code}" http://127.0.0.1:$PORT 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
  CONTENT=$(head -c 500 /tmp/current_response.html 2>/dev/null || echo "")
  if echo "$CONTENT" | grep -qi "智控王\|Smart Control King"; then
    echo "❌ 確認問題：端口 3000 返回的是 'AI 智控王' 頁面"
    NEED_FIX=true
  else
    echo "✅ 端口 3000 返回的內容正確"
    NEED_FIX=false
  fi
else
  echo "⚠️  端口 3000 未響應 (HTTP $HTTP_CODE)"
  NEED_FIX=true
fi
echo ""

if [ "$NEED_FIX" = "false" ]; then
  echo "✅ 端口 3000 已經正確，無需修復"
  rm -f /tmp/current_response.html
  exit 0
fi

# 2. 停止端口 3000 上的所有進程
echo "2. 停止端口 3000 上的所有進程..."
echo "----------------------------------------"
if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
  echo "找到佔用端口 $PORT 的進程，正在停止..."
  
  # 獲取所有佔用端口的進程 PID
  PIDS=$(lsof -ti :$PORT 2>/dev/null || ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP "pid=\K\d+" | head -1 || echo "")
  
  if [ -n "$PIDS" ]; then
    for PID in $PIDS; do
      if [ -n "$PID" ] && [ "$PID" != "N/A" ]; then
        echo "   停止進程 $PID..."
        sudo kill -9 $PID 2>/dev/null || true
      fi
    done
    sleep 2
  fi
  
  # 再次檢查
  if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "⚠️  仍有進程佔用端口，強制停止..."
    sudo lsof -ti :$PORT 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
    sleep 2
  fi
  
  if ! lsof -i :$PORT >/dev/null 2>&1 && ! ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "✅ 端口 $PORT 已釋放"
  else
    echo "⚠️  端口 $PORT 仍被佔用，但繼續執行..."
  fi
else
  echo "✅ 端口 $PORT 未被佔用"
fi
echo ""

# 3. 停止 PM2 中的 saas-demo（如果存在）
echo "3. 停止 PM2 中的 saas-demo..."
echo "----------------------------------------"
if command -v pm2 >/dev/null 2>&1; then
  pm2 delete saas-demo 2>/dev/null || true
  echo "✅ 已停止 PM2 中的 saas-demo"
else
  echo "⚠️  PM2 未安裝"
fi
echo ""

# 4. 檢查 saas-demo 目錄
echo "4. 檢查 saas-demo 目錄..."
echo "----------------------------------------"
if [ ! -d "$SAAS_DEMO_DIR" ]; then
  echo "❌ saas-demo 目錄不存在: $SAAS_DEMO_DIR"
  exit 1
fi
echo "✅ saas-demo 目錄存在"
echo ""

# 5. 進入 saas-demo 目錄並檢查構建
echo "5. 檢查並重新構建 saas-demo..."
echo "----------------------------------------"
cd "$SAAS_DEMO_DIR" || exit 1

if [ ! -f "package.json" ]; then
  echo "❌ package.json 不存在"
  exit 1
fi

# 檢查是否需要構建
if [ ! -d ".next" ]; then
  echo "⚠️  .next 目錄不存在，需要構建"
  NEED_BUILD=true
else
  # 檢查構建是否過舊或損壞
  BUILD_TIME=$(stat -c %Y .next 2>/dev/null || echo "0")
  CURRENT_TIME=$(date +%s)
  AGE=$((CURRENT_TIME - BUILD_TIME))
  
  if [ $AGE -gt 3600 ]; then
    echo "⚠️  構建時間超過 1 小時，建議重新構建"
    NEED_BUILD=true
  else
    echo "✅ .next 目錄存在"
    NEED_BUILD=false
  fi
fi

if [ "$NEED_BUILD" = "true" ]; then
  echo "重新構建 saas-demo..."
  rm -rf .next
  npm run build || {
    echo "❌ 構建失敗"
    exit 1
  }
  echo "✅ 構建完成"
else
  echo "使用現有構建"
fi
echo ""

# 6. 確保日誌目錄存在
echo "6. 準備啟動 saas-demo..."
echo "----------------------------------------"
mkdir -p "$SAAS_DEMO_DIR/logs"
echo "✅ 日誌目錄已準備"
echo ""

# 7. 使用 PM2 啟動 saas-demo
echo "7. 啟動 saas-demo..."
echo "----------------------------------------"
pm2 start npm \
  --name saas-demo \
  --cwd "$SAAS_DEMO_DIR" \
  --error "$SAAS_DEMO_DIR/logs/saas-demo-error.log" \
  --output "$SAAS_DEMO_DIR/logs/saas-demo-out.log" \
  --merge-logs \
  --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
  -- start || {
  echo "❌ PM2 啟動失敗"
  echo "查看錯誤："
  pm2 logs saas-demo --lines 20 --nostream 2>/dev/null || true
  exit 1
}

pm2 save || true
echo "✅ saas-demo 已啟動"
pm2 list | grep saas-demo || true
echo ""

# 8. 等待服務啟動
echo "8. 等待服務啟動..."
echo "----------------------------------------"
sleep 10

# 9. 驗證服務
echo "9. 驗證服務..."
echo "----------------------------------------"
if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
  echo "✅ 端口 $PORT 正在監聽"
  
  # 測試本地訪問
  sleep 2
  HTTP_CODE=$(curl -s -o /tmp/new_response.html -w "%{http_code}" http://127.0.0.1:$PORT 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    echo "✅ 本地訪問正常 (HTTP $HTTP_CODE)"
    
    # 檢查返回的內容
    NEW_CONTENT=$(head -c 500 /tmp/new_response.html 2>/dev/null || echo "")
    if echo "$NEW_CONTENT" | grep -qi "智控王\|Smart Control King"; then
      echo "❌ 返回的內容仍包含 'AI 智控王'"
      echo "   這可能是構建問題，請檢查："
      echo "   1. saas-demo 的構建輸出是否正確"
      echo "   2. 是否有其他服務仍在運行"
      echo ""
      echo "   查看 PM2 日誌："
      pm2 logs saas-demo --lines 30 --nostream 2>/dev/null || true
    elif echo "$NEW_CONTENT" | grep -qi "登錄\|login\|聊天 AI"; then
      echo "✅ 返回的內容正確（包含登錄相關文字）"
      echo ""
      echo "   內容預覽："
      echo "$NEW_CONTENT" | head -10
    else
      echo "⚠️  無法確定返回的內容是否正確"
      echo "   內容預覽："
      echo "$NEW_CONTENT" | head -10
    fi
  else
    echo "⚠️  本地訪問異常 (HTTP $HTTP_CODE)"
    pm2 logs saas-demo --lines 30 --nostream 2>/dev/null || true
  fi
else
  echo "❌ 端口 $PORT 未在監聽"
  echo "查看 PM2 日誌："
  pm2 logs saas-demo --lines 30 --nostream 2>/dev/null || true
  exit 1
fi

# 清理臨時文件
rm -f /tmp/current_response.html /tmp/new_response.html

echo ""
echo "=========================================="
echo "✅ 修復完成！"
echo "時間: $(date)"
echo "=========================================="
echo ""
echo "如果問題仍然存在，請運行："
echo "  bash scripts/server/fix_port_3000_issue.sh"
echo "  來診斷具體問題"
