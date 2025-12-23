#!/bin/bash

# 停止端口 3000 上的進程並重新啟動 saas-demo
# 使用方法: bash scripts/server/kill_port_3000_and_restart_saas_demo.sh

set -e

echo "=========================================="
echo "🔧 停止端口 3000 衝突並重啟 saas-demo"
echo "時間: $(date)"
echo "=========================================="
echo ""

PORT=3000
SAAS_DEMO_DIR="/home/ubuntu/telegram-ai-system/saas-demo"

# 1. 查找並停止端口 3000 上的所有進程
echo "1. 查找端口 3000 上的進程..."
echo "----------------------------------------"

PIDS=""
if command -v lsof >/dev/null 2>&1; then
  PIDS=$(lsof -ti :$PORT 2>/dev/null || echo "")
elif command -v ss >/dev/null 2>&1; then
  PIDS=$(ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP "pid=\K\d+" | head -1 || echo "")
fi

if [ -n "$PIDS" ]; then
  echo "發現佔用端口 $PORT 的進程:"
  for PID in $PIDS; do
    if [ -n "$PID" ] && [ "$PID" != "N/A" ]; then
      PROCESS_INFO=$(ps -p $PID -o pid,cmd= 2>/dev/null || echo "無法獲取")
      echo "  PID $PID: $PROCESS_INFO"
    fi
  done
  echo ""
  
  echo "停止這些進程..."
  for PID in $PIDS; do
    if [ -n "$PID" ] && [ "$PID" != "N/A" ]; then
      echo "  停止 PID $PID..."
      sudo kill -9 $PID 2>/dev/null || true
    fi
  done
  
  sleep 2
  
  # 再次檢查
  REMAINING_PIDS=$(lsof -ti :$PORT 2>/dev/null || ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP "pid=\K\d+" | head -1 || echo "")
  if [ -n "$REMAINING_PIDS" ]; then
    echo "⚠️  仍有進程佔用，強制停止..."
    for PID in $REMAINING_PIDS; do
      sudo kill -9 $PID 2>/dev/null || true
    done
    sleep 2
  fi
  
  if ! lsof -i :$PORT >/dev/null 2>&1 && ! ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "✅ 端口 $PORT 已釋放"
  else
    echo "❌ 端口 $PORT 仍被佔用"
    exit 1
  fi
else
  echo "✅ 端口 $PORT 未被佔用"
fi
echo ""

# 2. 停止 PM2 中的 saas-demo
echo "2. 停止 PM2 中的 saas-demo..."
echo "----------------------------------------"
if command -v pm2 >/dev/null 2>&1; then
  pm2 delete saas-demo 2>/dev/null || true
  sleep 1
  echo "✅ 已停止 PM2 中的 saas-demo"
else
  echo "⚠️  PM2 未安裝"
  exit 1
fi
echo ""

# 3. 檢查 saas-demo 目錄和構建
echo "3. 檢查 saas-demo..."
echo "----------------------------------------"
if [ ! -d "$SAAS_DEMO_DIR" ]; then
  echo "❌ saas-demo 目錄不存在: $SAAS_DEMO_DIR"
  exit 1
fi

cd "$SAAS_DEMO_DIR" || exit 1

if [ ! -f "package.json" ]; then
  echo "❌ package.json 不存在"
  exit 1
fi

# 檢查構建
if [ ! -d ".next" ]; then
  echo "⚠️  .next 目錄不存在，需要構建"
  echo "構建 saas-demo..."
  npm run build || {
    echo "❌ 構建失敗"
    exit 1
  }
  echo "✅ 構建完成"
else
  echo "✅ .next 目錄存在"
fi
echo ""

# 4. 確保日誌目錄存在
mkdir -p "$SAAS_DEMO_DIR/logs"
echo "✅ 日誌目錄已準備"
echo ""

# 5. 啟動 saas-demo
echo "4. 啟動 saas-demo..."
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

# 6. 等待服務啟動
echo "5. 等待服務啟動..."
echo "----------------------------------------"
sleep 10

# 7. 驗證
echo "6. 驗證服務..."
echo "----------------------------------------"
if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
  echo "✅ 端口 $PORT 正在監聽"
  
  # 檢查是否是 saas-demo
  LISTENING_PID=$(lsof -ti :$PORT 2>/dev/null | head -1 || ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP "pid=\K\d+" | head -1 || echo "")
  if [ -n "$LISTENING_PID" ]; then
    PROCESS_CWD=$(readlink -f /proc/$LISTENING_PID/cwd 2>/dev/null || echo "")
    if echo "$PROCESS_CWD" | grep -q "saas-demo"; then
      echo "✅ 確認是 saas-demo 在監聽端口 $PORT"
    else
      echo "⚠️  端口 $PORT 上的進程工作目錄: $PROCESS_CWD"
    fi
  fi
  
  # 測試 HTTP 響應
  sleep 2
  HTTP_CODE=$(curl -s -o /tmp/saas_demo_test.html -w "%{http_code}" http://127.0.0.1:$PORT 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    echo "✅ HTTP 響應正常 (HTTP $HTTP_CODE)"
    
    # 檢查內容
    CONTENT=$(head -c 500 /tmp/saas_demo_test.html 2>/dev/null || echo "")
    if echo "$CONTENT" | grep -qi "智控王\|Smart Control King"; then
      echo "❌ 返回的內容仍包含 'AI 智控王'"
      echo "   這可能是構建問題或緩存問題"
    elif echo "$CONTENT" | grep -qi "登錄\|login\|聊天 AI"; then
      echo "✅ 返回的內容正確（包含登錄相關文字）"
    else
      echo "⚠️  無法確定返回的內容"
    fi
  else
    echo "⚠️  HTTP 響應異常 (HTTP $HTTP_CODE)"
  fi
  
  rm -f /tmp/saas_demo_test.html
else
  echo "❌ 端口 $PORT 未在監聽"
  echo "查看 PM2 日誌："
  pm2 logs saas-demo --lines 30 --nostream 2>/dev/null || true
  exit 1
fi

echo ""
echo "=========================================="
echo "✅ 修復完成！"
echo "時間: $(date)"
echo "=========================================="
echo ""
echo "訪問地址: https://aikz.usdt2026.cc"
echo ""
echo "如果瀏覽器仍顯示錯誤頁面，請："
echo "1. 強制刷新 (Ctrl+F5)"
echo "2. 清除瀏覽器緩存"
echo "3. 使用無痕模式訪問"
