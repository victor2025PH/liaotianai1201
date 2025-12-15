#!/bin/bash
# ============================================================
# 彻底重置 Nginx 配置
# ============================================================

set +e

echo "=========================================="
echo "🔧 彻底重置 Nginx 配置"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

DOMAIN="aikz.usdt2026.cc"
CONFIG_FILE="/etc/nginx/sites-enabled/default"
AVAILABLE_FILE="/etc/nginx/sites-available/default"

# 1. 备份旧配置
echo "[1/4] 备份旧配置..."
echo "----------------------------------------"
if [ -f "$CONFIG_FILE" ]; then
    BACKUP="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$CONFIG_FILE" "$BACKUP"
    echo "✅ 已备份到: $BACKUP"
else
    echo "⚠️  配置文件不存在，跳过备份"
fi
if [ -f "$AVAILABLE_FILE" ]; then
    BACKUP_AVAILABLE="${AVAILABLE_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$AVAILABLE_FILE" "$BACKUP_AVAILABLE"
    echo "✅ 已备份到: $BACKUP_AVAILABLE"
fi
echo ""

# 2. 删除旧配置
echo "[2/4] 删除旧配置文件..."
echo "----------------------------------------"
rm -f "$CONFIG_FILE"
rm -f "$AVAILABLE_FILE"
echo "✅ 旧配置文件已删除"
echo ""

# 3. 创建新配置
echo "[3/4] 创建新配置文件..."
echo "----------------------------------------"
cat > "$AVAILABLE_FILE" <<'NGINX_CONFIG'
server {
    listen 443 ssl;
    server_name aikz.usdt2026.cc;
    
    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    # 客户端最大请求体大小
    client_max_body_size 50M;
    
    # 登录页面 - 转发到后端 API（必须在根路径之前）
    location /login {
        proxy_pass http://127.0.0.1:8000/api/v1/auth/login;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 认证相关路由
    location /api/v1/auth/ {
        proxy_pass http://127.0.0.1:8000/api/v1/auth/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 后端 API - 转发到后端
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
    
    # 前端应用 - 转发到前端
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
NGINX_CONFIG

# 创建符号链接
ln -sf "$AVAILABLE_FILE" "$CONFIG_FILE"
echo "✅ 新配置文件已创建: $AVAILABLE_FILE"
echo "✅ 符号链接已创建: $CONFIG_FILE"
echo ""

# 4. 测试并重启
echo "[4/4] 测试配置并重启 Nginx..."
echo "----------------------------------------"
if nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
    systemctl restart nginx
    sleep 2
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已重启"
    else
        echo "❌ Nginx 启动失败"
        systemctl status nginx --no-pager -l | head -15
        exit 1
    fi
else
    echo "❌ Nginx 配置语法错误:"
    nginx -t 2>&1 | tail -10
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Nginx 配置重置完成"
echo "=========================================="
echo ""

