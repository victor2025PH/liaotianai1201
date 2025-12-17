#!/bin/bash
# 完整修復 Next.js 靜態文件 404 問題

echo "=========================================="
echo "完整修復 Next.js 靜態文件 404 問題"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_DIR" || exit 1

# 1. 處理 git 問題
echo "[1/7] 處理 Git 並拉取最新代碼..."
echo "----------------------------------------"
if [ -n "$(git status --porcelain)" ]; then
  echo "⚠️  發現本地更改，自動丟棄..."
  git checkout -- .
fi
git fetch origin main
git reset --hard origin/main
echo "✅ 代碼已更新"
echo ""

# 2. 檢查 .next 目錄結構
echo "[2/7] 檢查 .next 目錄結構..."
echo "----------------------------------------"
cd saas-demo

if [ ! -d ".next" ]; then
  echo "❌ .next 目錄不存在，需要重新構建"
  echo "這會在步驟 3 中處理"
else
  echo "✅ .next 目錄存在"
  
  # 檢查靜態文件位置
  if [ -d ".next/static" ]; then
    STATIC_COUNT=$(find .next/static -type f | wc -l)
    echo "  ✅ .next/static 存在（包含 $STATIC_COUNT 個文件）"
  fi
  
  if [ -d ".next/standalone/.next/static" ]; then
    STANDALONE_COUNT=$(find .next/standalone/.next/static -type f | wc -l)
    echo "  ✅ .next/standalone/.next/static 存在（包含 $STANDALONE_COUNT 個文件）"
  fi
fi
cd ..
echo ""

# 3. 重新構建前端（如果需要）
echo "[3/7] 檢查並重新構建前端..."
echo "----------------------------------------"
cd saas-demo

# 檢查是否有靜態文件
NEEDS_BUILD=false
if [ ! -d ".next/static" ] && [ ! -d ".next/standalone/.next/static" ]; then
  echo "⚠️  未找到靜態文件，需要重新構建"
  NEEDS_BUILD=true
fi

# 檢查構建是否過舊（超過 1 天）
if [ -d ".next" ]; then
  BUILD_AGE=$(find .next -name "*.js" -type f -mtime +1 | head -1)
  if [ -n "$BUILD_AGE" ]; then
    echo "⚠️  構建文件較舊，建議重新構建"
    NEEDS_BUILD=true
  fi
fi

if [ "$NEEDS_BUILD" = "true" ]; then
  echo "開始重新構建..."
  echo "安裝依賴..."
  npm install --prefer-offline --no-audit --no-fund
  
  echo "構建前端項目..."
  export NODE_ENV=production
  export NODE_OPTIONS="--max-old-space-size=4096"
  npm run build
  
  if [ $? -eq 0 ]; then
    echo "✅ 前端構建完成"
  else
    echo "❌ 前端構建失敗"
    exit 1
  fi
else
  echo "✅ 構建文件存在且較新，跳過構建"
fi
cd ..
echo ""

# 4. 更新 Nginx 配置
echo "[4/7] 更新 Nginx 配置..."
echo "----------------------------------------"
NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

if [ ! -f "$NGINX_CONFIG" ]; then
  echo "❌ Nginx 配置文件不存在，創建它..."
  chmod +x scripts/server/create-nginx-config.sh
  sudo bash scripts/server/create-nginx-config.sh
fi

# 檢查是否已有 /next/ 配置
if ! sudo grep -q "location /next/" "$NGINX_CONFIG"; then
  echo "⚠️  配置中缺少 /next/ 處理，正在添加..."
  
  # 使用 Python 來正確插入配置
  sudo python3 << 'PYTHON_SCRIPT'
import re

config_file = '/etc/nginx/sites-available/aikz.usdt2026.cc'

with open(config_file, 'r') as f:
    content = f.read()

# 檢查是否已有 /next/ 配置
if 'location /next/' not in content:
    # 在 location /api/v1/notifications/ws 之後添加 /next/ 配置
    next_location = '''    # Next.js 靜態文件（優先處理，在 location / 之前）
    location /next/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

'''
    
    # 找到 location /api/v1/notifications/ws 的結束位置
    pattern = r'(location /api/v1/notifications/ws \{.*?\n    \})\n'
    replacement = r'\1\n' + next_location
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(config_file, 'w') as f:
        f.write(content)
    print("✅ 配置已更新")
else:
    print("✅ 配置已包含 /next/ 處理")
PYTHON_SCRIPT
else
  echo "✅ 配置已包含 /next/ 處理"
fi
echo ""

# 5. 測試 Nginx 配置
echo "[5/7] 測試 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t; then
  echo "✅ Nginx 配置語法正確"
else
  echo "❌ Nginx 配置語法錯誤"
  exit 1
fi
echo ""

# 6. 重載 Nginx 和重啟前端服務
echo "[6/7] 重載 Nginx 和重啟前端服務..."
echo "----------------------------------------"
sudo systemctl reload nginx
if [ $? -ne 0 ]; then
  echo "⚠️  重載失敗，嘗試重啟..."
  sudo systemctl restart nginx
fi

sudo systemctl restart liaotian-frontend
sleep 3
echo "✅ 服務已重啟"
echo ""

# 7. 驗證
echo "[7/7] 驗證修復..."
echo "----------------------------------------"
sleep 3

echo "檢查端口監聽:"
if sudo ss -tlnp | grep -q ":443"; then
  echo "  ✅ 端口 443 (HTTPS) 正在監聽"
fi

if sudo ss -tlnp | grep -q ":3000"; then
  echo "  ✅ 端口 3000 (前端) 正在監聽"
fi

echo ""
echo "測試前端服務:"
FRONTEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ 2>&1)
echo "  前端直接訪問: $FRONTEND_TEST"

echo ""
echo "測試 Nginx 代理:"
NGINX_TEST=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: aikz.usdt2026.cc" http://localhost/ 2>&1)
echo "  通過 Nginx 訪問: $NGINX_TEST"

# 嘗試找到一個實際的靜態文件進行測試
STATIC_FILE=$(find saas-demo/.next -name "*.js" -path "*/static/chunks/*" | head -1)
if [ -n "$STATIC_FILE" ]; then
  RELATIVE_PATH=${STATIC_FILE#saas-demo/.next/}
  echo ""
  echo "測試靜態文件訪問:"
  echo "  文件: $RELATIVE_PATH"
  STATIC_TEST=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: aikz.usdt2026.cc" "http://localhost/next/static/${RELATIVE_PATH#static/}" 2>&1)
  echo "  狀態碼: $STATIC_TEST"
  if [ "$STATIC_TEST" = "200" ]; then
    echo "  ✅ 靜態文件可以訪問！"
  else
    echo "  ⚠️  靜態文件訪問失敗，可能需要檢查路徑映射"
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
echo "3. 檢查開發者工具控制台"
echo ""
echo "如果仍有問題，請查看："
echo "  - Nginx 錯誤日誌: sudo tail -50 /var/log/nginx/error.log"
echo "  - 前端服務日誌: sudo journalctl -u liaotian-frontend -n 50 --no-pager"
