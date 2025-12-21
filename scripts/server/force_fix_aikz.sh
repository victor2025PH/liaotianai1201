#!/bin/bash

# 強制修復 aikz.usdt2026.cc，確保指向 saas-demo (端口 3000)
# 使用方法: sudo bash scripts/server/force_fix_aikz.sh

set -e

echo "=========================================="
echo "🔧 強制修復 aikz.usdt2026.cc"
echo "時間: $(date)"
echo "=========================================="
echo ""

DOMAIN="aikz.usdt2026.cc"
PORT=3000
NGINX_CONFIG="/etc/nginx/sites-available/$DOMAIN"
NGINX_ENABLED="/etc/nginx/sites-enabled/$DOMAIN"

# 1. 停止可能運行在端口 3003 的 aizkw 服務（如果它佔用了 aikz 域名）
echo "1. 檢查並停止衝突服務..."
echo "----------------------------------------"

# 檢查端口 3003 是否有服務運行
if lsof -i :3003 >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":3003 "; then
  echo "⚠️  檢測到端口 3003 有服務運行（可能是 aizkw）"
  echo "   這不應該影響 aikz.usdt2026.cc，但我們會確保配置正確"
fi

# 確保端口 3000 有服務運行
if ! lsof -i :$PORT >/dev/null 2>&1 && ! ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
  echo "❌ 端口 $PORT 沒有服務運行"
  echo "   請先啟動 saas-demo:"
  echo "   cd /home/ubuntu/telegram-ai-system/saas-demo"
  echo "   pm2 start npm --name saas-demo --cwd /home/ubuntu/telegram-ai-system/saas-demo -- start"
  exit 1
fi
echo "✅ 端口 $PORT 正在監聽"
echo ""

# 2. 檢查 SSL 證書
echo "2. 檢查 SSL 證書..."
echo "----------------------------------------"
SSL_CERT=""
SSL_KEY=""

# 檢查標準路徑
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ] && [ -f "/etc/letsencrypt/live/$DOMAIN/privkey.pem" ]; then
  SSL_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
  SSL_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
  echo "✅ SSL 證書存在: $SSL_CERT"
else
  # 檢查帶後綴的證書
  MATCHING=$(find /etc/letsencrypt/live/ -name "${DOMAIN}*" -type d 2>/dev/null | head -1)
  if [ -n "$MATCHING" ] && [ -f "$MATCHING/fullchain.pem" ] && [ -f "$MATCHING/privkey.pem" ]; then
    SSL_CERT="$MATCHING/fullchain.pem"
    SSL_KEY="$MATCHING/privkey.pem"
    echo "✅ SSL 證書存在（帶後綴）: $SSL_CERT"
  else
    echo "❌ SSL 證書不存在"
    exit 1
  fi
fi
echo ""

# 3. 生成正確的 Nginx 配置
echo "3. 生成 Nginx 配置..."
echo "----------------------------------------"

cat > "$NGINX_CONFIG" <<EOF
# aikz.usdt2026.cc - 聊天AI後台 (saas-demo)
# 強制指向端口 3000，不是 3003

# HTTP 重定向到 HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    
    # 允許 Let's Encrypt 驗證
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # 其他所有請求重定向到 HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS 服務器
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN;
    
    # SSL 證書
    ssl_certificate $SSL_CERT;
    ssl_certificate_key $SSL_KEY;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全頭
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    client_max_body_size 50M;

    # Next.js 應用反向代理 - 強制指向端口 3000
    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        
        # Next.js 特殊配置
        proxy_buffering off;
    }
    
    # Next.js 靜態文件
    location /_next/static {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_cache_valid 200 60m;
        add_header Cache-Control "public, immutable";
    }
    
    # API 代理（如果需要）
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

echo "✅ 配置文件已生成: $NGINX_CONFIG"
echo ""

# 4. 創建符號鏈接
echo "4. 創建符號鏈接..."
echo "----------------------------------------"
rm -f "$NGINX_ENABLED"
ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"
echo "✅ 符號鏈接已創建: $NGINX_ENABLED"
echo ""

# 5. 測試 Nginx 配置
echo "5. 測試 Nginx 配置..."
echo "----------------------------------------"
if nginx -t 2>&1 | grep -q "test is successful"; then
  echo "✅ Nginx 配置測試通過"
else
  echo "❌ Nginx 配置測試失敗"
  nginx -t
  exit 1
fi
echo ""

# 6. 重啟 Nginx
echo "6. 重啟 Nginx..."
echo "----------------------------------------"
systemctl restart nginx
sleep 2

if systemctl is-active --quiet nginx; then
  echo "✅ Nginx 重啟成功"
else
  echo "❌ Nginx 重啟失敗"
  systemctl status nginx
  exit 1
fi
echo ""

# 7. 驗證配置
echo "7. 驗證配置..."
echo "----------------------------------------"

# 檢查配置文件中指向的端口
CONFIG_PORT=$(grep "proxy_pass.*127.0.0.1" "$NGINX_CONFIG" | grep -oP "127\.0\.0\.1:\K\d+" | head -1)
if [ "$CONFIG_PORT" = "$PORT" ]; then
  echo "✅ 配置正確指向端口 $PORT"
else
  echo "❌ 配置錯誤！指向端口 $CONFIG_PORT，應該是 $PORT"
  exit 1
fi

# 測試本地訪問
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
  echo "✅ 本地服務響應正常 (HTTP $HTTP_CODE)"
else
  echo "⚠️  本地服務響應異常 (HTTP $HTTP_CODE)"
fi

# 測試外部訪問
EXTERNAL_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN 2>/dev/null || echo "000")
if [ "$EXTERNAL_CODE" = "200" ]; then
  echo "✅ 外部訪問正常 (HTTP $EXTERNAL_CODE)"
  
  # 檢查返回的內容
  EXTERNAL_CONTENT=$(curl -s https://$DOMAIN 2>/dev/null | head -c 300)
  if echo "$EXTERNAL_CONTENT" | grep -qi "智控王\|Smart Control King"; then
    echo "❌ 外部訪問返回的內容仍包含 'AI 智控王'"
    echo "   這可能是："
    echo "   1. 瀏覽器緩存（請強制刷新 Ctrl+F5）"
    echo "   2. CDN 緩存（需要等待或清除）"
    echo "   3. saas-demo 構建問題"
  elif echo "$EXTERNAL_CONTENT" | grep -qi "登錄\|login\|聊天 AI"; then
    echo "✅ 外部訪問返回的內容正確（包含登錄相關文字）"
  else
    echo "⚠️  無法確定返回的內容是否正確"
  fi
else
  echo "⚠️  外部訪問異常 (HTTP $EXTERNAL_CODE)"
fi
echo ""

echo "=========================================="
echo "✅ 修復完成！"
echo "時間: $(date)"
echo "=========================================="
echo ""
echo "訪問地址: https://$DOMAIN"
echo ""
echo "如果瀏覽器仍然顯示錯誤頁面，請："
echo "1. 強制刷新 (Ctrl+F5 或 Cmd+Shift+R)"
echo "2. 清除瀏覽器緩存"
echo "3. 使用無痕模式訪問"
echo "4. 檢查 saas-demo 是否正確構建: cd /home/ubuntu/telegram-ai-system/saas-demo && npm run build"
