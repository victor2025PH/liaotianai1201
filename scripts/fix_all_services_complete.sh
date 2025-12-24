#!/bin/bash
# 完整修复所有服务和配置
# 1. 修复 Nginx 配置
# 2. 检查并启动所有服务
# 3. 验证服务可访问性

set -e

echo "=========================================="
echo "🔧 完整修复所有服务和配置"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"

cd "$PROJECT_ROOT" || exit 1

# 备份配置
BACKUP_DIR="/tmp/complete_fix_backup_$(date +%Y%m%d_%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"
echo "📦 备份现有配置到: $BACKUP_DIR"
sudo cp -r "$NGINX_AVAILABLE"/* "$BACKUP_DIR/" 2>/dev/null || true
echo "✅ 备份完成"
echo ""

# 正确的端口和服务映射
declare -A SERVICES=(
    ["aikz.usdt2026.cc:3000"]="saas-demo:next-server"
    ["tgmini.usdt2026.cc:3001"]="tgmini20251220:tgmini-frontend"
    ["hongbao.usdt2026.cc:3002"]="hbwy20251220:hongbao-frontend"
    ["aizkw.usdt2026.cc:3003"]="aizkw20251219:aizkw-frontend"
    ["aiadmin.usdt2026.cc:8000"]="admin-backend:backend"
    ["aiadmin.usdt2026.cc:3006"]="ai-monitor-frontend:ai-monitor-frontend"
    ["aiadmin.usdt2026.cc:3007"]="sites-admin-frontend:sites-admin-frontend"
)

# 1. 修复 Nginx 配置
echo "1️⃣ 修复 Nginx 配置"
echo "----------------------------------------"

# 1.1 修复展示网站配置
declare -A CORRECT_PORTS=(
    ["aikz.usdt2026.cc"]="3000"
    ["tgmini.usdt2026.cc"]="3001"
    ["hongbao.usdt2026.cc"]="3002"
    ["aizkw.usdt2026.cc"]="3003"
)

for domain in "${!CORRECT_PORTS[@]}"; do
    port="${CORRECT_PORTS[$domain]}"
    config_file="$NGINX_AVAILABLE/$domain"
    
    echo "检查 $domain (端口 $port)..."
    
    if [ -f "$config_file" ]; then
        current_port=$(sudo grep -oP "proxy_pass http://127.0.0.1:\K[0-9]+" "$config_file" 2>/dev/null | head -1 || echo "")
        if [ "$current_port" != "$port" ] && [ -n "$current_port" ]; then
            echo "  ⚠️  端口错误 ($current_port → $port)，正在修复..."
            sudo sed -i.bak "s|proxy_pass http://127.0.0.1:$current_port|proxy_pass http://127.0.0.1:$port|g" "$config_file"
            sudo sed -i.bak "s|127\.0\.0\.1:$current_port|127.0.0.1:$port|g" "$config_file"
            rm -f "$config_file.bak"
            echo "  ✅ 已修复"
        else
            echo "  ✅ 端口配置正确 ($port)"
        fi
        
        if [ ! -L "$NGINX_ENABLED/$domain" ]; then
            sudo ln -s "$config_file" "$NGINX_ENABLED/$domain"
            echo "  ✅ 已创建符号链接"
        fi
    else
        echo "  ⚠️  配置文件不存在: $config_file"
    fi
done

# 1.2 创建/修复 aiadmin.usdt2026.cc 配置
ADMIN_CONFIG="$NGINX_AVAILABLE/aiadmin.usdt2026.cc"
ADMIN_ENABLED="$NGINX_ENABLED/aiadmin.usdt2026.cc"

if [ ! -f "$ADMIN_CONFIG" ] && [ ! -L "$ADMIN_CONFIG" ]; then
    echo "创建管理后台配置..."
    
    SSL_CERT="/etc/letsencrypt/live/aiadmin.usdt2026.cc/fullchain.pem"
    SSL_KEY="/etc/letsencrypt/live/aiadmin.usdt2026.cc/privkey.pem"
    HAS_SSL=false
    
    if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
        HAS_SSL=true
    fi
    
    if [ "$HAS_SSL" = true ]; then
        sudo tee "$ADMIN_CONFIG" > /dev/null << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name aiadmin.usdt2026.cc;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name aiadmin.usdt2026.cc;

    ssl_certificate /etc/letsencrypt/live/aiadmin.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aiadmin.usdt2026.cc/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 50M;
    access_log /var/log/nginx/aiadmin-access.log;
    error_log /var/log/nginx/aiadmin-error.log;

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

    location /ai-monitor {
        proxy_pass http://127.0.0.1:3006;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        rewrite ^/ai-monitor/?(.*) /$1 break;
    }

    location /admin {
        proxy_pass http://127.0.0.1:3007;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        rewrite ^/admin/?(.*) /$1 break;
    }

    location = / {
        return 301 /admin;
    }
}
EOF
    else
        sudo tee "$ADMIN_CONFIG" > /dev/null << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name aiadmin.usdt2026.cc;

    client_max_body_size 50M;
    access_log /var/log/nginx/aiadmin-access.log;
    error_log /var/log/nginx/aiadmin-error.log;

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

    location /ai-monitor {
        proxy_pass http://127.0.0.1:3006;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        rewrite ^/ai-monitor/?(.*) /$1 break;
    }

    location /admin {
        proxy_pass http://127.0.0.1:3007;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        rewrite ^/admin/?(.*) /$1 break;
    }

    location = / {
        return 301 /admin;
    }
}
EOF
    fi
    
    sudo ln -sf "$ADMIN_CONFIG" "$ADMIN_ENABLED"
    echo "✅ 管理后台配置已创建"
fi

echo ""

# 2. 测试 Nginx 配置
echo "2️⃣ 测试 Nginx 配置"
echo "----------------------------------------"

if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
    sudo systemctl reload nginx
    echo "✅ Nginx 已重新加载"
else
    echo "❌ Nginx 配置有错误:"
    sudo nginx -t
    echo ""
    echo "⚠️  请先修复 Nginx 配置错误"
    exit 1
fi

echo ""

# 3. 检查并启动服务
echo "3️⃣ 检查并启动服务"
echo "----------------------------------------"

# 3.1 检查后端服务 (端口 8000)
echo "检查后端服务 (端口 8000)..."
if sudo lsof -i :8000 >/dev/null 2>&1 || sudo netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
    echo "  ✅ 后端服务正在运行"
else
    echo "  ⚠️  后端服务未运行，尝试启动..."
    if [ -d "$PROJECT_ROOT/admin-backend" ]; then
        cd "$PROJECT_ROOT/admin-backend"
        if pm2 list | grep -q "backend\|luckyred-api"; then
            pm2 restart backend luckyred-api 2>/dev/null || true
        else
            if [ -f ".venv/bin/uvicorn" ]; then
                pm2 start .venv/bin/uvicorn --name backend --interpreter none -- \
                    app.main:app --host 0.0.0.0 --port 8000 || true
            fi
        fi
        cd "$PROJECT_ROOT"
    fi
fi

# 3.2 检查并启动展示网站服务
start_frontend_service() {
    local port=$1
    local dir=$2
    local pm2_name=$3
    local domain=$4
    
    echo "检查 $domain (端口 $port)..."
    
    if sudo lsof -i :$port >/dev/null 2>&1 || sudo netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        echo "  ✅ 端口 $port 正在监听"
    else
        echo "  ⚠️  端口 $port 未监听，尝试启动服务..."
        
        if [ -d "$PROJECT_ROOT/$dir" ]; then
            cd "$PROJECT_ROOT/$dir"
            
            # 检查是否是 Next.js 项目
            if [ -f "package.json" ] && grep -q "next" package.json; then
                if [ ! -d ".next" ]; then
                    echo "    构建 Next.js 项目..."
                    npm install --production=false 2>/dev/null || true
                    npm run build 2>/dev/null || true
                fi
                if pm2 list | grep -q "$pm2_name"; then
                    pm2 restart "$pm2_name" 2>/dev/null || true
                else
                    export PORT=$port
                    pm2 start npm --name "$pm2_name" -- start 2>/dev/null || true
                fi
            # 检查是否是 Vite 项目
            elif [ -f "package.json" ] && grep -q "vite" package.json; then
                if [ ! -d "dist" ]; then
                    echo "    构建 Vite 项目..."
                    npm install --production=false 2>/dev/null || true
                    npm run build 2>/dev/null || true
                fi
                if [ -d "dist" ]; then
                    if pm2 list | grep -q "$pm2_name"; then
                        pm2 restart "$pm2_name" 2>/dev/null || true
                    else
                        if command -v serve >/dev/null 2>&1; then
                            pm2 start serve --name "$pm2_name" -- -s dist -l $port 2>/dev/null || true
                        else
                            npm install -g serve 2>/dev/null || true
                            pm2 start serve --name "$pm2_name" -- -s dist -l $port 2>/dev/null || true
                        fi
                    fi
                fi
            fi
            
            cd "$PROJECT_ROOT"
        fi
    fi
}

start_frontend_service 3000 "saas-demo" "next-server" "aikz.usdt2026.cc"
start_frontend_service 3001 "tgmini20251220" "tgmini-frontend" "tgmini.usdt2026.cc"
start_frontend_service 3002 "hbwy20251220" "hongbao-frontend" "hongbao.usdt2026.cc"
start_frontend_service 3003 "aizkw20251219" "aizkw-frontend" "aizkw.usdt2026.cc"
start_frontend_service 3006 "ai-monitor-frontend" "ai-monitor-frontend" "ai-monitor"
start_frontend_service 3007 "sites-admin-frontend" "sites-admin-frontend" "sites-admin"

echo ""

# 4. 等待服务启动
echo "4️⃣ 等待服务启动..."
echo "----------------------------------------"
sleep 5

# 5. 验证服务可访问性
echo "5️⃣ 验证服务可访问性"
echo "----------------------------------------"

test_service() {
    local port=$1
    local name=$2
    
    if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:$port 2>/dev/null | grep -q "200\|404\|301\|302"; then
        local code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:$port 2>/dev/null)
        echo "  ✅ $name (端口 $port): 可访问 (HTTP $code)"
    else
        echo "  ❌ $name (端口 $port): 不可访问"
    fi
}

test_service 3000 "aikz.usdt2026.cc"
test_service 3001 "tgmini.usdt2026.cc"
test_service 3002 "hongbao.usdt2026.cc"
test_service 3003 "aizkw.usdt2026.cc"
test_service 3006 "ai-monitor-frontend"
test_service 3007 "sites-admin-frontend"
test_service 8000 "admin-backend"

echo ""

# 6. 显示 PM2 进程状态
echo "6️⃣ PM2 进程状态"
echo "----------------------------------------"
pm2 list | grep -E "next-server|tgmini-frontend|hongbao-frontend|aizkw-frontend|ai-monitor-frontend|sites-admin-frontend|backend|luckyred-api" || echo "未找到相关进程"

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "📋 服务状态:"
echo "  展示网站:"
echo "    - aikz.usdt2026.cc → 端口 3000"
echo "    - tgmini.usdt2026.cc → 端口 3001"
echo "    - hongbao.usdt2026.cc → 端口 3002"
echo "    - aizkw.usdt2026.cc → 端口 3003"
echo ""
echo "  管理后台 (aiadmin.usdt2026.cc):"
echo "    - /api/ → 端口 8000"
echo "    - /admin → 端口 3007"
echo "    - /ai-monitor → 端口 3006"
echo ""
echo "💡 如果服务仍无法访问，请检查:"
echo "   1. PM2 进程是否运行: pm2 list"
echo "   2. 端口是否监听: sudo lsof -i :端口号"
echo "   3. 服务日志: pm2 logs 进程名"
echo ""

