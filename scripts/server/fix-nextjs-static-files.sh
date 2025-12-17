#!/bin/bash
# 修復 Next.js 靜態文件 404 問題

echo "=========================================="
echo "修復 Next.js 靜態文件 404 問題"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_DIR" || exit 1

# 1. 檢查 .next 目錄結構
echo "[1/6] 檢查 .next 目錄結構..."
echo "----------------------------------------"
cd saas-demo

if [ ! -d ".next" ]; then
  echo "❌ .next 目錄不存在，需要重新構建"
  echo "執行: cd saas-demo && npm run build"
  exit 1
fi

echo "✅ .next 目錄存在"
echo ""
echo "檢查關鍵目錄："

if [ -d ".next/static" ]; then
  echo "  ✅ .next/static 存在"
  STATIC_COUNT=$(find .next/static -type f | wc -l)
  echo "     包含 $STATIC_COUNT 個文件"
else
  echo "  ❌ .next/static 不存在"
fi

if [ -d ".next/standalone" ]; then
  echo "  ✅ .next/standalone 存在"
else
  echo "  ⚠️  .next/standalone 不存在（可能是非 standalone 模式）"
fi

if [ -d ".next/standalone/.next/static" ]; then
  echo "  ✅ .next/standalone/.next/static 存在"
  STANDALONE_STATIC_COUNT=$(find .next/standalone/.next/static -type f | wc -l)
  echo "     包含 $STANDALONE_STATIC_COUNT 個文件"
else
  echo "  ⚠️  .next/standalone/.next/static 不存在"
fi

if [ -f ".next/standalone/server.js" ]; then
  echo "  ✅ server.js 存在"
else
  SERVER_JS=$(find .next -name "server.js" -type f | head -1)
  if [ -n "$SERVER_JS" ]; then
    echo "  ✅ server.js 存在: $SERVER_JS"
  else
    echo "  ❌ server.js 不存在"
  fi
fi
echo ""

# 2. 檢查前端服務配置
echo "[2/6] 檢查前端服務配置..."
echo "----------------------------------------"
SERVICE_FILE="/etc/systemd/system/liaotian-frontend.service"
if [ -f "$SERVICE_FILE" ]; then
  echo "服務配置文件內容："
  sudo cat "$SERVICE_FILE" | grep -E "WorkingDirectory|ExecStart" | head -5
else
  echo "❌ 服務配置文件不存在"
fi
echo ""

# 3. 檢查當前運行中的前端進程
echo "[3/6] 檢查前端服務運行情況..."
echo "----------------------------------------"
if sudo systemctl is-active --quiet liaotian-frontend; then
  echo "✅ 前端服務正在運行"
  FRONTEND_PID=$(sudo systemctl show -p MainPID --value liaotian-frontend)
  echo "   PID: $FRONTEND_PID"
  
  # 檢查進程的工作目錄
  if [ -n "$FRONTEND_PID" ] && [ "$FRONTEND_PID" != "0" ]; then
    WORK_DIR=$(sudo pwdx $FRONTEND_PID 2>/dev/null | awk '{print $2}' || echo "")
    echo "   工作目錄: $WORK_DIR"
  fi
else
  echo "❌ 前端服務未運行"
fi
echo ""

# 4. 測試靜態文件訪問
echo "[4/6] 測試靜態文件訪問..."
echo "----------------------------------------"
# 嘗試找到一個實際存在的 JS 文件
JS_FILE=$(find .next -name "*.js" -path "*/static/chunks/*" | head -1)
if [ -n "$JS_FILE" ]; then
  echo "找到示例 JS 文件: $JS_FILE"
  # 計算相對路徑
  if [[ "$JS_FILE" == .next/standalone* ]]; then
    RELATIVE_PATH=${JS_FILE#.next/standalone/}
  else
    RELATIVE_PATH=${JS_FILE#.next/}
  fi
  echo "相對路徑: $RELATIVE_PATH"
  
  # 測試直接訪問
  echo "測試直接訪問: http://localhost:3000/next/${RELATIVE_PATH#.next/}"
  DIRECT_TEST=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/next/${RELATIVE_PATH#.next/}" 2>&1)
  echo "   狀態碼: $DIRECT_TEST"
else
  echo "⚠️  未找到示例 JS 文件"
fi
echo ""

# 5. 檢查 Nginx 配置中的靜態文件處理
echo "[5/6] 檢查 Nginx 配置..."
echo "----------------------------------------"
NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
if [ -f "$NGINX_CONFIG" ]; then
  if grep -q "/next/static" "$NGINX_CONFIG"; then
    echo "✅ Nginx 配置中有 /next/static 處理"
    echo "相關配置："
    sudo grep -A 5 "/next/static" "$NGINX_CONFIG"
  else
    echo "⚠️  Nginx 配置中沒有 /next/static 的專門處理"
    echo "這可能是問題所在"
  fi
else
  echo "❌ Nginx 配置文件不存在"
fi
echo ""

# 6. 修復方案
echo "[6/6] 生成修復方案..."
echo "----------------------------------------"

cd "$PROJECT_DIR"

# 檢查是否是 standalone 模式的問題
if [ -d "saas-demo/.next/standalone/.next/static" ]; then
  echo "檢測到 standalone 模式，靜態文件在 standalone 目錄中"
  echo ""
  echo "修復方案：需要更新 Nginx 配置以正確處理靜態文件"
  
  # 生成更新的 Nginx 配置建議
  cat > /tmp/nginx-static-fix.conf << 'EOF'
# 在 server 塊中添加以下 location 塊（在 location / 之前）：

    # Next.js 靜態文件
    location /next/ {
        alias /home/ubuntu/telegram-ai-system/saas-demo/.next/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Next.js standalone 靜態文件（如果使用 standalone 模式）
    location /_next/static/ {
        alias /home/ubuntu/telegram-ai-system/saas-demo/.next/standalone/.next/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
EOF

  echo "建議的 Nginx 配置已保存到: /tmp/nginx-static-fix.conf"
  echo "查看內容: cat /tmp/nginx-static-fix.conf"
  
else
  echo "檢查標準模式的靜態文件配置"
fi

echo ""
echo "=========================================="
echo "診斷完成"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 檢查前端服務的工作目錄是否正確"
echo "2. 確保 .next/static 目錄存在並包含文件"
echo "3. 更新 Nginx 配置以正確處理 /next/static 路徑"
echo "4. 重啟前端服務和 Nginx"
