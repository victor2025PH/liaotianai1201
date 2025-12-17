#!/bin/bash
# 更新 Nginx 配置以修復 Next.js 靜態文件問題

echo "=========================================="
echo "更新 Nginx 配置以修復靜態文件問題"
echo "=========================================="
echo ""

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
BACKUP_CONFIG="${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

# 1. 備份當前配置
echo "[1/4] 備份當前配置..."
echo "----------------------------------------"
if [ -f "$NGINX_CONFIG" ]; then
  sudo cp "$NGINX_CONFIG" "$BACKUP_CONFIG"
  echo "✅ 配置已備份到: $BACKUP_CONFIG"
else
  echo "❌ 配置文件不存在: $NGINX_CONFIG"
  exit 1
fi
echo ""

# 2. 更新配置
echo "[2/4] 更新 Nginx 配置..."
echo "----------------------------------------"

# 讀取當前配置並檢查是否已有 /next/ 配置
if sudo grep -q "location /next/" "$NGINX_CONFIG"; then
  echo "✅ 配置中已包含 /next/ 處理，跳過更新"
  UPDATE_NEEDED=false
else
  echo "⚠️  配置中缺少 /next/ 處理，正在添加..."
  
  # 使用 sed 在 location /api/v1/notifications/ws 之後添加 /next/ 配置
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
  
  if [ $? -eq 0 ]; then
    echo "✅ 配置已更新"
    UPDATE_NEEDED=true
  else
    echo "❌ 配置更新失敗，使用完整替換方式..."
    
    # 如果 sed 失敗，使用完整替換
    sudo tee "$NGINX_CONFIG" > /dev/null << 'EOF'
server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级更高）
    location /api/v1/notifications/ws {
        proxy_pass http://127.0.0.1:8000/api/v1/notifications/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_buffering off;
    }

    # Next.js 靜態文件（優先處理，在 location / 之前）
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

    # 前端
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # /api/workers/ -> /api/v1/workers（带末尾斜杠）
    location = /api/workers/ {
        proxy_pass http://127.0.0.1:8000/api/v1/workers;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # /api/workers/xxx -> /api/v1/workers/xxx
    location ~ ^/api/workers/(.+)$ {
        proxy_pass http://127.0.0.1:8000/api/v1/workers/$1;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
    }
}
EOF
    UPDATE_NEEDED=true
  fi
fi
echo ""

# 3. 測試配置
echo "[3/4] 測試 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t; then
  echo "✅ 配置語法正確"
else
  echo "❌ 配置語法錯誤，恢復備份..."
  sudo cp "$BACKUP_CONFIG" "$NGINX_CONFIG"
  echo "已恢復備份配置"
  exit 1
fi
echo ""

# 4. 重載 Nginx
echo "[4/4] 重載 Nginx..."
echo "----------------------------------------"
if sudo systemctl reload nginx; then
  echo "✅ Nginx 已重載"
else
  echo "⚠️  重載失敗，嘗試重啟..."
  sudo systemctl restart nginx
  if [ $? -eq 0 ]; then
    echo "✅ Nginx 已重啟"
  else
    echo "❌ Nginx 重啟失敗"
    exit 1
  fi
fi
echo ""

echo "=========================================="
echo "配置更新完成！"
echo "=========================================="
echo ""
echo "現在 Nginx 應該可以正確處理 Next.js 靜態文件了。"
echo ""
echo "測試步驟："
echo "1. 清除瀏覽器緩存或使用無痕模式"
echo "2. 訪問: https://aikz.usdt2026.cc/login"
echo "3. 檢查開發者工具控制台是否還有 404 錯誤"
echo ""
echo "如果問題仍然存在，請執行診斷腳本："
echo "  bash scripts/server/fix-nextjs-static-files.sh"
