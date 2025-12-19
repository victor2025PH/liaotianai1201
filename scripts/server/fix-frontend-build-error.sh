#!/bin/bash
# ============================================================
# 修复前端构建错误：服务器端代码被错误打包到客户端
# ============================================================

echo "=========================================="
echo "🔧 修复前端构建错误"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

# 1. 停止前端服务
echo "[1/6] 停止前端服务..."
echo "----------------------------------------"
sudo -u ubuntu pm2 stop frontend 2>/dev/null || true
sudo -u ubuntu pm2 delete frontend 2>/dev/null || true
sleep 2
echo "✅ 前端服务已停止"
echo ""

# 2. 清理旧的构建产物
echo "[2/6] 清理旧的构建产物..."
echo "----------------------------------------"
cd "$FRONTEND_DIR" || exit 1

# 删除 .next 目录
rm -rf .next
echo "✅ 已清理 .next 目录"

# 清理 node_modules/.cache（如果有）
rm -rf node_modules/.cache 2>/dev/null || true
echo "✅ 已清理缓存"
echo ""

# 3. 检查 Next.js 配置
echo "[3/6] 检查 Next.js 配置..."
echo "----------------------------------------"
if [ -f "next.config.ts" ]; then
    echo "✅ next.config.ts 存在"
    # 检查是否有 output: "standalone"
    if grep -q 'output.*standalone' next.config.ts; then
        echo "✅ standalone 模式已启用"
    else
        echo "⚠️  standalone 模式未启用"
    fi
else
    echo "❌ next.config.ts 不存在"
    exit 1
fi
echo ""

# 4. 检查客户端组件标记
echo "[4/6] 检查客户端组件标记..."
echo "----------------------------------------"
# 查找可能缺少 'use client' 的组件
echo "检查主要组件文件..."
MISSING_CLIENT_DIRECTIVE=0

check_file() {
    local file="$1"
    if [ -f "$file" ]; then
        # 检查是否使用了客户端特性但没有 'use client'
        if grep -q "useState\|useEffect\|useRouter\|window\|document" "$file" 2>/dev/null; then
            if ! grep -q "'use client'" "$file" 2>/dev/null && ! grep -q '"use client"' "$file" 2>/dev/null; then
                echo "  ⚠️  $file 使用了客户端特性但缺少 'use client'"
                MISSING_CLIENT_DIRECTIVE=1
            fi
        fi
    fi
}

check_file "src/app/page.tsx"
check_file "src/components/layout-wrapper.tsx"
check_file "src/components/sidebar.tsx"
check_file "src/components/header.tsx"

if [ $MISSING_CLIENT_DIRECTIVE -eq 0 ]; then
    echo "✅ 客户端组件标记检查通过"
else
    echo "⚠️  发现可能缺少 'use client' 的组件"
fi
echo ""

# 5. 重新安装依赖（确保版本正确）
echo "[5/6] 重新安装依赖..."
echo "----------------------------------------"
# 使用正确的 Node.js 版本
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20 2>/dev/null || nvm use node 2>/dev/null || true

# 清理并重新安装
rm -rf node_modules package-lock.json 2>/dev/null || true
npm install --prefer-offline --no-audit
if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi
echo "✅ 依赖已重新安装"
echo ""

# 6. 重新构建前端
echo "[6/6] 重新构建前端..."
echo "----------------------------------------"
export NODE_ENV=production
export NODE_OPTIONS="--max-old-space-size=2048"
export NEXT_TELEMETRY_DISABLED=1

echo "开始构建..."
npm run build 2>&1 | tee /tmp/frontend-build.log

BUILD_EXIT_CODE=${PIPESTATUS[0]}

if [ $BUILD_EXIT_CODE -ne 0 ]; then
    echo "❌ 构建失败，退出码: $BUILD_EXIT_CODE"
    echo "构建日志已保存到 /tmp/frontend-build.log"
    echo ""
    echo "最后 50 行错误日志:"
    tail -50 /tmp/frontend-build.log
    exit 1
fi

echo "✅ 构建成功"
echo ""

# 7. 检查构建产物
echo "=========================================="
echo "🔍 检查构建产物"
echo "=========================================="
echo ""

# 检查 standalone 目录
STANDALONE_DIR=".next/standalone"
if [ ! -d "$STANDALONE_DIR" ]; then
    STANDALONE_DIR=$(find .next/standalone -type f -name "server.js" 2>/dev/null | head -1 | xargs dirname 2>/dev/null)
fi

if [ -z "$STANDALONE_DIR" ] || [ ! -d "$STANDALONE_DIR" ]; then
    echo "❌ standalone 目录不存在"
    exit 1
fi

echo "✅ standalone 目录: $STANDALONE_DIR"

# 检查 server.js
if [ -f "$STANDALONE_DIR/server.js" ]; then
    echo "✅ server.js 存在"
else
    echo "❌ server.js 不存在"
    exit 1
fi

# 检查静态文件
if [ -d ".next/static" ]; then
    echo "✅ static 目录存在"
    STATIC_COUNT=$(find .next/static -name "*.js" | wc -l)
    echo "  静态 JS 文件数量: $STATIC_COUNT"
else
    echo "❌ static 目录不存在"
    exit 1
fi

# 检查是否有服务器端代码泄漏到客户端
echo ""
echo "检查客户端 bundle 中是否包含服务器端代码..."
CLIENT_BUNDLES=$(find .next/static/chunks -name "*.js" -type f 2>/dev/null | head -5)
SERVER_CODE_FOUND=0

for bundle in $CLIENT_BUNDLES; do
    if grep -q "Server\|server\|SERVER" "$bundle" 2>/dev/null; then
        # 检查是否是正常的客户端代码（如 'use server' 字符串）
        if grep -q "'use server'\|\\\"use server\\\"" "$bundle" 2>/dev/null; then
            continue
        fi
        # 检查是否包含 Node.js 模块
        if grep -q "require.*fs\|require.*path\|require.*http" "$bundle" 2>/dev/null; then
            echo "  ⚠️  发现服务器端代码在客户端 bundle 中: $bundle"
            SERVER_CODE_FOUND=1
        fi
    fi
done

if [ $SERVER_CODE_FOUND -eq 0 ]; then
    echo "✅ 未发现明显的服务器端代码泄漏"
else
    echo "⚠️  可能发现服务器端代码泄漏，需要进一步检查"
fi
echo ""

# 8. 处理静态资源
echo "=========================================="
echo "📂 处理静态资源"
echo "=========================================="
echo ""

# 确保目录结构完整
mkdir -p "$STANDALONE_DIR/.next/static"
mkdir -p "$STANDALONE_DIR/.next/server"
mkdir -p "$STANDALONE_DIR/.next"

# 复制 BUILD_ID
if [ -f ".next/BUILD_ID" ]; then
    cp .next/BUILD_ID "$STANDALONE_DIR/.next/BUILD_ID" 2>/dev/null || true
    echo "✅ BUILD_ID 已复制"
fi

# 复制所有 JSON 配置文件
for json_file in .next/*.json; do
    if [ -f "$json_file" ]; then
        cp "$json_file" "$STANDALONE_DIR/.next/" 2>/dev/null || true
    fi
done
echo "✅ JSON 配置文件已复制"

# 复制 static 目录
if [ -d ".next/static" ]; then
    cp -r .next/static/* "$STANDALONE_DIR/.next/static/" 2>/dev/null || true
    echo "✅ static 目录已复制"
fi

# 复制 server 目录
if [ -d ".next/server" ]; then
    cp -r .next/server/* "$STANDALONE_DIR/.next/server/" 2>/dev/null || true
    echo "✅ server 目录已复制"
fi

# 复制 public 目录
if [ -d "public" ]; then
    cp -r public "$STANDALONE_DIR/" 2>/dev/null || true
    echo "✅ public 目录已复制"
fi
echo ""

# 9. 启动前端服务
echo "=========================================="
echo "🚀 启动前端服务"
echo "=========================================="
echo ""

cd "$PROJECT_DIR" || exit 1
sudo -u ubuntu pm2 start ecosystem.config.js --only frontend
sleep 5

echo "检查服务状态:"
sudo -u ubuntu pm2 list | grep frontend
echo ""

# 10. 验证服务
echo "=========================================="
echo "🧪 验证服务"
echo "=========================================="
echo ""

echo "等待服务启动 (15秒)..."
sleep 15

echo "检查端口 3000:"
PORT_3000=$(sudo ss -tlnp | grep ":3000 " || echo "")
if [ -n "$PORT_3000" ]; then
    echo "✅ 端口 3000 正在监听"
    echo "   $PORT_3000"
else
    echo "❌ 端口 3000 未监听"
    echo "查看前端日志:"
    sudo -u ubuntu pm2 logs frontend --lines 50 --nostream 2>&1 | tail -50
    exit 1
fi
echo ""

echo "测试前端服务:"
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/ 2>/dev/null || echo "000")
if [ "$FRONTEND_RESPONSE" = "200" ]; then
    echo "✅ 前端服务正常 (HTTP $FRONTEND_RESPONSE)"
else
    echo "⚠️  前端服务响应: HTTP $FRONTEND_RESPONSE"
fi
echo ""

echo "测试 Nginx 代理:"
NGINX_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ 2>/dev/null || echo "000")
if [ "$NGINX_RESPONSE" = "200" ] || [ "$NGINX_RESPONSE" = "301" ] || [ "$NGINX_RESPONSE" = "302" ]; then
    echo "✅ Nginx 代理正常 (HTTP $NGINX_RESPONSE)"
else
    echo "⚠️  Nginx 代理响应: HTTP $NGINX_RESPONSE"
    echo "查看 Nginx 错误日志:"
    sudo tail -20 /var/log/nginx/aikz.error.log 2>/dev/null || true
fi
echo ""

echo "=========================================="
echo "✅ 前端构建修复完成"
echo "=========================================="
echo ""
echo "如果浏览器仍然显示错误，请："
echo "1. 清除浏览器缓存并硬刷新 (Ctrl+Shift+R)"
echo "2. 检查浏览器控制台的具体错误信息"
echo "3. 查看前端日志: sudo -u ubuntu pm2 logs frontend --lines 100"
echo "4. 查看构建日志: cat /tmp/frontend-build.log"
echo ""

