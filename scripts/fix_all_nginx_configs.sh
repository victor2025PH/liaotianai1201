#!/bin/bash
# 修复所有 Nginx 配置中的端口错误
# 1. 修复 aikz.usdt2026.cc 端口（3003 → 3000）
# 2. 确保所有配置正确

set -e

echo "=========================================="
echo "🔧 修复所有 Nginx 配置"
echo "=========================================="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"

# 备份配置
BACKUP_DIR="/tmp/nginx_backup_$(date +%Y%m%d_%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"
echo "📦 备份现有配置到: $BACKUP_DIR"
sudo cp -r "$NGINX_AVAILABLE"/* "$BACKUP_DIR/" 2>/dev/null || true
echo "✅ 备份完成"
echo ""

# 1. 修复 aikz.usdt2026.cc 端口配置（3003 → 3000）
echo "1️⃣ 修复 aikz.usdt2026.cc 端口配置（3003 → 3000）"
echo "----------------------------------------"

AIKZ_CONFIG="$NGINX_AVAILABLE/aikz.usdt2026.cc"
if [ -f "$AIKZ_CONFIG" ]; then
    echo "找到配置文件: $AIKZ_CONFIG"
    
    # 检查当前配置
    CURRENT_PORT=$(sudo grep -oP "proxy_pass http://127.0.0.1:\K[0-9]+" "$AIKZ_CONFIG" | head -1 || echo "")
    echo "当前端口: ${CURRENT_PORT:-未找到}"
    
    if [ "$CURRENT_PORT" = "3003" ]; then
        echo "⚠️  发现错误端口 3003，正在修复为 3000..."
        sudo sed -i.bak 's|proxy_pass http://127.0.0.1:3003|proxy_pass http://127.0.0.1:3000|g' "$AIKZ_CONFIG"
        sudo sed -i.bak 's|127\.0\.0\.1:3003|127.0.0.1:3000|g' "$AIKZ_CONFIG"
        rm -f "$AIKZ_CONFIG.bak"
        echo "✅ 已修复为端口 3000"
    elif [ "$CURRENT_PORT" = "3000" ]; then
        echo "✅ 端口配置正确（3000）"
    else
        echo "⚠️  端口为 $CURRENT_PORT，预期 3000"
    fi
else
    echo "⚠️  配置文件不存在: $AIKZ_CONFIG"
    echo "   将创建新配置..."
    
    # 检查 SSL 证书
    SSL_CERT="/etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem"
    SSL_KEY="/etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem"
    HAS_SSL=false
    
    if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
        HAS_SSL=true
        echo "✅ 检测到 SSL 证书"
    fi
    
    # 创建配置文件
    if [ "$HAS_SSL" = true ]; then
        sudo tee "$AIKZ_CONFIG" > /dev/null << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name aikz.usdt2026.cc;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name aikz.usdt2026.cc;

    ssl_certificate /etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 50M;

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
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # 前端应用（端口 3000 - saas-demo）
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF
    else
        sudo tee "$AIKZ_CONFIG" > /dev/null << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name aikz.usdt2026.cc;

    client_max_body_size 50M;

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

    # 前端应用（端口 3000 - saas-demo）
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF
    fi
    
    echo "✅ 已创建配置文件"
fi

# 确保符号链接存在
if [ ! -L "$NGINX_ENABLED/aikz.usdt2026.cc" ]; then
    echo "🔗 创建符号链接..."
    sudo ln -s "$AIKZ_CONFIG" "$NGINX_ENABLED/aikz.usdt2026.cc"
    echo "✅ 符号链接已创建"
fi

echo ""
echo "2️⃣ 验证其他网站的配置"
echo "----------------------------------------"

# 定义正确的映射
declare -A CORRECT_MAPPING=(
    ["tgmini.usdt2026.cc"]="3001"
    ["hongbao.usdt2026.cc"]="3002"
    ["aizkw.usdt2026.cc"]="3003"
    ["aikz.usdt2026.cc"]="3000"
)

for domain in "${!CORRECT_MAPPING[@]}"; do
    expected_port="${CORRECT_MAPPING[$domain]}"
    config_file="$NGINX_AVAILABLE/$domain"
    
    if [ -f "$config_file" ] || [ -L "$config_file" ]; then
        actual_port=$(sudo grep -oP "proxy_pass http://127.0.0.1:\K[0-9]+" "$config_file" 2>/dev/null | head -1 || echo "")
        if [ "$actual_port" = "$expected_port" ]; then
            echo "✅ $domain → 端口 $expected_port (正确)"
        elif [ -n "$actual_port" ]; then
            echo "⚠️  $domain → 端口 $actual_port (应该是 $expected_port)"
        else
            echo "⚠️  $domain → 未找到端口配置"
        fi
    else
        echo "⚠️  $domain → 配置文件不存在"
    fi
done

echo ""
echo "3️⃣ 测试 Nginx 配置"
echo "----------------------------------------"

if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
    
    # 重新加载 Nginx
    echo ""
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
            sudo systemctl status nginx --no-pager -l | head -20
            exit 1
        fi
    fi
else
    echo "❌ Nginx 配置语法错误:"
    sudo nginx -t
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "📋 端口映射:"
echo "  - aikz.usdt2026.cc → 端口 3000 (saas-demo)"
echo "  - tgmini.usdt2026.cc → 端口 3001"
echo "  - hongbao.usdt2026.cc → 端口 3002"
echo "  - aizkw.usdt2026.cc → 端口 3003"
echo ""
echo "💡 备份位置: $BACKUP_DIR"
echo ""

