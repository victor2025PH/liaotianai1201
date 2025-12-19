#!/bin/bash
# ============================================================
# 修复白屏问题：让 Nginx 直接服务静态文件
# ============================================================

set -e

echo "=========================================="
echo "🔧 修复白屏问题（Nginx 直接服务静态文件）"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"
DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/$DOMAIN"

# 1. 定位静态资源路径
echo "[1/4] 定位静态资源路径..."
echo "----------------------------------------"

# 检查多个可能的路径
STATIC_PATH=""
PUBLIC_PATH=""

# 优先检查 standalone 目录中的静态文件
if [ -d "$FRONTEND_DIR/.next/standalone/.next/static" ]; then
    STATIC_PATH="$FRONTEND_DIR/.next/standalone/.next/static"
    echo "✅ 找到静态资源路径（standalone）: $STATIC_PATH"
elif [ -d "$FRONTEND_DIR/.next/static" ]; then
    STATIC_PATH="$FRONTEND_DIR/.next/static"
    echo "✅ 找到静态资源路径: $STATIC_PATH"
else
    # 尝试查找
    STATIC_PATH=$(find "$FRONTEND_DIR/.next" -type d -name "static" 2>/dev/null | head -1)
    if [ -n "$STATIC_PATH" ] && [ -d "$STATIC_PATH" ]; then
        echo "✅ 找到静态资源路径（自动查找）: $STATIC_PATH"
    else
        echo "❌ 未找到静态资源路径"
        echo "请确保前端已构建: cd $FRONTEND_DIR && npm run build"
        exit 1
    fi
fi

# 检查 public 目录
if [ -d "$FRONTEND_DIR/public" ]; then
    PUBLIC_PATH="$FRONTEND_DIR/public"
    echo "✅ 找到 public 目录: $PUBLIC_PATH"
elif [ -d "$FRONTEND_DIR/.next/standalone/public" ]; then
    PUBLIC_PATH="$FRONTEND_DIR/.next/standalone/public"
    echo "✅ 找到 public 目录（standalone）: $PUBLIC_PATH"
else
    echo "⚠️  public 目录不存在，将跳过 /public/ 配置"
fi

# 验证路径权限
if [ -n "$STATIC_PATH" ] && [ ! -r "$STATIC_PATH" ]; then
    echo "⚠️  静态资源路径不可读，尝试修复权限..."
    sudo chown -R ubuntu:ubuntu "$STATIC_PATH" 2>/dev/null || true
    sudo chmod -R 755 "$STATIC_PATH" 2>/dev/null || true
fi

if [ -n "$PUBLIC_PATH" ] && [ ! -r "$PUBLIC_PATH" ]; then
    echo "⚠️  public 目录不可读，尝试修复权限..."
    sudo chown -R ubuntu:ubuntu "$PUBLIC_PATH" 2>/dev/null || true
    sudo chmod -R 755 "$PUBLIC_PATH" 2>/dev/null || true
fi

echo ""

# 2. 生成 Nginx 配置
echo "[2/4] 生成 Nginx 配置..."
echo "----------------------------------------"

# 备份现有配置
if [ -f "$NGINX_CONFIG" ]; then
    sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ 已备份现有配置"
fi

# 生成新配置
sudo tee "$NGINX_CONFIG" > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;

    # 日志配置
    access_log /var/log/nginx/aikz.access.log;
    error_log /var/log/nginx/aikz.error.log;

    # 客户端最大请求体大小
    client_max_body_size 50M;

    # Next.js 静态资源 - 直接服务本地文件（不使用代理）
    location /_next/static/ {
        alias $STATIC_PATH/;
        expires 365d;
        add_header Cache-Control "public, immutable";
        access_log off;
        
        # 确保文件存在时返回，不存在时返回 404
        try_files \$uri =404;
    }

    # Next.js 静态资源（兼容没有下划线的路径）
    location /next/static/ {
        # 重写路径，将 /next/static/xxx 重写为 /_next/static/xxx
        rewrite ^/next/static/(.*)$ /_next/static/\$1 last;
    }

EOF

# 如果有 public 目录，添加 public 配置
if [ -n "$PUBLIC_PATH" ]; then
    sudo tee -a "$NGINX_CONFIG" > /dev/null << EOF
    # 公共资源 - 直接服务本地文件
    location /public/ {
        alias $PUBLIC_PATH/;
        expires 30d;
        access_log off;
        
        # 确保文件存在时返回，不存在时返回 404
        try_files \$uri =404;
    }

EOF
fi

# 添加 API 和主应用配置
sudo tee -a "$NGINX_CONFIG" > /dev/null << 'EOF'
    # API 转发到后端 (端口 8000)
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        
        # 基础代理头
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass $http_upgrade;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 前端应用转发（所有其他请求）
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        
        # 基础代理头
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass $http_upgrade;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲设置
        proxy_buffering off;
    }
}

# HTTPS 配置（如果 SSL 证书存在）
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL 证书路径（如果存在）
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 日志配置
    access_log /var/log/nginx/aikz.access.log;
    error_log /var/log/nginx/aikz.error.log;

    # 客户端最大请求体大小
    client_max_body_size 50M;

    # Next.js 静态资源 - 直接服务本地文件（不使用代理）
    location /_next/static/ {
        alias $STATIC_PATH/;
        expires 365d;
        add_header Cache-Control "public, immutable";
        access_log off;
        
        # 确保文件存在时返回，不存在时返回 404
        try_files $uri =404;
    }

    # Next.js 静态资源（兼容没有下划线的路径）
    location /next/static/ {
        # 重写路径，将 /next/static/xxx 重写为 /_next/static/xxx
        rewrite ^/next/static/(.*)$ /_next/static/$1 last;
    }

EOF

# 如果有 public 目录，添加 public 配置到 HTTPS
if [ -n "$PUBLIC_PATH" ]; then
    sudo tee -a "$NGINX_CONFIG" > /dev/null << EOF
    # 公共资源 - 直接服务本地文件
    location /public/ {
        alias $PUBLIC_PATH/;
        expires 30d;
        access_log off;
        
        # 确保文件存在时返回，不存在时返回 404
        try_files \$uri =404;
    }

EOF
fi

# 添加 HTTPS 的 API 和主应用配置
sudo tee -a "$NGINX_CONFIG" > /dev/null << 'EOF'
    # API 转发到后端 (端口 8000)
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        
        # 基础代理头
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass $http_upgrade;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 前端应用转发（所有其他请求）
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        
        # 基础代理头
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass $http_upgrade;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲设置
        proxy_buffering off;
    }
}
EOF

echo "✅ Nginx 配置已生成"
echo "  静态资源路径: $STATIC_PATH"
if [ -n "$PUBLIC_PATH" ]; then
    echo "  Public 路径: $PUBLIC_PATH"
fi
echo ""

# 3. 测试配置
echo "[3/4] 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t; then
    echo "✅ Nginx 配置测试通过"
else
    echo "❌ Nginx 配置测试失败"
    echo "查看错误详情:"
    sudo nginx -t 2>&1
    exit 1
fi
echo ""

# 4. 重启 Nginx
echo "[4/4] 重启 Nginx..."
echo "----------------------------------------"
sudo systemctl restart nginx
sleep 2

# 检查 Nginx 状态
if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx 已重启"
    sudo systemctl status nginx --no-pager -l | head -10
else
    echo "❌ Nginx 重启失败"
    echo "查看错误日志:"
    sudo journalctl -u nginx --no-pager -l | tail -20
    exit 1
fi
echo ""

# 5. 验证静态资源
echo "=========================================="
echo "🧪 验证静态资源"
echo "=========================================="
echo ""

# 查找一个示例静态文件
EXAMPLE_FILE=$(find "$STATIC_PATH" -name "*.js" -type f 2>/dev/null | head -1)
if [ -n "$EXAMPLE_FILE" ]; then
    RELATIVE_PATH=$(echo "$EXAMPLE_FILE" | sed "s|$STATIC_PATH/||")
    STATIC_URL="/_next/static/$RELATIVE_PATH"
    
    echo "测试静态资源访问:"
    echo "  文件路径: $EXAMPLE_FILE"
    echo "  URL: $STATIC_URL"
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1$STATIC_URL" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  ✅ 静态资源访问正常 (HTTP $HTTP_CODE)"
    else
        echo "  ⚠️  静态资源访问异常 (HTTP $HTTP_CODE)"
        echo "  请检查文件权限和路径配置"
    fi
else
    echo "⚠️  未找到示例静态文件，无法测试"
fi
echo ""

echo "测试主页面:"
MAIN_PAGE_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ 2>/dev/null || echo "000")
if [ "$MAIN_PAGE_CODE" = "200" ] || [ "$MAIN_PAGE_CODE" = "301" ] || [ "$MAIN_PAGE_CODE" = "302" ]; then
    echo "  ✅ 主页面访问正常 (HTTP $MAIN_PAGE_CODE)"
else
    echo "  ⚠️  主页面访问异常 (HTTP $MAIN_PAGE_CODE)"
fi
echo ""

echo "=========================================="
echo "✅ 白屏问题修复完成"
echo "=========================================="
echo ""
echo "配置摘要:"
echo "  - 静态资源路径: $STATIC_PATH"
if [ -n "$PUBLIC_PATH" ]; then
    echo "  - Public 路径: $PUBLIC_PATH"
fi
echo "  - 配置文件: $NGINX_CONFIG"
echo ""
echo "如果问题仍然存在，请："
echo "1. 清除浏览器缓存并硬刷新 (Ctrl+Shift+R)"
echo "2. 检查浏览器控制台是否还有错误"
echo "3. 查看 Nginx 错误日志: sudo tail -f /var/log/nginx/aikz.error.log"
echo "4. 验证静态文件权限: ls -la $STATIC_PATH | head -10"
echo ""

