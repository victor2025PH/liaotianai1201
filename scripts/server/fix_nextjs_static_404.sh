#!/bin/bash
# ============================================================
# 修复 Next.js 静态文件 404 错误
# 确保 Nginx 正确代理静态文件请求
# ============================================================

set -e

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_ROOT/saas-demo"

echo "=========================================="
echo "🔧 修复 Next.js 静态文件 404 错误"
echo "=========================================="
echo ""

# 1. 检查 Next.js 服务器是否运行
echo "[1/5] 检查 Next.js 服务器状态..."
echo "----------------------------------------"
if pm2 list | grep -q "saas-demo-frontend.*online"; then
  echo "✅ Next.js 服务器正在运行"
  PORT_3000=$(sudo lsof -ti :3000 2>/dev/null || echo "")
  if [ -n "$PORT_3000" ]; then
    echo "✅ 端口 3000 正在监听 (PID: $PORT_3000)"
  else
    echo "⚠️  端口 3000 未监听，但 PM2 显示在线"
  fi
else
  echo "❌ Next.js 服务器未运行"
  echo "正在启动..."
  cd "$FRONTEND_DIR" || exit 1
  if [ -f ".next/standalone/server.js" ]; then
    pm2 start node \
      --name saas-demo-frontend \
      --max-memory-restart 1G \
      -- .next/standalone/server.js || {
      echo "❌ 启动失败"
      exit 1
    }
    sleep 5
    echo "✅ 已启动 Next.js 服务器"
  else
    echo "❌ 找不到 server.js，需要重新构建"
    exit 1
  fi
fi
echo ""

# 2. 检查静态文件是否存在
echo "[2/5] 检查静态文件..."
echo "----------------------------------------"
cd "$FRONTEND_DIR" || exit 1

if [ -d ".next/static" ]; then
  STATIC_COUNT=$(find .next/static -type f 2>/dev/null | wc -l)
  echo "✅ .next/static 存在（$STATIC_COUNT 个文件）"
  
  # 检查 chunks 目录
  if [ -d ".next/static/chunks" ]; then
    CHUNK_COUNT=$(find .next/static/chunks -type f 2>/dev/null | wc -l)
    echo "✅ .next/static/chunks 存在（$CHUNK_COUNT 个文件）"
    
    # 显示一个示例文件
    SAMPLE_FILE=$(find .next/static/chunks -name "*.js" -type f 2>/dev/null | head -1)
    if [ -n "$SAMPLE_FILE" ]; then
      echo "   示例文件: $SAMPLE_FILE"
      ls -lh "$SAMPLE_FILE" | awk '{print "   大小: " $5}'
    fi
  else
    echo "❌ .next/static/chunks 不存在"
  fi
else
  echo "❌ .next/static 不存在，需要重新构建"
  exit 1
fi
echo ""

# 3. 测试 Next.js 服务器是否能提供静态文件
echo "[3/5] 测试 Next.js 服务器静态文件访问..."
echo "----------------------------------------"
if [ -n "$SAMPLE_FILE" ]; then
  REL_PATH=${SAMPLE_FILE#.next/static/}
  TEST_URL="http://127.0.0.1:3000/_next/static/$REL_PATH"
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$TEST_URL" 2>/dev/null || echo "000")
  
  if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Next.js 服务器可以正常提供静态文件 (HTTP $HTTP_CODE)"
  else
    echo "⚠️  Next.js 服务器无法提供静态文件 (HTTP $HTTP_CODE)"
    echo "   测试 URL: $TEST_URL"
  fi
fi
echo ""

# 4. 修复 Nginx 配置
echo "[4/5] 修复 Nginx 配置..."
echo "----------------------------------------"

# 备份原配置
sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true

# 创建新的 Nginx 配置
sudo tee "$NGINX_CONFIG" > /dev/null << 'EOF'
# HTTP 到 HTTPS 重定向
server {
    listen 80;
    server_name aikz.usdt2026.cc;
    return 301 https://$host$request_uri;
}

# HTTPS 配置
server {
    listen 443 ssl http2;
    server_name aikz.usdt2026.cc;

    # SSL 证书
    ssl_certificate /etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 50M;

    # WebSocket 支持 - 通知服务（必须在 /api/ 之前，优先级最高）
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

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Next.js 静态资源（兼容路径 - 处理 /next/static 请求）
    # 重写为 /_next/static 然后代理到 Next.js 服务器
    location /next/static {
        rewrite ^/next/static/(.*)$ /_next/static/$1 break;
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        expires 365d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Next.js 静态资源 - 标准路径（代理到 Next.js 服务器）
    location /_next/static {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        expires 365d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # public 目录资源
    location /public {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        expires 30d;
        access_log off;
    }

    # 前端应用（所有其他请求）
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 禁用 HTML 缓存
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
        expires off;
    }
}
EOF

# 创建符号链接
sudo ln -sf "$NGINX_CONFIG" /etc/nginx/sites-enabled/aikz.usdt2026.cc

# 测试配置
if sudo nginx -t 2>/dev/null; then
  echo "✅ Nginx 配置语法正确"
  sudo systemctl reload nginx
  echo "✅ Nginx 已重新加载"
else
  echo "❌ Nginx 配置语法错误"
  sudo nginx -t
  exit 1
fi
echo ""

# 5. 验证修复
echo "[5/5] 验证修复..."
echo "----------------------------------------"
sleep 2

# 测试静态文件访问
if [ -n "$SAMPLE_FILE" ]; then
  REL_PATH=${SAMPLE_FILE#.next/static/}
  TEST_URL="https://aikz.usdt2026.cc/next/static/$REL_PATH"
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k "$TEST_URL" 2>/dev/null || echo "000")
  
  if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ 静态文件可以通过 Nginx 访问 (HTTP $HTTP_CODE)"
  else
    echo "⚠️  静态文件访问异常 (HTTP $HTTP_CODE)"
    echo "   测试 URL: $TEST_URL"
  fi
fi

# 测试主页
MAIN_PAGE_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k "https://aikz.usdt2026.cc/" 2>/dev/null || echo "000")
if [ "$MAIN_PAGE_CODE" = "200" ] || [ "$MAIN_PAGE_CODE" = "301" ] || [ "$MAIN_PAGE_CODE" = "302" ]; then
  echo "✅ 主页可以访问 (HTTP $MAIN_PAGE_CODE)"
else
  echo "⚠️  主页访问异常 (HTTP $MAIN_PAGE_CODE)"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "建议操作："
echo "1. 清除浏览器缓存并刷新页面"
echo "2. 如果还有问题，检查 PM2 日志: pm2 logs saas-demo-frontend --lines 50"
echo "3. 检查 Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
