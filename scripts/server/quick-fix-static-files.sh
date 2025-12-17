#!/bin/bash
# 快速修復 Next.js 靜態文件問題（包含自動處理 git 問題）

echo "=========================================="
echo "快速修復 Next.js 靜態文件問題"
echo "=========================================="
echo ""

# 1. 處理 git 問題並拉取代碼
echo "[1/4] 處理 Git 並拉取最新代碼..."
echo "----------------------------------------"
cd /home/ubuntu/telegram-ai-system || exit 1

# 如果有未提交的更改，先處理
if [ -n "$(git status --porcelain)" ]; then
  echo "⚠️  發現未提交的更改，自動丟棄以使用遠程版本..."
  git checkout -- .
fi

# 拉取代碼
git pull origin main
if [ $? -ne 0 ]; then
  echo "❌ 拉取代碼失敗，嘗試強制重置..."
  git fetch origin main
  git reset --hard origin/main
fi

echo "✅ 代碼已更新"
echo ""

# 2. 更新 Nginx 配置
echo "[2/4] 更新 Nginx 配置..."
echo "----------------------------------------"
chmod +x scripts/server/update-nginx-for-static-files.sh
if [ -f "scripts/server/update-nginx-for-static-files.sh" ]; then
  sudo bash scripts/server/update-nginx-for-static-files.sh
else
  echo "⚠️  更新腳本不存在，手動更新配置..."
  
  # 手動更新 Nginx 配置
  NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
  
  if [ -f "$NGINX_CONFIG" ]; then
    # 檢查是否已有 /next/ 配置
    if ! sudo grep -q "location /next/" "$NGINX_CONFIG"; then
      echo "添加 /next/ 配置..."
      
      # 在 location /api/v1/notifications/ws 之後插入配置
      sudo sed -i '/location \/api\/v1\/notifications\/ws {/,/^    }/{
        /^    }/a\
\
    # Next.js 靜態文件（優先處理，在 location / 之前）\
    location /next/ {\
        proxy_pass http://127.0.0.1:3000;\
        proxy_http_version 1.1;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        expires 1y;\
        add_header Cache-Control "public, immutable";\
    }
      }' "$NGINX_CONFIG"
      
      # 測試配置
      if sudo nginx -t; then
        sudo systemctl reload nginx
        echo "✅ Nginx 配置已更新"
      else
        echo "❌ Nginx 配置語法錯誤"
      fi
    else
      echo "✅ Nginx 配置已包含 /next/ 處理"
    fi
  fi
fi
echo ""

# 3. 檢查前端服務
echo "[3/4] 檢查前端服務..."
echo "----------------------------------------"
if sudo systemctl is-active --quiet liaotian-frontend; then
  echo "✅ 前端服務正在運行"
  
  # 測試前端是否響應
  FRONTEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ 2>&1)
  if [ "$FRONTEND_TEST" = "200" ] || [ "$FRONTEND_TEST" = "304" ]; then
    echo "✅ 前端服務響應正常"
  else
    echo "⚠️  前端服務響應異常（狀態碼: $FRONTEND_TEST），嘗試重啟..."
    sudo systemctl restart liaotian-frontend
    sleep 3
  fi
else
  echo "❌ 前端服務未運行，啟動中..."
  sudo systemctl start liaotian-frontend
  sleep 3
fi
echo ""

# 4. 最終測試
echo "[4/4] 最終測試..."
echo "----------------------------------------"
sleep 2

echo "測試靜態文件訪問："
STATIC_TEST=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: aikz.usdt2026.cc" http://localhost/next/static/chunks/_app-xxx.js 2>&1 | head -1 || echo "000")
echo "  狀態碼: $STATIC_TEST"

echo ""
echo "測試主頁訪問："
HOME_TEST=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: aikz.usdt2026.cc" http://localhost/ 2>&1)
echo "  狀態碼: $HOME_TEST"
echo ""

echo "=========================================="
echo "修復完成！"
echo "=========================================="
echo ""
echo "請執行以下步驟驗證："
echo "1. 清除瀏覽器緩存或使用無痕模式"
echo "2. 訪問: https://aikz.usdt2026.cc/login"
echo "3. 檢查開發者工具控制台是否還有 404 錯誤"
echo ""
echo "如果問題仍然存在，請執行診斷："
echo "  bash scripts/server/fix-nextjs-static-files.sh"
