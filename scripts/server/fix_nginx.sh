#!/bin/bash
# ============================================================
# 修复 Nginx 配置脚本
# ============================================================

set -e

echo "=========================================="
echo "🔧 修复 Nginx 配置"
echo "=========================================="
echo ""

# 1. 检查并安装 Nginx
echo "[1/5] 检查并安装 Nginx..."
echo "----------------------------------------"
if ! command -v nginx &> /dev/null; then
    echo "Nginx 未安装，正在安装..."
    sudo DEBIAN_FRONTEND=noninteractive apt-get update -q
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nginx
    echo "✅ Nginx 已安装"
else
    echo "✅ Nginx 已安装"
    nginx -v
fi
echo ""

# 2. 生成 Nginx 配置
echo "[2/5] 生成 Nginx 配置..."
echo "----------------------------------------"
NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
DOMAIN="aikz.usdt2026.cc"

# 创建配置目录（如果不存在）
sudo mkdir -p /etc/nginx/sites-available
sudo mkdir -p /etc/nginx/sites-enabled

# 生成配置文件
sudo tee "$NGINX_CONFIG" > /dev/null << 'EOF'
server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # 日志配置
    access_log /var/log/nginx/aikz.access.log;
    error_log /var/log/nginx/aikz.error.log;

    # 客户端最大请求体大小
    client_max_body_size 50M;

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

    # Next.js 静态资源 - 代理到前端服务器
    location /_next/static {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # 缓存静态资源
        expires 365d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Next.js 静态资源（兼容没有下划线的路径）
    location /next/static {
        # 重写路径，将 /next/static/xxx 重写为 /_next/static/xxx
        rewrite ^/next/static/(.*)$ /_next/static/$1 break;
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # 缓存静态资源
        expires 365d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # 公共资源
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

echo "✅ Nginx 配置已生成: $NGINX_CONFIG"
echo ""

# 3. 启用配置
echo "[3/5] 启用 Nginx 配置..."
echo "----------------------------------------"
# 创建软链接到 sites-enabled
if [ ! -f "/etc/nginx/sites-enabled/aikz.usdt2026.cc" ]; then
    sudo ln -s "$NGINX_CONFIG" /etc/nginx/sites-enabled/aikz.usdt2026.cc
    echo "✅ 配置已启用"
else
    echo "✅ 配置已存在"
fi

# 删除 default 配置（如果存在）
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    sudo rm -f /etc/nginx/sites-enabled/default
    echo "✅ 已删除 default 配置"
fi
echo ""

# 4. 测试 Nginx 配置
echo "[4/5] 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t; then
    echo "✅ Nginx 配置测试通过"
else
    echo "❌ Nginx 配置测试失败"
    exit 1
fi
echo ""

# 5. 重启 Nginx
echo "[5/5] 重启 Nginx..."
echo "----------------------------------------"
sudo systemctl restart nginx
sleep 2

# 检查 Nginx 状态
if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx 已启动"
    sudo systemctl status nginx --no-pager -l | head -10
else
    echo "❌ Nginx 启动失败"
    echo "查看错误日志:"
    sudo journalctl -u nginx --no-pager -l | tail -20
    exit 1
fi
echo ""

# 6. 申请 SSL 证书（可选）
echo "=========================================="
echo "🔒 申请 SSL 证书（可选）"
echo "=========================================="
echo ""

# 检查是否已安装 certbot
if ! command -v certbot &> /dev/null; then
    echo "Certbot 未安装，正在安装..."
    sudo DEBIAN_FRONTEND=noninteractive apt-get update -q
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y certbot python3-certbot-nginx
    echo "✅ Certbot 已安装"
fi

# 检查是否已有 SSL 证书
SSL_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
if [ -f "$SSL_CERT" ]; then
    echo "✅ SSL 证书已存在: $SSL_CERT"
    echo "证书有效期:"
    sudo openssl x509 -in "$SSL_CERT" -noout -dates 2>/dev/null || true
    echo ""
    echo "如果需要更新证书，请运行:"
    echo "  sudo certbot renew"
else
    echo "未找到 SSL 证书，尝试申请..."
    echo ""
    echo "⚠️  注意：申请 SSL 证书需要："
    echo "  1. 域名 DNS 已正确解析到服务器 IP"
    echo "  2. 端口 80 可以从外网访问"
    echo "  3. 服务器防火墙允许端口 80 和 443"
    echo ""
    read -p "是否现在申请 SSL 证书？(y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "正在申请 SSL 证书..."
        sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN" --redirect || {
            echo "⚠️  SSL 证书申请失败，但 HTTP 配置已生效"
            echo "   您可以稍后手动运行: sudo certbot --nginx -d $DOMAIN"
        }
    else
        echo "跳过 SSL 证书申请"
        echo "您可以稍后运行: sudo certbot --nginx -d $DOMAIN"
    fi
fi
echo ""

# 7. 验证服务
echo "=========================================="
echo "🧪 验证服务"
echo "=========================================="
echo ""

echo "检查端口监听:"
echo "  端口 80 (HTTP):"
sudo ss -tlnp | grep ":80 " || echo "    ⚠️  端口 80 未监听"

if [ -f "$SSL_CERT" ]; then
    echo "  端口 443 (HTTPS):"
    sudo ss -tlnp | grep ":443 " || echo "    ⚠️  端口 443 未监听"
fi

echo ""
echo "检查后端服务 (端口 8000):"
if sudo ss -tlnp | grep -q ":8000 "; then
    echo "  ✅ 端口 8000 正在监听"
else
    echo "  ⚠️  端口 8000 未监听（后端服务可能未启动）"
fi

echo ""
echo "检查前端服务 (端口 3000):"
if sudo ss -tlnp | grep -q ":3000 "; then
    echo "  ✅ 端口 3000 正在监听"
else
    echo "  ⚠️  端口 3000 未监听（前端服务可能未启动）"
fi

echo ""
echo "测试本地连接:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "  ✅ HTTP 连接正常 (状态码: $HTTP_CODE)"
else
    echo "  ⚠️  HTTP 连接异常 (状态码: $HTTP_CODE)"
fi

if [ -f "$SSL_CERT" ]; then
    HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://127.0.0.1/ 2>/dev/null || echo "000")
    if [ "$HTTPS_CODE" = "200" ] || [ "$HTTPS_CODE" = "301" ] || [ "$HTTPS_CODE" = "302" ]; then
        echo "  ✅ HTTPS 连接正常 (状态码: $HTTPS_CODE)"
    else
        echo "  ⚠️  HTTPS 连接异常 (状态码: $HTTPS_CODE)"
    fi
fi

echo ""
echo "=========================================="
echo "✅ Nginx 配置修复完成"
echo "=========================================="
echo ""
echo "配置摘要:"
echo "  - 配置文件: $NGINX_CONFIG"
echo "  - 域名: $DOMAIN"
echo "  - 前端代理: http://127.0.0.1:3000"
echo "  - 后端代理: http://127.0.0.1:8000/api/"
echo "  - WebSocket: 已启用"
echo ""
echo "如果浏览器仍然无法访问，请检查:"
echo "  1. 防火墙是否允许端口 80 和 443"
echo "  2. 域名 DNS 是否正确解析到服务器 IP"
echo "  3. PM2 服务是否正常运行: sudo -u ubuntu pm2 list"
echo "  4. Nginx 错误日志: sudo tail -f /var/log/nginx/aikz.error.log"
echo ""

