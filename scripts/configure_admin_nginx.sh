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

# 检查 SSL 证书是否存在
SSL_CERT="/etc/letsencrypt/live/aiadmin.usdt2026.cc/fullchain.pem"
SSL_KEY="/etc/letsencrypt/live/aiadmin.usdt2026.cc/privkey.pem"
HAS_SSL=false

if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
    HAS_SSL=true
    echo "✅ 检测到 SSL 证书，将配置 HTTPS"
else
    echo "⚠️  未检测到 SSL 证书，将仅配置 HTTP"
    echo "   SSL 证书路径: $SSL_CERT"
fi

# 创建或更新配置文件
CONFIG_FILE="$NGINX_SITES_DIR/aiadmin.usdt2026.cc"

echo "📝 创建 Nginx 配置文件: $CONFIG_FILE"

if [ "$HAS_SSL" = true ]; then
    # 配置 HTTPS
    sudo tee "$CONFIG_FILE" > /dev/null << EOF
# 管理后台配置 - HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name aiadmin.usdt2026.cc;

    # 重定向到 HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name aiadmin.usdt2026.cc;

    # SSL 证书配置
    ssl_certificate $SSL_CERT;
    ssl_certificate_key $SSL_KEY;
    
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
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # 管理后台前端代理
    location /admin {
        proxy_pass http://127.0.0.1:3006;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # 重写路径，移除 /admin 前缀
        rewrite ^/admin/?(.*) /\$1 break;
    }

    # 管理后台根路径（可选，直接访问域名时跳转到 /admin）
    location = / {
        return 301 /admin;
    }
}
EOF
else
    # 仅配置 HTTP
    sudo tee "$CONFIG_FILE" > /dev/null << 'EOF'
# 管理后台配置 - HTTP（无 SSL 证书）
server {
    listen 80;
    listen [::]:80;
    server_name aiadmin.usdt2026.cc;

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
fi

# 创建符号链接
if [ ! -L "$NGINX_ENABLED_DIR/aiadmin.usdt2026.cc" ]; then
    echo "🔗 创建符号链接..."
    sudo ln -s "$CONFIG_FILE" "$NGINX_ENABLED_DIR/aiadmin.usdt2026.cc"
fi

# 测试配置
echo "🧪 测试 Nginx 配置..."
if sudo nginx -t; then
    echo "✅ Nginx 配置测试通过"
    
    # 重新加载或启动 Nginx
    echo "🔄 重新加载 Nginx..."
    if sudo systemctl is-active --quiet nginx; then
        sudo systemctl reload nginx
        echo "✅ Nginx 已重新加载"
    else
        echo "⚠️  Nginx 服务未运行，尝试启动..."
        sudo systemctl start nginx
        if sudo systemctl is-active --quiet nginx; then
            echo "✅ Nginx 已启动"
        else
            echo "❌ Nginx 启动失败"
            echo "请检查 Nginx 状态: sudo systemctl status nginx"
            exit 1
        fi
    fi
    
    echo "✅ Nginx 配置完成！"
    echo ""
    if [ "$HAS_SSL" = true ]; then
        echo "📋 访问地址:"
        echo "   - HTTP:  http://aiadmin.usdt2026.cc/admin (自动跳转到 HTTPS)"
        echo "   - HTTPS: https://aiadmin.usdt2026.cc/admin"
    else
        echo "📋 访问地址:"
        echo "   - HTTP:  http://aiadmin.usdt2026.cc/admin"
        echo ""
        echo "💡 提示: 如需配置 HTTPS，请先申请 SSL 证书："
        echo "   sudo certbot certonly --nginx -d aiadmin.usdt2026.cc"
        echo "   然后重新运行此脚本"
    fi
    echo ""
    echo "⚠️  注意:"
    echo "   1. 确保域名 DNS 已指向服务器 IP"
    echo "   2. 确保防火墙允许 80 端口（HTTP）或 443 端口（HTTPS）"
else
    echo "❌ Nginx 配置测试失败"
    echo "请检查配置文件: $CONFIG_FILE"
    exit 1
fi
