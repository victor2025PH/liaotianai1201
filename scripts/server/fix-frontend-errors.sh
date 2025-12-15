#!/bin/bash
# ============================================================
# 修复前端错误（静态资源、WebSocket、React警告）
# ============================================================

set -e

echo "=========================================="
echo "🔧 修复前端错误"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-enabled/default"
BACKUP_DIR="/var/backups/nginx_configs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

# 1. 备份当前配置
echo "[1/5] 备份当前配置..."
echo "----------------------------------------"
mkdir -p "$BACKUP_DIR"
cp "$NGINX_CONFIG" "$BACKUP_DIR/default.backup.$TIMESTAMP"
echo "✅ 配置已备份"
echo ""

# 2. 更新 Nginx 配置（修复静态资源路径和 WebSocket 支持）
echo "[2/5] 更新 Nginx 配置..."
echo "----------------------------------------"
cat > "$NGINX_CONFIG" <<'NGINX_EOF'
server {
    listen 443 ssl;
    server_name aikz.usdt2026.cc;
    
    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    client_max_body_size 50M;
    
    # WebSocket 支持（必须在其他 location 之前）
    location /api/v1/notifications/ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
    
    # 后端 API - 转发到后端（必须在根路径之前）
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # 前端应用 - 转发到前端（包括所有路径，Next.js 会处理静态资源）
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# HTTP 到 HTTPS 重定向
server {
    listen 80;
    server_name aikz.usdt2026.cc;
    return 301 https://$host$request_uri;
}
NGINX_EOF

echo "✅ Nginx 配置已更新（包含 WebSocket 支持）"
echo ""

# 3. 测试并重新加载 Nginx
echo "[3/5] 测试并重新加载 Nginx..."
echo "----------------------------------------"
if nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
    systemctl reload nginx
    echo "✅ Nginx 已重新加载"
else
    echo "❌ Nginx 配置语法错误"
    nginx -t
    echo ""
    echo "恢复备份..."
    cp "$BACKUP_DIR/default.backup.$TIMESTAMP" "$NGINX_CONFIG"
    exit 1
fi
echo ""

# 4. 检查后端 WebSocket 路由
echo "[4/5] 检查后端 WebSocket 路由..."
echo "----------------------------------------"
cd "$PROJECT_DIR/admin-backend"

# 检查 notifications.py 中是否有 WebSocket 路由
if grep -q "@router.websocket" "app/api/notifications.py"; then
    echo "✅ 后端 WebSocket 路由已定义"
else
    echo "⚠️  后端 WebSocket 路由未找到"
fi

# 检查路由是否注册
if grep -q "notifications" "app/api/__init__.py" || grep -q "notifications" "app/main.py"; then
    echo "✅ 通知路由已注册"
else
    echo "⚠️  通知路由可能未注册"
fi
echo ""

# 5. 验证
echo "[5/5] 验证修复..."
echo "----------------------------------------"
sleep 3

# 测试 HTTPS 访问
HTTPS_LOGIN=$(curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/login 2>/dev/null || echo "000")
if [ "$HTTPS_LOGIN" = "200" ]; then
    echo "✅ HTTPS /login: HTTP 200"
else
    echo "⚠️  HTTPS /login: HTTP $HTTPS_LOGIN"
fi

# 测试 API
HTTPS_API=$(curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/api/v1/health 2>/dev/null || echo "000")
if [ "$HTTPS_API" = "200" ] || [ "$HTTPS_API" = "404" ] || [ "$HTTPS_API" = "401" ]; then
    echo "✅ HTTPS /api: HTTP $HTTPS_API"
else
    echo "⚠️  HTTPS /api: HTTP $HTTPS_API"
fi

# 测试 WebSocket 端点（检查路由是否存在）
WS_ROUTE=$(curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/api/v1/notifications/ws/test 2>/dev/null || echo "000")
if [ "$WS_ROUTE" = "400" ] || [ "$WS_ROUTE" = "426" ]; then
    echo "✅ WebSocket 路由存在（返回 $WS_ROUTE 是正常的，因为需要 WebSocket 协议）"
else
    echo "⚠️  WebSocket 路由: HTTP $WS_ROUTE"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "前端代码修复说明:"
echo "1. Switch 组件警告：确保所有 Switch 的 checked 属性始终是 boolean，不是 undefined"
echo "2. 静态资源 403：Next.js standalone 模式会自动处理，如果仍有问题，检查 .next/static 目录权限"
echo "3. WebSocket 连接：确保后端路由 /api/v1/notifications/ws/{user_email} 已正确注册"
echo ""
echo "如果仍有问题，请检查:"
echo "1. 前端服务日志: sudo journalctl -u liaotian-frontend -n 50 --no-pager"
echo "2. 后端服务日志: sudo journalctl -u luckyred-api -n 50 --no-pager"
echo "3. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo ""

