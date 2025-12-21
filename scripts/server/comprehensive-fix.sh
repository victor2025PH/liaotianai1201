#!/bin/bash
# ============================================================
# 全面修复部署问题 - 包含所有诊断和修复步骤
# ============================================================

set -e

echo "============================================================"
echo "🔧 全面修复部署问题"
echo "============================================================"
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 步骤 1: 检查并修复 Git Pull
echo "============================================================"
echo "步骤 1: 检查并修复 Git Pull"
echo "============================================================"
cd "$PROJECT_DIR" 2>/dev/null || {
    echo "⚠️  项目目录不存在，创建目录..."
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    git clone https://github.com/victor2025PH/liaotianai1201.git . || {
        echo "❌ Git clone 失败"
        exit 1
    }
}

# 处理未提交的更改
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    echo "⚠️  发现未提交的更改，暂存..."
    git stash push -m "Auto stash $(date +%Y%m%d_%H%M%S)" 2>/dev/null || {
        git fetch origin main
        git reset --hard origin/main
    }
fi

# 拉取最新代码
echo "📥 拉取最新代码..."
git fetch origin main || git fetch origin || true
git pull origin main || {
    echo "⚠️  Git pull 失败，使用 reset --hard..."
    git fetch origin main
    git reset --hard origin/main || {
        echo "❌ Git reset 失败"
        exit 1
    }
}
echo "✅ 代码已更新"
echo ""

# 步骤 2: 检查环境
echo "============================================================"
echo "步骤 2: 检查环境"
echo "============================================================"

# 检查 Node.js
if ! command -v node >/dev/null 2>&1; then
    echo "⚠️  Node.js 未安装，安装 Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs || {
        echo "❌ Node.js 安装失败"
        exit 1
    }
fi
echo "✅ Node.js: $(node -v)"

# 检查 npm
if ! command -v npm >/dev/null 2>&1; then
    echo "❌ npm 未安装"
    exit 1
fi
echo "✅ npm: $(npm -v)"

# 检查 PM2
if ! command -v pm2 >/dev/null 2>&1; then
    echo "⚠️  PM2 未安装，安装 PM2..."
    sudo npm install -g pm2
    pm2 startup systemd -u ubuntu --hp /home/ubuntu || true
fi
echo "✅ PM2: $(pm2 -v 2>/dev/null || echo '已安装')"

# 检查 serve
if ! command -v serve >/dev/null 2>&1; then
    echo "⚠️  serve 未安装，安装 serve..."
    sudo npm install -g serve
fi
echo "✅ serve: 已安装"
echo ""

# 步骤 3: 部署三个网站
echo "============================================================"
echo "步骤 3: 部署三个网站"
echo "============================================================"

SITES=(
    "tgmini20251220:tgmini.usdt2026.cc:3001:tgmini-frontend"
    "hbwy20251220:hongbao.usdt2026.cc:3002:hongbao-frontend"
    "aizkw20251219:aikz.usdt2026.cc:3003:aizkw-frontend"
)

for SITE_INFO in "${SITES[@]}"; do
    IFS=':' read -r DIR DOMAIN PORT PM2_NAME <<< "$SITE_INFO"
    SITE_DIR="$PROJECT_DIR/$DIR"
    
    echo ""
    echo "----------------------------------------"
    echo "🚀 部署: $DIR"
    echo "域名: $DOMAIN"
    echo "端口: $PORT"
    echo "----------------------------------------"
    
    # 检查目录
    if [ ! -d "$SITE_DIR" ]; then
        echo "❌ 目录不存在: $SITE_DIR"
        echo "当前项目目录内容:"
        ls -la "$PROJECT_DIR" | grep -E "tgmini|hbwy|aizkw" || ls -la "$PROJECT_DIR" | head -20
        continue
    fi
    
    cd "$SITE_DIR" || {
        echo "❌ 无法进入目录: $SITE_DIR"
        continue
    }
    
    # 显示当前目录
    echo "当前目录: $(pwd)"
    echo "目录内容:"
    ls -la | head -10
    
    # 检查 package.json
    if [ ! -f "package.json" ]; then
        echo "❌ package.json 不存在"
        echo "尝试查找 package.json..."
        find . -name "package.json" -type f 2>/dev/null | head -5
        continue
    fi
    
    echo "✅ 找到 package.json"
    
    # 清理旧的构建
    echo "🧹 清理旧的构建..."
    rm -rf node_modules/.cache dist .next
    
    # 安装依赖
    echo "📦 安装依赖..."
    npm install --legacy-peer-deps || npm install || {
        echo "❌ npm install 失败"
        continue
    }
    
    # 构建
    echo "🔨 构建项目..."
    export NODE_OPTIONS="--max-old-space-size=3072"
    npm run build || {
        echo "❌ npm run build 失败"
        echo "查看构建错误..."
        npm run build 2>&1 | tail -20
        continue
    }
    
    # 检查 dist 目录
    if [ ! -d "dist" ]; then
        echo "❌ dist 目录不存在，构建可能失败"
        echo "检查构建输出..."
        ls -la
        continue
    fi
    
    echo "✅ 构建成功，dist 目录大小: $(du -sh dist | cut -f1)"
    
    # 停止旧进程
    echo "🛑 停止旧进程..."
    pm2 delete "$PM2_NAME" 2>/dev/null || true
    
    # 停止占用端口的进程
    if sudo lsof -i :$PORT >/dev/null 2>&1; then
        echo "停止占用端口 $PORT 的进程..."
        sudo lsof -ti :$PORT | xargs sudo kill -9 2>/dev/null || true
        sleep 2
    fi
    
    # 启动服务
    echo "🚀 启动服务..."
    pm2 start serve \
        --name "$PM2_NAME" \
        -- "$SITE_DIR/dist" \
        --listen $PORT \
        --single \
        --no-clipboard \
        --no-open || {
        echo "❌ PM2 启动失败"
        pm2 logs "$PM2_NAME" --lines 10 --nostream 2>/dev/null || true
        continue
    }
    
    pm2 save || true
    
    # 等待启动
    echo "⏳ 等待服务启动..."
    sleep 5
    
    # 检查服务
    if sudo lsof -i :$PORT >/dev/null 2>&1; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT || echo "000")
        if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
            echo "✅ 服务已启动 (端口 $PORT, HTTP $HTTP_CODE)"
        else
            echo "⚠️  服务响应异常 (HTTP $HTTP_CODE)"
            pm2 logs "$PM2_NAME" --lines 10 --nostream 2>/dev/null || true
        fi
    else
        echo "❌ 服务启动失败，端口未监听"
        pm2 logs "$PM2_NAME" --lines 20 --nostream 2>/dev/null || true
    fi
done

# 保存 PM2 配置
pm2 save || true

echo ""
echo "============================================================"
echo "步骤 4: 配置 Nginx"
echo "============================================================"

# 检查 Nginx
if ! command -v nginx >/dev/null 2>&1; then
    echo "⚠️  Nginx 未安装，安装 Nginx..."
    sudo apt-get update
    sudo apt-get install -y nginx
fi

# 为每个网站配置 Nginx
for SITE_INFO in "${SITES[@]}"; do
    IFS=':' read -r DIR DOMAIN PORT PM2_NAME <<< "$SITE_INFO"
    
    echo "配置 Nginx: $DOMAIN -> 端口 $PORT"
    
    NGINX_CONFIG="/tmp/${DIR}.conf"
    
    # 检查 SSL 证书是否存在
    SSL_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    SSL_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
    
    if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
        # SSL 证书存在，配置 HTTPS
        cat > "$NGINX_CONFIG" << EOF
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name $DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate $SSL_CERT;
    ssl_certificate_key $SSL_KEY;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    client_max_body_size 50M;

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
    }
}
EOF
    else
        # SSL 证书不存在，只配置 HTTP
        echo "⚠️  SSL 证书不存在，配置 HTTP only"
        cat > "$NGINX_CONFIG" << EOF
# HTTP server (SSL certificate not found)
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 50M;

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
    }
}
EOF
    fi
    
    # 复制配置
    sudo cp "$NGINX_CONFIG" "/etc/nginx/sites-available/$DOMAIN"
    
    # 创建符号链接
    if [ ! -L "/etc/nginx/sites-enabled/$DOMAIN" ]; then
        sudo ln -s "/etc/nginx/sites-available/$DOMAIN" "/etc/nginx/sites-enabled/$DOMAIN"
    fi
done

# 测试 Nginx 配置
echo "测试 Nginx 配置..."
if sudo nginx -t; then
    echo "✅ Nginx 配置测试通过"
    # 重载 Nginx
    echo "重载 Nginx..."
    sudo systemctl reload nginx || sudo systemctl restart nginx || {
        echo "⚠️  Nginx reload 失败，查看状态..."
        sudo systemctl status nginx --no-pager -l || true
    }
else
    echo "❌ Nginx 配置测试失败"
    echo "查看详细错误..."
    sudo nginx -t 2>&1 | tail -20
    echo ""
    echo "⚠️  跳过 Nginx 配置，但服务已在端口上运行"
    echo "你可以手动配置 Nginx 或使用 Certbot 获取 SSL 证书"
fi

echo "✅ Nginx 配置完成"
echo ""

# 步骤 5: 验证部署
echo "============================================================"
echo "步骤 5: 验证部署"
echo "============================================================"

echo "PM2 进程列表:"
pm2 list
echo ""

echo "端口监听状态:"
for SITE_INFO in "${SITES[@]}"; do
    IFS=':' read -r DIR DOMAIN PORT PM2_NAME <<< "$SITE_INFO"
    if sudo lsof -i :$PORT >/dev/null 2>&1; then
        echo "✅ 端口 $PORT ($DOMAIN): 正在监听"
    else
        echo "❌ 端口 $PORT ($DOMAIN): 未监听"
    fi
done

echo ""
echo "============================================================"
echo "✅ 全面修复完成"
echo "============================================================"
echo ""
echo "访问网站:"
for SITE_INFO in "${SITES[@]}"; do
    IFS=':' read -r DIR DOMAIN PORT PM2_NAME <<< "$SITE_INFO"
    echo "  - https://$DOMAIN"
done
echo ""
