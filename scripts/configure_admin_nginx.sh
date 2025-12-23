#!/bin/bash
# 配置 Nginx 反向代理管理后台

set -e

NGINX_SITES_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"

echo "🔧 配置 Nginx 反向代理管理后台..."

# 检查 Nginx 是否安装
if ! command -v nginx &> /dev/null; then
    echo "❌ Nginx 未安装"
    exit 1
fi

# 创建或更新配置文件
CONFIG_FILE="$NGINX_SITES_DIR/aiadmin.usdt2026.cc"

echo "📝 创建 Nginx 配置文件: $CONFIG_FILE"

sudo tee "$CONFIG_FILE" > /dev/null << 'EOF'
# 管理后台配置
server {
    listen 80;
    listen [::]:80;
    server_name aiadmin.usdt2026.cc;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name aiadmin.usdt2026.cc;

    # SSL 证书配置（根据实际情况修改路径）
    ssl_certificate /etc/letsencrypt/live/aiadmin.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aiadmin.usdt2026.cc/privkey.pem;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 日志
    access_log /var/log/nginx/aiadmin-access.log;
    error_log /var/log/nginx/aiadmin-error.log;

    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # 管理后台前端代理
    location /admin {
        proxy_pass http://127.0.0.1:3006;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 重写路径，移除 /admin 前缀
        rewrite ^/admin/?(.*) /$1 break;
    }

    # 管理后台根路径（可选，直接访问域名时跳转到 /admin）
    location = / {
        return 301 /admin;
    }
}
EOF

# 创建符号链接
if [ ! -L "$NGINX_ENABLED_DIR/aiadmin.usdt2026.cc" ]; then
    echo "🔗 创建符号链接..."
    sudo ln -s "$CONFIG_FILE" "$NGINX_ENABLED_DIR/aiadmin.usdt2026.cc"
fi

# 测试配置
echo "🧪 测试 Nginx 配置..."
if sudo nginx -t; then
    echo "✅ Nginx 配置测试通过"
    
    # 重新加载 Nginx
    echo "🔄 重新加载 Nginx..."
    sudo systemctl reload nginx
    
    echo "✅ Nginx 配置完成！"
    echo ""
    echo "📋 访问地址:"
    echo "   - HTTP:  http://aiadmin.usdt2026.cc/admin"
    echo "   - HTTPS: https://aiadmin.usdt2026.cc/admin"
    echo ""
    echo "⚠️  注意:"
    echo "   1. 确保 SSL 证书已配置（如果使用 HTTPS）"
    echo "   2. 确保域名 DNS 已指向服务器 IP"
    echo "   3. 确保防火墙允许 80 和 443 端口"
else
    echo "❌ Nginx 配置测试失败"
    echo "请检查配置文件: $CONFIG_FILE"
    exit 1
fi

