#!/bin/bash
# 創建並啟用 Nginx 配置

echo "=========================================="
echo "創建 Nginx 配置"
echo "=========================================="
echo ""

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"

# 1. 創建配置文件
echo "[1/5] 創建 Nginx 配置文件..."
echo "----------------------------------------"

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

    # Next.js 靜態文件 - 直接從文件系統提供（優先級最高）
    location /next/static/ {
        alias /home/ubuntu/telegram-ai-system/saas-demo/.next/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Next.js 其他 /next/ 路徑（通過代理）
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

if [ $? -eq 0 ]; then
  echo "✅ 配置文件已創建: $NGINX_CONFIG"
else
  echo "❌ 配置文件創建失敗"
  exit 1
fi
echo ""

# 2. 啟用站點
echo "[2/5] 啟用站點..."
echo "----------------------------------------"
if [ -L "$NGINX_ENABLED" ]; then
  echo "✅ 站點已啟用（符號鏈接已存在）"
else
  sudo ln -s "$NGINX_CONFIG" "$NGINX_ENABLED"
  if [ $? -eq 0 ]; then
    echo "✅ 站點已啟用: $NGINX_ENABLED"
  else
    echo "❌ 站點啟用失敗"
    exit 1
  fi
fi
echo ""

# 3. 測試配置
echo "[3/5] 測試 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t; then
  echo "✅ Nginx 配置語法正確"
else
  echo "❌ Nginx 配置有錯誤"
  exit 1
fi
echo ""

# 4. 重載 Nginx
echo "[4/5] 重載 Nginx..."
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

# 5. 驗證端口監聽
echo "[5/5] 驗證端口監聽..."
echo "----------------------------------------"
sleep 2
if sudo ss -tlnp | grep -q ":80"; then
  echo "✅ 端口 80 (HTTP) 正在監聽"
else
  echo "❌ 端口 80 未監聽"
fi

if sudo ss -tlnp | grep -q ":3000"; then
  echo "✅ 端口 3000 (前端) 正在監聽"
else
  echo "❌ 端口 3000 未監聽"
fi

if sudo ss -tlnp | grep -q ":8000"; then
  echo "✅ 端口 8000 (後端) 正在監聽"
else
  echo "❌ 端口 8000 未監聽"
fi
echo ""

echo "=========================================="
echo "配置完成！"
echo "=========================================="
echo ""
echo "現在可以使用 HTTP 訪問網站："
echo "  http://aikz.usdt2026.cc"
echo ""
echo "要配置 HTTPS，請執行："
echo "  sudo certbot --nginx -d aikz.usdt2026.cc"
echo ""
echo "注意：如果 Certbot 驗證失敗，可能是："
echo "  1. 域名 DNS 未正確解析到此服務器"
echo "  2. 防火牆阻止了端口 80"
echo "  3. 域名已申請過證書但證書已失效"
echo ""
echo "如果 Certbot 驗證失敗，可以："
echo "  1. 檢查 DNS: nslookup aikz.usdt2026.cc"
echo "  2. 檢查域名是否指向此服務器 IP"
echo "  3. 確保端口 80 對外開放"
