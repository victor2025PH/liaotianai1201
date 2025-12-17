#!/bin/bash
# 驗證並診斷靜態文件修復

echo "=========================================="
echo "驗證靜態文件配置"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_DIR" || exit 1

# 1. 檢查實際的 Nginx 配置
echo "[1/6] 檢查 Nginx 配置..."
echo "----------------------------------------"
NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
echo "當前 /next/static/ 配置："
sudo grep -A 5 "location /next/static/" "$NGINX_CONFIG" | head -10
echo ""

# 2. 檢查文件是否存在
echo "[2/6] 檢查靜態文件是否存在..."
echo "----------------------------------------"
cd saas-demo

# 檢查標準目錄
if [ -d ".next/static" ]; then
  STATIC_COUNT=$(find .next/static -type f | wc -l)
  echo "✅ .next/static 存在（$STATIC_COUNT 個文件）"
  
  # 找到一個實際的文件
  SAMPLE_FILE=$(find .next/static -name "*.js" -type f | head -1)
  if [ -n "$SAMPLE_FILE" ]; then
    echo "   示例文件: $SAMPLE_FILE"
    echo "   文件大小: $(ls -lh "$SAMPLE_FILE" | awk '{print $5}')"
    echo "   文件權限: $(ls -l "$SAMPLE_FILE" | awk '{print $1}')"
  fi
else
  echo "❌ .next/static 不存在"
fi

# 檢查 standalone 目錄
if [ -d ".next/standalone/.next/static" ]; then
  STANDALONE_COUNT=$(find .next/standalone/.next/static -type f | wc -l)
  echo "✅ .next/standalone/.next/static 存在（$STANDALONE_COUNT 個文件）"
  
  # 找到一個實際的文件
  SAMPLE_STANDALONE=$(find .next/standalone/.next/static -name "*.js" -type f | head -1)
  if [ -n "$SAMPLE_STANDALONE" ]; then
    echo "   示例文件: $SAMPLE_STANDALONE"
    echo "   文件大小: $(ls -lh "$SAMPLE_STANDALONE" | awk '{print $5}')"
    echo "   文件權限: $(ls -l "$SAMPLE_STANDALONE" | awk '{print $1}')"
  fi
else
  echo "❌ .next/standalone/.next/static 不存在"
fi
cd ..
echo ""

# 3. 測試文件訪問權限
echo "[3/6] 測試文件訪問權限..."
echo "----------------------------------------"
if [ -n "$SAMPLE_STANDALONE" ]; then
  STANDALONE_FULL_PATH="$PROJECT_DIR/saas-demo/$SAMPLE_STANDALONE"
  echo "測試文件: $STANDALONE_FULL_PATH"
  
  if sudo test -r "$STANDALONE_FULL_PATH"; then
    echo "✅ Nginx 可以讀取此文件"
  else
    echo "❌ Nginx 無法讀取此文件"
    echo "   修復權限..."
    sudo chown -R ubuntu:ubuntu "$PROJECT_DIR/saas-demo/.next"
    sudo chmod -R 755 "$PROJECT_DIR/saas-demo/.next"
  fi
elif [ -n "$SAMPLE_FILE" ]; then
  STATIC_FULL_PATH="$PROJECT_DIR/saas-demo/$SAMPLE_FILE"
  echo "測試文件: $STATIC_FULL_PATH"
  
  if sudo test -r "$STATIC_FULL_PATH"; then
    echo "✅ Nginx 可以讀取此文件"
  else
    echo "❌ Nginx 無法讀取此文件"
  fi
fi
echo ""

# 4. 測試通過 Nginx 訪問
echo "[4/6] 測試通過 Nginx 訪問靜態文件..."
echo "----------------------------------------"
if [ -n "$SAMPLE_STANDALONE" ]; then
  RELATIVE_PATH=${SAMPLE_STANDALONE#.next/standalone/.next/static/}
  TEST_URL="/next/static/$RELATIVE_PATH"
elif [ -n "$SAMPLE_FILE" ]; then
  RELATIVE_PATH=${SAMPLE_FILE#.next/static/}
  TEST_URL="/next/static/$RELATIVE_PATH"
fi

if [ -n "$TEST_URL" ]; then
  echo "測試 URL: $TEST_URL"
  echo "使用 curl 測試..."
  
  # 測試本地訪問
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: aikz.usdt2026.cc" "http://localhost$TEST_URL" 2>&1)
  echo "HTTP 狀態碼: $HTTP_CODE"
  
  if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ 靜態文件可以通過 Nginx 訪問！"
  else
    echo "❌ 靜態文件無法訪問（狀態碼: $HTTP_CODE）"
    echo ""
    echo "詳細響應："
    curl -v -H "Host: aikz.usdt2026.cc" "http://localhost$TEST_URL" 2>&1 | head -20
  fi
fi
echo ""

# 5. 檢查 Nginx 錯誤日誌
echo "[5/6] 檢查 Nginx 錯誤日誌..."
echo "----------------------------------------"
echo "最近的錯誤（如果有）："
sudo tail -20 /var/log/nginx/error.log | grep -i "static\|404\|alias" | tail -10 || echo "  無相關錯誤"
echo ""

# 6. 檢查訪問日誌
echo "[6/6] 檢查訪問日誌..."
echo "----------------------------------------"
echo "最近的 /next/static 訪問記錄："
sudo tail -50 /var/log/nginx/access.log | grep "/next/static" | tail -5 || echo "  無訪問記錄"
echo ""

echo "=========================================="
echo "診斷完成"
echo "=========================================="
echo ""
echo "如果仍然無法訪問，請檢查："
echo "1. Nginx 配置中的 alias 路徑是否完全正確"
echo "2. 文件權限是否允許 Nginx 讀取"
echo "3. SELinux 或 AppArmor 是否阻止訪問（如果啟用）"
echo ""
echo "手動檢查命令："
echo "  sudo cat $NGINX_CONFIG | grep -A 5 'location /next/static'"
echo "  ls -la $PROJECT_DIR/saas-demo/.next/standalone/.next/static/ | head -10"
