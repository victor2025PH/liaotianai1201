#!/bin/bash
# 最終修復：使用實際存在的靜態文件目錄

echo "=========================================="
echo "最終修復靜態文件路徑"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

# 1. 確定實際存在的靜態文件目錄
echo "[1/4] 查找實際的靜態文件目錄..."
echo "----------------------------------------"
cd "$PROJECT_DIR/saas-demo" || exit 1

STATIC_PATH=""
if [ -d ".next/standalone/.next/static" ] && [ "$(find .next/standalone/.next/static -type f | wc -l)" -gt 0 ]; then
  STATIC_PATH="/home/ubuntu/telegram-ai-system/saas-demo/.next/standalone/.next/static/"
  echo "✅ 找到 standalone 目錄中的靜態文件"
elif [ -d ".next/static" ] && [ "$(find .next/static -type f | wc -l)" -gt 0 ]; then
  STATIC_PATH="/home/ubuntu/telegram-ai-system/saas-demo/.next/static/"
  echo "✅ 找到標準目錄中的靜態文件"
  FILE_COUNT=$(find .next/static -type f | wc -l)
  echo "   文件數量: $FILE_COUNT"
else
  echo "❌ 找不到靜態文件目錄"
  exit 1
fi

echo "將使用路徑: $STATIC_PATH"
cd "$PROJECT_DIR"
echo ""

# 2. 備份當前配置
echo "[2/4] 備份當前配置..."
echo "----------------------------------------"
sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ 配置已備份"
echo ""

# 3. 更新 Nginx 配置
echo "[3/4] 更新 Nginx 配置..."
echo "----------------------------------------"

# 使用 sed 更新 alias 路徑
sudo sed -i "s|alias /home/ubuntu/telegram-ai-system/saas-demo/.next/standalone/.next/static/|alias $STATIC_PATH|g" "$NGINX_CONFIG"
sudo sed -i "s|alias /home/ubuntu/telegram-ai-system/saas-demo/.next/static/|alias $STATIC_PATH|g" "$NGINX_CONFIG"

# 驗證更新
if sudo grep -q "alias $STATIC_PATH" "$NGINX_CONFIG"; then
  echo "✅ 配置已更新"
  echo "當前配置："
  sudo grep -A 3 "location /next/static/" "$NGINX_CONFIG" | head -5
else
  echo "⚠️  配置更新可能失敗，檢查配置..."
  # 如果 sed 失敗，使用 Python 更新
  sudo python3 << PYTHON_SCRIPT
import re

config_file = '/etc/nginx/sites-available/aikz.usdt2026.cc'
static_path = '${STATIC_PATH}'

with open(config_file, 'r') as f:
    content = f.read()

# 更新或添加配置
pattern = r'location /next/static/.*?access_log off;\s*\}'
new_location = f'''    location /next/static/ {{
        alias {static_path};
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }}'''

if 'location /next/static/' in content:
    content = re.sub(pattern, new_location, content, flags=re.DOTALL)
    print("✅ 配置已更新（使用 Python）")
else:
    # 添加新配置
    pattern2 = r'(    # (?:WebSocket|Next\.js|前端|location /))'
    content = re.sub(pattern2, new_location + '\n\n\\1', content, count=1)
    print("✅ 配置已添加（使用 Python）")

with open(config_file, 'w') as f:
    f.write(content)
PYTHON_SCRIPT
fi
echo ""

# 4. 測試並重載
echo "[4/4] 測試並重載 Nginx..."
echo "----------------------------------------"
if sudo nginx -t; then
  echo "✅ 配置語法正確"
  echo "重載 Nginx..."
  sudo systemctl reload nginx
  echo "✅ Nginx 已重載"
else
  echo "❌ 配置語法錯誤"
  echo "恢復備份..."
  sudo cp "${NGINX_CONFIG}.backup."* "$NGINX_CONFIG" 2>/dev/null || true
  exit 1
fi
echo ""

# 5. 驗證
echo "=========================================="
echo "驗證修復..."
echo "=========================================="
sleep 2

# 找到一個實際的文件
if [ -d "$PROJECT_DIR/saas-demo/.next/static" ]; then
  SAMPLE_FILE=$(find "$PROJECT_DIR/saas-demo/.next/static" -name "*.js" -type f | head -1)
  if [ -n "$SAMPLE_FILE" ]; then
    RELATIVE_PATH=${SAMPLE_FILE#*/.next/static/}
    TEST_URL="/next/static/$RELATIVE_PATH"
    
    echo "測試 URL: $TEST_URL"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: aikz.usdt2026.cc" "http://localhost$TEST_URL" 2>&1)
    echo "HTTP 狀態碼: $HTTP_CODE"
    
    if [ "$HTTP_CODE" = "200" ]; then
      echo "✅ 靜態文件可以正常訪問！"
    elif [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
      echo "⚠️  返回重定向（$HTTP_CODE），請使用 HTTPS 測試"
      HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k "https://localhost$TEST_URL" 2>&1)
      if [ "$HTTPS_CODE" = "200" ]; then
        echo "✅ 通過 HTTPS 可以正常訪問！"
      else
        echo "⚠️  HTTPS 訪問狀態碼: $HTTPS_CODE"
      fi
    else
      echo "⚠️  狀態碼: $HTTP_CODE，請檢查配置和文件路徑"
    fi
  fi
fi

echo ""
echo "=========================================="
echo "修復完成！"
echo "=========================================="
echo ""
echo "當前配置的靜態文件路徑："
sudo grep "alias.*static" "$NGINX_CONFIG" | head -1
echo ""
echo "請清除瀏覽器緩存並重新訪問網站測試："
echo "  https://aikz.usdt2026.cc/login"
