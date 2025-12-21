#!/bin/bash

# 修復端口 3000 返回錯誤頁面的問題
# 使用方法: bash scripts/server/fix_port_3000_issue.sh

set -e

echo "=========================================="
echo "🔍 診斷並修復端口 3000 問題"
echo "時間: $(date)"
echo "=========================================="
echo ""

PORT=3000
SAAS_DEMO_DIR="/home/ubuntu/telegram-ai-system/saas-demo"

# 1. 檢查端口 3000 上運行的進程
echo "1. 檢查端口 3000 上運行的進程..."
echo "----------------------------------------"

if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
  echo "✅ 端口 $PORT 正在監聽"
  
  # 獲取進程信息
  if command -v lsof >/dev/null 2>&1; then
    PROCESS_INFO=$(lsof -i :$PORT 2>/dev/null | grep LISTEN | head -1)
    PID=$(echo "$PROCESS_INFO" | awk '{print $2}')
    COMMAND=$(echo "$PROCESS_INFO" | awk '{print $1}')
    if [ -n "$PID" ]; then
      echo "   進程 ID: $PID"
      echo "   命令: $COMMAND"
      echo "   完整命令: $(ps -p $PID -o cmd= 2>/dev/null || echo '無法獲取')"
      
      # 檢查進程的工作目錄
      if [ -n "$PID" ]; then
        CWD=$(pwdx $PID 2>/dev/null || readlink -f /proc/$PID/cwd 2>/dev/null || echo "無法獲取")
        echo "   工作目錄: $CWD"
        
        # 檢查是否是 saas-demo
        if echo "$CWD" | grep -q "saas-demo"; then
          echo "   ✅ 進程在 saas-demo 目錄中"
        else
          echo "   ⚠️  進程不在 saas-demo 目錄中，可能是其他服務"
        fi
      fi
    fi
  else
    PROCESS_INFO=$(ss -tlnp 2>/dev/null | grep ":$PORT " | head -1)
    echo "   進程信息: $PROCESS_INFO"
  fi
else
  echo "❌ 端口 $PORT 未監聽"
fi
echo ""

# 2. 測試端口 3000 返回的內容
echo "2. 測試端口 3000 返回的內容..."
echo "----------------------------------------"
HTTP_CODE=$(curl -s -o /tmp/port_3000_response.html -w "%{http_code}" http://127.0.0.1:$PORT 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
  echo "✅ HTTP 響應正常 (HTTP $HTTP_CODE)"
  
  # 檢查返回的內容
  CONTENT=$(head -c 500 /tmp/port_3000_response.html 2>/dev/null || echo "")
  if echo "$CONTENT" | grep -qi "智控王\|Smart Control King"; then
    echo "❌ 返回的內容包含 'AI 智控王'，說明端口 3000 上運行的是錯誤的服務"
    echo ""
    echo "   返回的內容預覽："
    echo "$CONTENT" | head -20
    echo ""
    echo "   這說明端口 3000 上運行的不是 saas-demo，而是 aizkw 或其他服務"
  elif echo "$CONTENT" | grep -qi "登錄\|login\|聊天 AI\|saas-demo"; then
    echo "✅ 返回的內容正確（包含登錄相關文字）"
  else
    echo "⚠️  無法確定返回的內容是否正確"
    echo "   內容預覽："
    echo "$CONTENT" | head -20
  fi
else
  echo "⚠️  HTTP 響應異常 (HTTP $HTTP_CODE)"
fi
echo ""

# 3. 檢查 PM2 中的 saas-demo
echo "3. 檢查 PM2 中的 saas-demo..."
echo "----------------------------------------"
if command -v pm2 >/dev/null 2>&1; then
  SAAS_DEMO_STATUS=$(pm2 list | grep saas-demo || echo "")
  if [ -n "$SAAS_DEMO_STATUS" ]; then
    echo "PM2 進程狀態:"
    echo "$SAAS_DEMO_STATUS"
    
    # 檢查狀態
    if echo "$SAAS_DEMO_STATUS" | grep -q "online"; then
      echo "✅ saas-demo 在 PM2 中顯示為 online"
      
      # 獲取 PM2 進程的 PID
      PM2_PID=$(echo "$SAAS_DEMO_STATUS" | awk '{print $6}')
      if [ -n "$PM2_PID" ] && [ "$PM2_PID" != "N/A" ] && [ "$PM2_PID" != "pid" ]; then
        echo "   PM2 進程 PID: $PM2_PID"
        
        # 檢查這個 PID 是否在監聽端口 3000
        if lsof -i :$PORT 2>/dev/null | grep -q "$PM2_PID"; then
          echo "   ✅ PM2 進程正在監聽端口 $PORT"
        else
          echo "   ⚠️  PM2 進程未監聽端口 $PORT，可能啟動失敗"
        fi
      fi
    elif echo "$SAAS_DEMO_STATUS" | grep -q "errored\|stopped"; then
      echo "❌ saas-demo 在 PM2 中狀態異常"
      echo "查看日誌："
      pm2 logs saas-demo --lines 20 --nostream 2>/dev/null || true
    fi
  else
    echo "❌ 未找到 saas-demo PM2 進程"
  fi
else
  echo "⚠️  PM2 未安裝"
fi
echo ""

# 4. 檢查是否有其他服務佔用端口 3000
echo "4. 檢查是否有其他服務佔用端口 3000..."
echo "----------------------------------------"
# 檢查 aizkw 是否在運行
if pm2 list | grep -q "aizkw"; then
  AIZKW_STATUS=$(pm2 list | grep aizkw)
  AIZKW_PORT=$(echo "$AIZKW_STATUS" | awk '{print $NF}' | grep -oP "\d+" | head -1 || echo "")
  if [ "$AIZKW_PORT" = "3003" ]; then
    echo "✅ aizkw 運行在端口 3003（正確）"
  else
    echo "⚠️  aizkw 可能運行在其他端口"
  fi
fi

# 檢查是否有其他 node 進程在端口 3000
ALL_NODE_PROCESSES=$(lsof -i :$PORT 2>/dev/null | grep node || ss -tlnp 2>/dev/null | grep ":$PORT " | grep node || echo "")
if [ -n "$ALL_NODE_PROCESSES" ]; then
  echo "發現的 Node.js 進程："
  echo "$ALL_NODE_PROCESSES"
fi
echo ""

# 5. 提供修復建議
echo "5. 修復建議..."
echo "----------------------------------------"

if echo "$CONTENT" | grep -qi "智控王\|Smart Control King"; then
  echo "❌ 問題確認：端口 3000 返回的是 'AI 智控王' 頁面"
  echo ""
  echo "修復步驟："
  echo ""
  echo "1. 停止端口 3000 上的錯誤服務："
  if [ -n "$PID" ]; then
    echo "   sudo kill -9 $PID"
  else
    echo "   sudo lsof -ti :$PORT | xargs sudo kill -9"
  fi
  echo ""
  echo "2. 確保 saas-demo 正確構建："
  echo "   cd $SAAS_DEMO_DIR"
  echo "   rm -rf .next"
  echo "   npm run build"
  echo ""
  echo "3. 使用 PM2 正確啟動 saas-demo："
  echo "   cd $SAAS_DEMO_DIR"
  echo "   pm2 delete saas-demo"
  echo "   pm2 start npm --name saas-demo --cwd $SAAS_DEMO_DIR -- start"
  echo "   pm2 save"
  echo ""
  echo "4. 等待幾秒後驗證："
  echo "   curl http://127.0.0.1:3000 | head -c 500"
  echo "   應該不包含 '智控王' 或 'Smart Control King'"
  echo ""
  echo "5. 如果仍然有問題，運行完整修復："
  echo "   sudo bash scripts/server/fix_aikz_complete.sh"
else
  echo "✅ 端口 3000 返回的內容看起來正確"
fi

# 清理臨時文件
rm -f /tmp/port_3000_response.html

echo ""
echo "=========================================="
echo "診斷完成"
echo "時間: $(date)"
echo "=========================================="
