#!/bin/bash
# 完整重建所有前端项目
# 1. 停止所有服务
# 2. 清理旧构建产物
# 3. 重新构建所有项目
# 4. 正确启动所有服务

set -e

echo "=========================================="
echo "🔨 完整重建所有前端项目"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || exit 1

# 确保 Node.js 环境
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20.19.6 2>/dev/null || nvm use node 2>/dev/null || true

# 1. 停止所有前端服务
echo "1️⃣ 停止所有前端服务"
echo "----------------------------------------"

pm2 stop all 2>/dev/null || true
pm2 delete all 2>/dev/null || true

# 确保端口释放
for port in 3000 3001 3002 3003 3006 3007; do
    if sudo lsof -i :$port >/dev/null 2>&1; then
        echo "  释放端口 $port..."
        sudo lsof -ti :$port | xargs sudo kill -9 2>/dev/null || true
        sleep 1
    fi
done

echo "✅ 所有服务已停止"
echo ""

# 2. 清理旧构建产物
echo "2️⃣ 清理旧构建产物"
echo "----------------------------------------"

cleanup_project() {
    local dir=$1
    local name=$2
    
    if [ -d "$PROJECT_ROOT/$dir" ]; then
        echo "清理 $name ($dir)..."
        cd "$PROJECT_ROOT/$dir" || return
        
        # 清理构建产物
        rm -rf .next
        rm -rf dist
        rm -rf build
        rm -rf node_modules/.cache
        rm -rf .turbo
        
        echo "  ✅ $name 已清理"
        cd "$PROJECT_ROOT" || return
    else
        echo "  ⚠️  $name 目录不存在: $dir"
    fi
}

cleanup_project "saas-demo" "saas-demo (Next.js)"
cleanup_project "tgmini20251220" "tgmini (Vite)"
cleanup_project "react-vite-template/hbwy20251220" "hongbao (Vite)"
cleanup_project "aizkw20251219" "aizkw (Vite)"
cleanup_project "ai-monitor-frontend" "ai-monitor-frontend"
cleanup_project "sites-admin-frontend" "sites-admin-frontend"

echo "✅ 清理完成"
echo ""

# 3. 重新构建所有项目
echo "3️⃣ 重新构建所有项目"
echo "----------------------------------------"

build_nextjs() {
    local dir=$1
    local name=$2
    
    if [ -d "$PROJECT_ROOT/$dir" ]; then
        echo "构建 $name ($dir)..."
        cd "$PROJECT_ROOT/$dir" || return
        
        # 安装依赖
        if [ ! -d "node_modules" ]; then
            echo "  安装依赖..."
            npm install --production=false 2>&1 | tail -5
        else
            echo "  依赖已存在，跳过安装"
        fi
        
        # 构建
        echo "  开始构建（这可能需要几分钟）..."
        if npm run build 2>&1 | tee /tmp/build_${name}.log; then
            # 检查构建结果
            if [ -d ".next" ]; then
                echo "  ✅ $name 构建成功 (.next 目录已创建)"
            elif [ -d ".next/standalone" ]; then
                echo "  ✅ $name 构建成功 (standalone 模式)"
            else
                echo "  ⚠️  $name 构建完成，但未找到 .next 目录"
            fi
        else
            echo "  ❌ $name 构建失败"
            echo "  构建日志:"
            tail -20 /tmp/build_${name}.log | grep -A 5 "ERROR\|error\|failed" || tail -20 /tmp/build_${name}.log
            return 1
        fi
        
        cd "$PROJECT_ROOT" || return
        echo ""
    else
        echo "  ⚠️  $name 目录不存在: $dir"
        echo ""
    fi
}

build_vite() {
    local dir=$1
    local name=$2
    
    if [ -d "$PROJECT_ROOT/$dir" ]; then
        echo "构建 $name ($dir)..."
        cd "$PROJECT_ROOT/$dir" || return
        
        # 安装依赖
        if [ ! -d "node_modules" ]; then
            echo "  安装依赖..."
            npm install --production=false 2>&1 | tail -5
        else
            echo "  依赖已存在，跳过安装"
        fi
        
        # 构建
        echo "  开始构建（这可能需要几分钟）..."
        if npm run build 2>&1 | tee /tmp/build_${name}.log; then
            # 检查构建结果
            if [ -d "dist" ]; then
                echo "  ✅ $name 构建成功 (dist 目录已创建)"
                echo "  dist 目录大小: $(du -sh dist | cut -f1)"
            else
                echo "  ❌ $name 构建失败，未找到 dist 目录"
                echo "  构建日志:"
                tail -20 /tmp/build_${name}.log | grep -A 5 "ERROR\|error\|failed" || tail -20 /tmp/build_${name}.log
                return 1
            fi
        else
            echo "  ❌ $name 构建失败"
            echo "  构建日志:"
            tail -20 /tmp/build_${name}.log | grep -A 5 "ERROR\|error\|failed" || tail -20 /tmp/build_${name}.log
            return 1
        fi
        
        cd "$PROJECT_ROOT" || return
        echo ""
    else
        echo "  ⚠️  $name 目录不存在: $dir"
        echo ""
    fi
}

# 构建 Next.js 项目
build_nextjs "saas-demo" "saas-demo"

# 构建 Vite 项目
build_vite "tgmini20251220" "tgmini"
build_vite "react-vite-template/hbwy20251220" "hongbao"
build_vite "aizkw20251219" "aizkw"

# 构建其他前端项目（如果存在）
if [ -d "$PROJECT_ROOT/ai-monitor-frontend" ] && [ -f "$PROJECT_ROOT/ai-monitor-frontend/package.json" ]; then
    if grep -q "next" "$PROJECT_ROOT/ai-monitor-frontend/package.json"; then
        build_nextjs "ai-monitor-frontend" "ai-monitor-frontend"
    else
        build_vite "ai-monitor-frontend" "ai-monitor-frontend"
    fi
fi

if [ -d "$PROJECT_ROOT/sites-admin-frontend" ] && [ -f "$PROJECT_ROOT/sites-admin-frontend/package.json" ]; then
    if grep -q "next" "$PROJECT_ROOT/sites-admin-frontend/package.json"; then
        build_nextjs "sites-admin-frontend" "sites-admin-frontend"
    else
        build_vite "sites-admin-frontend" "sites-admin-frontend"
    fi
fi

echo "✅ 构建完成"
echo ""

# 4. 启动所有服务
echo "4️⃣ 启动所有服务"
echo "----------------------------------------"

# 确保 serve 已安装
if ! command -v serve >/dev/null 2>&1; then
    echo "安装 serve..."
    npm install -g serve 2>/dev/null || true
fi

# 启动 Next.js 服务
start_nextjs() {
    local dir=$1
    local name=$2
    local port=$3
    local pm2_name=$4
    
    if [ -d "$PROJECT_ROOT/$dir" ]; then
        cd "$PROJECT_ROOT/$dir" || return
        
        # 检查是否有 standalone 构建
        if [ -f ".next/standalone/server.js" ]; then
            echo "启动 $name (standalone 模式, 端口 $port)..."
            pm2 start ".next/standalone/server.js" \
                --name "$pm2_name" \
                --interpreter node \
                --cwd "$PROJECT_ROOT/$dir" \
                --env PORT=$port \
                --env NODE_ENV=production 2>&1 | tail -3
        elif [ -d ".next" ]; then
            echo "启动 $name (npm start, 端口 $port)..."
            export PORT=$port
            pm2 start npm \
                --name "$pm2_name" \
                --cwd "$PROJECT_ROOT/$dir" \
                -- start 2>&1 | tail -3
        else
            echo "  ❌ $name 未找到构建产物，跳过启动"
            return 1
        fi
        
        cd "$PROJECT_ROOT" || return
        echo ""
    fi
}

# 启动 Vite 服务
start_vite() {
    local dir=$1
    local name=$2
    local port=$3
    local pm2_name=$4
    
    if [ -d "$PROJECT_ROOT/$dir" ] && [ -d "$PROJECT_ROOT/$dir/dist" ]; then
        echo "启动 $name (serve dist, 端口 $port)..."
        pm2 start serve \
            --name "$pm2_name" \
            --cwd "$PROJECT_ROOT/$dir" \
            -- -s dist -l $port 2>&1 | tail -3
        echo ""
    else
        echo "  ❌ $name 未找到 dist 目录，跳过启动"
        echo ""
    fi
}

# 启动所有服务
start_nextjs "saas-demo" "saas-demo" 3000 "next-server"
start_vite "tgmini20251220" "tgmini" 3001 "tgmini-frontend"
start_vite "react-vite-template/hbwy20251220" "hongbao" 3002 "hongbao-frontend"
start_vite "aizkw20251219" "aizkw" 3003 "aizkw-frontend"

# 启动其他前端服务
if [ -d "$PROJECT_ROOT/ai-monitor-frontend/.next" ] || [ -d "$PROJECT_ROOT/ai-monitor-frontend/dist" ]; then
    if [ -d "$PROJECT_ROOT/ai-monitor-frontend/.next" ]; then
        start_nextjs "ai-monitor-frontend" "ai-monitor-frontend" 3006 "ai-monitor-frontend"
    else
        start_vite "ai-monitor-frontend" "ai-monitor-frontend" 3006 "ai-monitor-frontend"
    fi
fi

if [ -d "$PROJECT_ROOT/sites-admin-frontend/.next" ] || [ -d "$PROJECT_ROOT/sites-admin-frontend/dist" ]; then
    if [ -d "$PROJECT_ROOT/sites-admin-frontend/.next" ]; then
        start_nextjs "sites-admin-frontend" "sites-admin-frontend" 3007 "sites-admin-frontend"
    else
        start_vite "sites-admin-frontend" "sites-admin-frontend" 3007 "sites-admin-frontend"
    fi
fi

echo "✅ 服务启动完成"
echo ""

# 5. 等待服务启动
echo "5️⃣ 等待服务启动..."
echo "----------------------------------------"
sleep 10

# 6. 验证服务状态
echo "6️⃣ 验证服务状态"
echo "----------------------------------------"

check_service() {
    local port=$1
    local name=$2
    
    if sudo lsof -i :$port >/dev/null 2>&1 || sudo netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        # 测试 HTTP 响应
        local code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:$port 2>/dev/null || echo "000")
        if [ "$code" = "200" ] || [ "$code" = "404" ] || [ "$code" = "301" ] || [ "$code" = "302" ]; then
            echo "  ✅ $name (端口 $port): 运行中 (HTTP $code)"
        else
            echo "  ⚠️  $name (端口 $port): 端口监听但响应异常 (HTTP $code)"
        fi
    else
        echo "  ❌ $name (端口 $port): 未运行"
    fi
}

check_service 3000 "saas-demo"
check_service 3001 "tgmini"
check_service 3002 "hongbao"
check_service 3003 "aizkw"
check_service 3006 "ai-monitor-frontend"
check_service 3007 "sites-admin-frontend"

echo ""

# 7. 显示 PM2 状态
echo "7️⃣ PM2 进程状态"
echo "----------------------------------------"
pm2 list

echo ""
echo "=========================================="
echo "✅ 重建完成！"
echo "=========================================="
echo ""
echo "📋 服务状态:"
echo "  展示网站:"
echo "    - aikz.usdt2026.cc → 端口 3000 (saas-demo)"
echo "    - tgmini.usdt2026.cc → 端口 3001"
echo "    - hongbao.usdt2026.cc → 端口 3002"
echo "    - aizkw.usdt2026.cc → 端口 3003"
echo ""
echo "  管理后台:"
echo "    - ai-monitor → 端口 3006"
echo "    - sites-admin → 端口 3007"
echo ""
echo "💡 如果服务仍有问题，请检查:"
echo "   1. PM2 日志: pm2 logs <进程名>"
echo "   2. 构建日志: cat /tmp/build_<项目名>.log"
echo "   3. 端口监听: sudo lsof -i :端口号"
echo ""

