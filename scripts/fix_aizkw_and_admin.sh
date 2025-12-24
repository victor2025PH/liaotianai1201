#!/bin/bash
# 修复 aizkw 和管理后台
# 1. 修复 aizkw 构建问题（vite: not found）
# 2. 修复管理后台（sites-admin-frontend）

set -e

echo "=========================================="
echo "🔧 修复 aizkw 和管理后台"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || exit 1

# 确保 Node.js 环境
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20.19.6 2>/dev/null || nvm use node 2>/dev/null || true

# 1. 修复 aizkw (端口 3003)
echo "1️⃣ 修复 aizkw (端口 3003)"
echo "----------------------------------------"

# 查找 aizkw 项目路径
AIZKW_DIR=""
if [ -d "$PROJECT_ROOT/aizkw20251219" ] && [ -f "$PROJECT_ROOT/aizkw20251219/package.json" ]; then
    AIZKW_DIR="$PROJECT_ROOT/aizkw20251219"
elif [ -d "$PROJECT_ROOT/migrations/aizkw20251219" ] && [ -f "$PROJECT_ROOT/migrations/aizkw20251219/package.json" ]; then
    AIZKW_DIR="$PROJECT_ROOT/migrations/aizkw20251219"
else
    AIZKW_DIR=$(find "$PROJECT_ROOT" -maxdepth 5 -type f -name "package.json" 2>/dev/null | \
        grep -iE "aizkw" | \
        grep -v "/logs/" | \
        grep -v "/\.git/" | \
        grep -v "/node_modules/" | \
        head -1 | xargs dirname 2>/dev/null || echo "")
fi

if [ -z "$AIZKW_DIR" ] || [ ! -f "$AIZKW_DIR/package.json" ]; then
    echo "  ❌ 未找到 aizkw 项目"
    exit 1
fi

echo "找到 aizkw 项目: $AIZKW_DIR"
cd "$AIZKW_DIR" || exit 1

# 停止旧服务
pm2 delete aizkw-frontend 2>/dev/null || true
if sudo lsof -i :3003 >/dev/null 2>&1; then
    sudo lsof -ti :3003 | xargs sudo kill -9 2>/dev/null || true
    sleep 1
fi

# 清理旧构建
echo "清理旧构建..."
rm -rf dist node_modules/.cache

# 重新安装依赖（确保 vite 可用）
echo "重新安装依赖..."
npm install --production=false 2>&1 | tail -10

# 检查 vite 是否可用
if ! npx vite --version >/dev/null 2>&1; then
    echo "  ⚠️  vite 不可用，尝试全局安装..."
    npm install -g vite 2>/dev/null || true
fi

# 构建项目
echo "开始构建..."
if npm run build 2>&1 | tee /tmp/aizkw_build.log; then
    if [ -d "dist" ]; then
        echo "  ✅ aizkw 构建成功"
        echo "  dist 目录大小: $(du -sh dist | cut -f1)"
    else
        echo "  ❌ 构建完成但未找到 dist 目录"
        echo "  构建日志:"
        tail -30 /tmp/aizkw_build.log | grep -A 5 "ERROR\|error\|failed" || tail -20 /tmp/aizkw_build.log
        exit 1
    fi
else
    echo "  ❌ 构建失败"
    echo "  构建日志:"
    tail -30 /tmp/aizkw_build.log | grep -A 5 "ERROR\|error\|failed" || tail -20 /tmp/aizkw_build.log
    exit 1
fi

# 启动服务
echo "启动 aizkw-frontend..."
pm2 start serve \
    --name aizkw-frontend \
    --cwd "$AIZKW_DIR" \
    -- -s dist -l 3003

sleep 3

# 验证服务
if sudo lsof -i :3003 >/dev/null 2>&1; then
    local_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:3003 2>/dev/null || echo "000")
    if [ "$local_code" = "200" ] || [ "$local_code" = "404" ] || [ "$local_code" = "301" ] || [ "$local_code" = "302" ]; then
        echo "  ✅ aizkw-frontend 已启动 (HTTP $local_code)"
    else
        echo "  ⚠️  aizkw-frontend 启动但响应异常 (HTTP $local_code)"
    fi
else
    echo "  ❌ aizkw-frontend 启动失败"
fi

cd "$PROJECT_ROOT" || exit 1
echo ""

# 2. 修复管理后台 (sites-admin-frontend, 端口 3007)
echo "2️⃣ 修复管理后台 (sites-admin-frontend, 端口 3007)"
echo "----------------------------------------"

if [ -d "$PROJECT_ROOT/sites-admin-frontend" ] && [ -f "$PROJECT_ROOT/sites-admin-frontend/package.json" ]; then
    cd "$PROJECT_ROOT/sites-admin-frontend" || exit 1
    
    # 停止旧服务
    pm2 delete sites-admin-frontend 2>/dev/null || true
    if sudo lsof -i :3007 >/dev/null 2>&1; then
        sudo lsof -ti :3007 | xargs sudo kill -9 2>/dev/null || true
        sleep 1
    fi
    
    # 检查项目类型
    if grep -q "next" package.json 2>/dev/null; then
        echo "检测到 Next.js 项目"
        
        # 清理旧构建
        rm -rf .next node_modules/.cache
        
        # 安装依赖
        if [ ! -d "node_modules" ]; then
            echo "安装依赖..."
            npm install --production=false 2>&1 | tail -10
        fi
        
        # 构建
        echo "开始构建..."
        if npm run build 2>&1 | tee /tmp/sites_admin_build.log; then
            if [ -d ".next" ]; then
                echo "  ✅ sites-admin-frontend 构建成功"
                
                # 启动服务
                echo "启动 sites-admin-frontend..."
                export PORT=3007
                pm2 start npm \
                    --name sites-admin-frontend \
                    --cwd "$PROJECT_ROOT/sites-admin-frontend" \
                    -- start
                
                sleep 3
                
                # 验证服务
                if sudo lsof -i :3007 >/dev/null 2>&1; then
                    local_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:3007 2>/dev/null || echo "000")
                    if [ "$local_code" = "200" ] || [ "$local_code" = "404" ] || [ "$local_code" = "301" ] || [ "$local_code" = "302" ]; then
                        echo "  ✅ sites-admin-frontend 已启动 (HTTP $local_code)"
                    else
                        echo "  ⚠️  sites-admin-frontend 启动但响应异常 (HTTP $local_code)"
                    fi
                else
                    echo "  ❌ sites-admin-frontend 启动失败"
                fi
            else
                echo "  ❌ 构建完成但未找到 .next 目录"
                tail -20 /tmp/sites_admin_build.log
            fi
        else
            echo "  ❌ 构建失败"
            tail -30 /tmp/sites_admin_build.log | grep -A 5 "ERROR\|error\|failed" || tail -20 /tmp/sites_admin_build.log
        fi
    else
        echo "检测到 Vite 项目"
        
        # 清理旧构建
        rm -rf dist node_modules/.cache
        
        # 安装依赖
        if [ ! -d "node_modules" ]; then
            echo "安装依赖..."
            npm install --production=false 2>&1 | tail -10
        fi
        
        # 构建
        echo "开始构建..."
        if npm run build 2>&1 | tee /tmp/sites_admin_build.log; then
            if [ -d "dist" ]; then
                echo "  ✅ sites-admin-frontend 构建成功"
                
                # 启动服务
                echo "启动 sites-admin-frontend..."
                pm2 start serve \
                    --name sites-admin-frontend \
                    --cwd "$PROJECT_ROOT/sites-admin-frontend" \
                    -- -s dist -l 3007
                
                sleep 3
                
                # 验证服务
                if sudo lsof -i :3007 >/dev/null 2>&1; then
                    local_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:3007 2>/dev/null || echo "000")
                    if [ "$local_code" = "200" ] || [ "$local_code" = "404" ] || [ "$local_code" = "301" ] || [ "$local_code" = "302" ]; then
                        echo "  ✅ sites-admin-frontend 已启动 (HTTP $local_code)"
                    else
                        echo "  ⚠️  sites-admin-frontend 启动但响应异常 (HTTP $local_code)"
                    fi
                else
                    echo "  ❌ sites-admin-frontend 启动失败"
                fi
            else
                echo "  ❌ 构建完成但未找到 dist 目录"
                tail -20 /tmp/sites_admin_build.log
            fi
        else
            echo "  ❌ 构建失败"
            tail -30 /tmp/sites_admin_build.log | grep -A 5 "ERROR\|error\|failed" || tail -20 /tmp/sites_admin_build.log
        fi
    fi
    
    cd "$PROJECT_ROOT" || exit 1
else
    echo "  ⚠️  sites-admin-frontend 目录不存在"
fi

echo ""

# 3. 验证所有服务
echo "3️⃣ 验证所有服务"
echo "----------------------------------------"

check_service() {
    local port=$1
    local name=$2
    
    if sudo lsof -i :$port >/dev/null 2>&1; then
        local_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:$port 2>/dev/null || echo "000")
        if [ "$local_code" = "200" ] || [ "$local_code" = "404" ] || [ "$local_code" = "301" ] || [ "$local_code" = "302" ]; then
            echo "  ✅ $name (端口 $port): 运行中 (HTTP $local_code)"
        else
            echo "  ⚠️  $name (端口 $port): 运行中但响应异常 (HTTP $local_code)"
        fi
    else
        echo "  ❌ $name (端口 $port): 未运行"
    fi
}

check_service 3000 "saas-demo (aikz)"
check_service 3001 "tgmini"
check_service 3002 "hongbao"
check_service 3003 "aizkw"
check_service 3007 "sites-admin-frontend"

echo ""

# 4. 显示 PM2 状态
echo "4️⃣ PM2 进程状态"
echo "----------------------------------------"
pm2 list | grep -E "next-server|tgmini-frontend|hongbao-frontend|aizkw-frontend|sites-admin-frontend" || echo "未找到相关进程"

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "📋 访问地址:"
echo "  展示网站:"
echo "    - https://aikz.usdt2026.cc (端口 3000)"
echo "    - https://tgmini.usdt2026.cc (端口 3001)"
echo "    - https://hongbao.usdt2026.cc (端口 3002)"
echo "    - https://aizkw.usdt2026.cc (端口 3003)"
echo ""
echo "  管理后台:"
echo "    - https://aiadmin.usdt2026.cc/admin (端口 3007)"
echo ""

