#!/bin/bash
# 诊断并修复所有问题
# 1. 检查服务状态
# 2. 检查构建产物
# 3. 检查 Nginx 配置
# 4. 修复发现的问题

set -e

echo "=========================================="
echo "🔍 诊断并修复所有问题"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || exit 1

# 1. 检查服务状态
echo "1️⃣ 检查服务状态"
echo "----------------------------------------"

check_port() {
    local port=$1
    local name=$2
    
    if sudo lsof -i :$port >/dev/null 2>&1 || sudo netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        local pid=$(sudo lsof -ti :$port 2>/dev/null | head -1 || sudo netstat -tlnp 2>/dev/null | grep ":$port " | grep -oP "pid=\K\d+" | head -1)
        local process=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
        echo "  ✅ $name (端口 $port): 运行中 (PID: $pid, 进程: $process)"
        
        # 测试 HTTP 响应
        local code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:$port 2>/dev/null || echo "000")
        if [ "$code" = "200" ] || [ "$code" = "404" ] || [ "$code" = "301" ] || [ "$code" = "302" ]; then
            echo "      HTTP 响应: $code"
        else
            echo "      ⚠️  HTTP 响应异常: $code"
        fi
    else
        echo "  ❌ $name (端口 $port): 未运行"
    fi
}

check_port 3000 "saas-demo (aikz)"
check_port 3001 "tgmini"
check_port 3002 "hongbao"
check_port 3003 "aizkw"
check_port 3006 "ai-monitor-frontend"
check_port 3007 "sites-admin-frontend"
check_port 8000 "admin-backend"

echo ""

# 2. 检查构建产物
echo "2️⃣ 检查构建产物"
echo "----------------------------------------"

check_build() {
    local dir=$1
    local name=$2
    local type=$3  # "nextjs" or "vite"
    
    if [ -d "$PROJECT_ROOT/$dir" ]; then
        if [ "$type" = "nextjs" ]; then
            if [ -d "$PROJECT_ROOT/$dir/.next" ]; then
                local size=$(du -sh "$PROJECT_ROOT/$dir/.next" 2>/dev/null | cut -f1)
                echo "  ✅ $name: .next 存在 ($size)"
                
                # 检查 standalone
                if [ -f "$PROJECT_ROOT/$dir/.next/standalone/server.js" ]; then
                    echo "      ✅ standalone 模式可用"
                else
                    echo "      ⚠️  standalone 模式不可用，将使用 npm start"
                fi
            else
                echo "  ❌ $name: .next 不存在，需要构建"
            fi
        elif [ "$type" = "vite" ]; then
            if [ -d "$PROJECT_ROOT/$dir/dist" ]; then
                local size=$(du -sh "$PROJECT_ROOT/$dir/dist" 2>/dev/null | cut -f1)
                local files=$(find "$PROJECT_ROOT/$dir/dist" -type f 2>/dev/null | wc -l)
                echo "  ✅ $name: dist 存在 ($size, $files 个文件)"
                
                # 检查 index.html
                if [ -f "$PROJECT_ROOT/$dir/dist/index.html" ]; then
                    echo "      ✅ index.html 存在"
                else
                    echo "      ❌ index.html 不存在"
                fi
            else
                echo "  ❌ $name: dist 不存在，需要构建"
            fi
        fi
    else
        echo "  ❌ $name: 目录不存在 ($dir)"
    fi
}

check_build "saas-demo" "saas-demo" "nextjs"
check_build "tgmini20251220" "tgmini" "vite"
check_build "react-vite-template/hbwy20251220" "hongbao" "vite"
check_build "aizkw20251219" "aizkw" "vite"
check_build "ai-monitor-frontend" "ai-monitor-frontend" "nextjs"
check_build "sites-admin-frontend" "sites-admin-frontend" "nextjs"

echo ""

# 3. 检查 PM2 进程
echo "3️⃣ 检查 PM2 进程"
echo "----------------------------------------"

pm2 list | grep -E "next-server|tgmini-frontend|hongbao-frontend|aizkw-frontend|ai-monitor-frontend|sites-admin-frontend|backend" || echo "未找到相关进程"

echo ""

# 4. 检查 Nginx 配置
echo "4️⃣ 检查 Nginx 配置"
echo "----------------------------------------"

check_nginx_config() {
    local domain=$1
    local expected_port=$2
    
    local config="/etc/nginx/sites-available/$domain"
    local enabled="/etc/nginx/sites-enabled/$domain"
    
    if [ -f "$config" ] || [ -L "$config" ]; then
        local actual_port=$(sudo grep -oP "proxy_pass http://127.0.0.1:\K[0-9]+" "$config" 2>/dev/null | head -1 || echo "")
        if [ "$actual_port" = "$expected_port" ]; then
            echo "  ✅ $domain: 配置正确 (端口 $expected_port)"
        else
            echo "  ⚠️  $domain: 端口不匹配 (期望: $expected_port, 实际: $actual_port)"
        fi
        
        if [ -L "$enabled" ]; then
            echo "      ✅ 已启用"
        else
            echo "      ⚠️  未启用，创建符号链接..."
            sudo ln -sf "$config" "$enabled"
            echo "      ✅ 已创建符号链接"
        fi
    else
        echo "  ❌ $domain: 配置文件不存在"
    fi
}

check_nginx_config "aikz.usdt2026.cc" "3000"
check_nginx_config "tgmini.usdt2026.cc" "3001"
check_nginx_config "hongbao.usdt2026.cc" "3002"
check_nginx_config "aizkw.usdt2026.cc" "3003"

# 检查管理后台配置
if [ -f "/etc/nginx/sites-available/aiadmin.usdt2026.cc" ]; then
    echo "  ✅ aiadmin.usdt2026.cc: 配置存在"
else
    echo "  ❌ aiadmin.usdt2026.cc: 配置不存在"
fi

echo ""

# 5. 测试 Nginx 配置
echo "5️⃣ 测试 Nginx 配置"
echo "----------------------------------------"

if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "  ✅ Nginx 配置语法正确"
    sudo systemctl reload nginx
    echo "  ✅ Nginx 已重新加载"
else
    echo "  ❌ Nginx 配置有错误:"
    sudo nginx -t
fi

echo ""

# 6. 修复缺失的服务
echo "6️⃣ 修复缺失的服务"
echo "----------------------------------------"

# 6.1 修复 hongbao (端口 3002)
if ! sudo lsof -i :3002 >/dev/null 2>&1; then
    echo "修复 hongbao (端口 3002)..."
    if [ -d "$PROJECT_ROOT/react-vite-template/hbwy20251220/dist" ]; then
        cd "$PROJECT_ROOT/react-vite-template/hbwy20251220"
        pm2 delete hongbao-frontend 2>/dev/null || true
        pm2 start serve --name hongbao-frontend -- -s dist -l 3002
        echo "  ✅ hongbao-frontend 已启动"
    else
        echo "  ⚠️  hongbao dist 不存在，需要构建"
    fi
    cd "$PROJECT_ROOT" || exit 1
fi

# 6.2 修复 aizkw (端口 3003)
if ! sudo lsof -i :3003 >/dev/null 2>&1; then
    echo "修复 aizkw (端口 3003)..."
    if [ -d "$PROJECT_ROOT/aizkw20251219/dist" ]; then
        cd "$PROJECT_ROOT/aizkw20251219"
        pm2 delete aizkw-frontend 2>/dev/null || true
        pm2 start serve --name aizkw-frontend -- -s dist -l 3003
        echo "  ✅ aizkw-frontend 已启动"
    else
        echo "  ⚠️  aizkw dist 不存在，需要构建"
    fi
    cd "$PROJECT_ROOT" || exit 1
fi

# 6.3 修复 saas-demo (端口 3000)
if ! sudo lsof -i :3000 >/dev/null 2>&1; then
    echo "修复 saas-demo (端口 3000)..."
    if [ -d "$PROJECT_ROOT/saas-demo/.next" ]; then
        cd "$PROJECT_ROOT/saas-demo"
        pm2 delete next-server 2>/dev/null || true
        
        if [ -f ".next/standalone/server.js" ]; then
            pm2 start ".next/standalone/server.js" \
                --name next-server \
                --interpreter node \
                --cwd "$PROJECT_ROOT/saas-demo" \
                --env PORT=3000 \
                --env NODE_ENV=production
        else
            export PORT=3000
            pm2 start npm --name next-server -- start
        fi
        echo "  ✅ next-server 已启动"
    else
        echo "  ⚠️  saas-demo .next 不存在，需要构建"
    fi
    cd "$PROJECT_ROOT" || exit 1
fi

# 6.4 修复后端服务 (端口 8000)
if ! sudo lsof -i :8000 >/dev/null 2>&1; then
    echo "修复后端服务 (端口 8000)..."
    if [ -d "$PROJECT_ROOT/admin-backend" ]; then
        cd "$PROJECT_ROOT/admin-backend"
        
        # 检查虚拟环境
        if [ ! -d ".venv" ]; then
            echo "  创建虚拟环境..."
            python3 -m venv .venv
        fi
        
        source .venv/bin/activate
        
        # 安装依赖（如果需要）
        if [ ! -f ".venv/bin/uvicorn" ]; then
            echo "  安装依赖..."
            pip install -r requirements.txt 2>&1 | tail -5
        fi
        
        # 启动服务
        pm2 delete backend luckyred-api 2>/dev/null || true
        pm2 start .venv/bin/uvicorn \
            --name backend \
            --interpreter none \
            -- app.main:app --host 0.0.0.0 --port 8000
        
        echo "  ✅ backend 已启动"
        cd "$PROJECT_ROOT" || exit 1
    else
        echo "  ❌ admin-backend 目录不存在"
    fi
fi

echo ""

# 7. 等待服务启动
echo "7️⃣ 等待服务启动..."
echo "----------------------------------------"
sleep 10

# 8. 最终验证
echo "8️⃣ 最终验证"
echo "----------------------------------------"

test_domain() {
    local domain=$1
    local port=$2
    
    # 测试本地端口
    local local_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:$port 2>/dev/null || echo "000")
    
    # 测试域名（通过 Nginx）
    local domain_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 -H "Host: $domain" http://127.0.0.1 2>/dev/null || echo "000")
    
    if [ "$local_code" = "200" ] || [ "$local_code" = "404" ] || [ "$local_code" = "301" ] || [ "$local_code" = "302" ]; then
        echo "  ✅ $domain (本地端口 $port): HTTP $local_code"
    else
        echo "  ❌ $domain (本地端口 $port): HTTP $local_code"
    fi
    
    if [ "$domain_code" = "200" ] || [ "$domain_code" = "404" ] || [ "$domain_code" = "301" ] || [ "$domain_code" = "302" ]; then
        echo "      ✅ Nginx 代理: HTTP $domain_code"
    else
        echo "      ⚠️  Nginx 代理: HTTP $domain_code"
    fi
}

test_domain "aikz.usdt2026.cc" 3000
test_domain "tgmini.usdt2026.cc" 3001
test_domain "hongbao.usdt2026.cc" 3002
test_domain "aizkw.usdt2026.cc" 3003

echo ""

# 9. 显示 PM2 状态
echo "9️⃣ PM2 进程状态"
echo "----------------------------------------"
pm2 list

echo ""
echo "=========================================="
echo "✅ 诊断和修复完成！"
echo "=========================================="
echo ""
echo "📋 问题总结:"
echo ""
echo "如果仍有 404 错误:"
echo "  1. 检查构建产物是否存在:"
echo "     ls -la saas-demo/.next"
echo "     ls -la tgmini20251220/dist"
echo "     ls -la react-vite-template/hbwy20251220/dist"
echo "     ls -la aizkw20251219/dist"
echo ""
echo "  2. 如果构建产物不存在，执行:"
echo "     sudo bash scripts/rebuild_all_frontends.sh"
echo ""
echo "如果仍有 502 错误 (aikz.usdt2026.cc):"
echo "  1. 检查后端服务:"
echo "     pm2 logs backend"
echo "     curl http://127.0.0.1:8000/health"
echo ""
echo "  2. 检查后端日志:"
echo "     tail -50 /home/ubuntu/.pm2/logs/backend-error.log"
echo ""

