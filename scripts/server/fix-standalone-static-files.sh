#!/bin/bash
# 修復 Next.js standalone 模式的靜態文件問題

echo "=========================================="
echo "修復 Next.js Standalone 靜態文件問題"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_DIR" || exit 1

# 1. 檢查目錄結構
echo "[1/5] 檢查目錄結構..."
echo "----------------------------------------"
cd saas-demo

if [ -d ".next/static" ]; then
  STATIC_COUNT=$(find .next/static -type f | wc -l)
  echo "✅ .next/static 存在（包含 $STATIC_COUNT 個文件）"
else
  echo "❌ .next/static 不存在，需要重新構建"
  exit 1
fi

if [ -d ".next/standalone" ]; then
  echo "✅ .next/standalone 存在"
  
  # 檢查是否需要複製靜態文件
  if [ ! -d ".next/standalone/.next/static" ]; then
    echo "⚠️  .next/standalone/.next/static 不存在"
    echo "創建目錄並複製靜態文件..."
    mkdir -p .next/standalone/.next
    cp -r .next/static .next/standalone/.next/static
    echo "✅ 靜態文件已複製到 standalone 目錄"
  else
    echo "✅ .next/standalone/.next/static 存在"
  fi
else
  echo "❌ .next/standalone 不存在"
  exit 1
fi
cd ..
echo ""

# 2. 更新 Nginx 配置 - 直接從文件系統提供靜態文件
echo "[2/5] 更新 Nginx 配置..."
echo "----------------------------------------"
NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

# 備份配置
sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

# 確定正確的靜態文件路徑
STATIC_PATH=""
if [ -d "saas-demo/.next/standalone/.next/static" ]; then
  STATIC_PATH="/home/ubuntu/telegram-ai-system/saas-demo/.next/standalone/.next/static/"
  echo "✅ 使用 standalone 目錄中的靜態文件"
elif [ -d "saas-demo/.next/static" ]; then
  STATIC_PATH="/home/ubuntu/telegram-ai-system/saas-demo/.next/static/"
  echo "⚠️  使用標準目錄中的靜態文件（standalone 目錄中沒有）"
else
  echo "❌ 找不到靜態文件目錄"
  exit 1
fi

# 使用 Python 來更新配置
sudo python3 << PYTHON_SCRIPT
import re

config_file = '/etc/nginx/sites-available/aikz.usdt2026.cc'
static_path = '${STATIC_PATH}'

with open(config_file, 'r') as f:
    content = f.read()

# 檢查是否已有 /next/static 的配置
if 'location /next/static/' in content:
    # 更新現有配置中的 alias 路徑
    pattern = r'(location /next/static/\s*\{[^}]*alias\s+)([^;]+)(;)'
    replacement = r'\1' + static_path + r'\3'
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        with open(config_file, 'w') as f:
            f.write(new_content)
        print(f"✅ 配置已更新 - 路徑已改為: {static_path}")
    else:
        # 嘗試另一種格式
        pattern2 = r'(location /next/static/\s*\{.*?alias\s+)([^\s;]+)(\s*;)'
        new_content2 = re.sub(pattern2, r'\1' + static_path + r'\3', content, flags=re.DOTALL)
        if new_content2 != content:
            with open(config_file, 'w') as f:
                f.write(new_content2)
            print(f"✅ 配置已更新 - 路徑已改為: {static_path}")
        else:
            print(f"⚠️  配置已存在但路徑可能不正確，請手動檢查")
            print(f"   應使用路徑: {static_path}")
else:
    # 添加新配置
    static_location = f'''    # Next.js 靜態文件 - 直接從文件系統提供（優先級最高）
    location /next/static/ {{
        alias {static_path};
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }}

'''
    
    # 在 location /next/ 或第一個 location 之前插入
    pattern = r'(    # (?:WebSocket|Next\.js|前端|location))'
    replacement = static_location + r'\1'
    new_content = re.sub(pattern, replacement, content, count=1)
    
    if new_content != content:
        with open(config_file, 'w') as f:
            f.write(new_content)
        print(f"✅ 配置已添加 - 路徑: {static_path}")
    else:
        # 如果上面失敗，在 server { 之後添加
        pattern2 = r'(server \{[^}]*?)'
        replacement2 = r'\1\n' + static_location
        new_content2 = re.sub(pattern2, replacement2, content, count=1)
        with open(config_file, 'w') as f:
            f.write(new_content2)
        print(f"✅ 配置已添加 - 路徑: {static_path}")
PYTHON_SCRIPT
echo ""

# 3. 確保目錄權限正確
echo "[3/5] 修復文件權限..."
echo "----------------------------------------"
sudo chown -R ubuntu:ubuntu "$PROJECT_DIR/saas-demo/.next"
echo "✅ 文件權限已修復"
echo ""

# 4. 測試 Nginx 配置
echo "[4/5] 測試 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t; then
  echo "✅ Nginx 配置語法正確"
else
  echo "❌ Nginx 配置語法錯誤"
  echo "恢復備份..."
  sudo cp "${NGINX_CONFIG}.backup."* "$NGINX_CONFIG" 2>/dev/null || true
  exit 1
fi
echo ""

# 5. 重載 Nginx
echo "[5/5] 重載 Nginx..."
echo "----------------------------------------"
sudo systemctl reload nginx
if [ $? -eq 0 ]; then
  echo "✅ Nginx 已重載"
else
  echo "⚠️  重載失敗，嘗試重啟..."
  sudo systemctl restart nginx
fi
echo ""

# 6. 驗證
echo "=========================================="
echo "驗證修復..."
echo "=========================================="
sleep 2

# 測試靜態文件訪問
STATIC_FILE=$(find saas-demo/.next/static -name "*.js" -type f | head -1)
if [ -n "$STATIC_FILE" ]; then
  RELATIVE_PATH=${STATIC_FILE#saas-demo/.next/static/}
  echo "測試靜態文件: /next/static/$RELATIVE_PATH"
  
  # 測試直接從文件系統訪問
  if [ -f "saas-demo/.next/static/$RELATIVE_PATH" ]; then
    echo "✅ 文件存在於文件系統"
  fi
  
  # 測試通過 Nginx 訪問
  STATIC_TEST=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: aikz.usdt2026.cc" "http://localhost/next/static/$RELATIVE_PATH" 2>&1)
  echo "通過 Nginx 訪問狀態碼: $STATIC_TEST"
  
  if [ "$STATIC_TEST" = "200" ]; then
    echo "✅ 靜態文件可以正常訪問！"
  else
    echo "⚠️  靜態文件訪問失敗（狀態碼: $STATIC_TEST）"
    echo "請檢查 Nginx 配置和文件路徑"
  fi
fi

echo ""
echo "=========================================="
echo "修復完成！"
echo "=========================================="
echo ""
echo "請執行以下步驟驗證："
echo "1. 清除瀏覽器緩存（Ctrl+Shift+Delete）或使用無痕模式"
echo "2. 訪問: https://aikz.usdt2026.cc/login"
echo "3. 檢查開發者工具控制台，應該不再有 404 錯誤"
echo ""
echo "如果問題仍然存在："
echo "  - 查看 Nginx 錯誤日誌: sudo tail -50 /var/log/nginx/error.log"
echo "  - 查看 Nginx 訪問日誌: sudo tail -50 /var/log/nginx/access.log | grep next/static"
