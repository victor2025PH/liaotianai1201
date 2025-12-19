#!/bin/bash
# ============================================================
# 修复前端构建产物缺失问题
# ============================================================

echo "=========================================="
echo "🔧 修复前端构建产物缺失问题"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

# 1. 检查前端构建产物
echo "[1/5] 检查前端构建产物..."
echo "----------------------------------------"
cd "$FRONTEND_DIR" || exit 1

if [ ! -d ".next" ]; then
    echo "❌ .next 目录不存在，需要重新构建"
    NEED_BUILD=true
elif [ ! -f ".next/standalone/server.js" ]; then
    echo "❌ .next/standalone/server.js 不存在"
    
    # 检查是否有其他位置的 standalone
    STANDALONE_FOUND=$(find .next -name "server.js" -type f 2>/dev/null | head -1 || echo "")
    if [ -n "$STANDALONE_FOUND" ]; then
        echo "⚠️  在其他位置找到 server.js: $STANDALONE_FOUND"
        echo "   这可能是构建路径问题"
    fi
    
    NEED_BUILD=true
else
    echo "✅ 找到 standalone/server.js"
    ls -lh .next/standalone/server.js
    NEED_BUILD=false
fi
echo ""

# 2. 检查静态资源
echo "[2/5] 检查静态资源..."
echo "----------------------------------------"
if [ -d ".next/static" ]; then
    STATIC_COUNT=$(find .next/static -type f 2>/dev/null | wc -l)
    echo "✅ .next/static 存在（包含 $STATIC_COUNT 个文件）"
else
    echo "⚠️  .next/static 不存在"
    NEED_BUILD=true
fi
echo ""

# 3. 如果需要，重新构建前端
if [ "$NEED_BUILD" = true ]; then
    echo "[3/5] 重新构建前端..."
    echo "----------------------------------------"
    
    # 清理旧的构建
    echo "清理旧的构建产物..."
    rm -rf .next
    rm -f .next/lock
    
    # 检查内存和 Swap
    echo "检查系统资源..."
    free -h || true
    
    # 启用 Swap（如果存在）
    if [ -f /swapfile ]; then
        echo "启用 Swap..."
        sudo swapon /swapfile 2>/dev/null || true
        free -h || true
    fi
    
    # 安装依赖（如果需要）
    if [ ! -d "node_modules" ]; then
        echo "安装前端依赖..."
        export NODE_OPTIONS="--max-old-space-size=1536"
        npm install --prefer-offline --no-audit
    fi
    
    # 构建
    echo "开始构建前端（这可能需要几分钟）..."
    export NODE_OPTIONS="--max-old-space-size=1536"
    npm run build
    
    # 验证构建结果
    if [ ! -f ".next/standalone/server.js" ]; then
        echo "❌ 构建失败：server.js 仍然不存在"
        echo "检查构建输出..."
        ls -la .next/ 2>/dev/null || echo ".next 目录不存在"
        if [ -d ".next/standalone" ]; then
            echo "standalone 目录内容:"
            find .next/standalone -type f 2>/dev/null | head -20
        fi
        exit 1
    fi
    
    echo "✅ 构建完成"
else
    echo "[3/5] 跳过构建（构建产物已存在）..."
fi
echo ""

# 4. 处理静态资源（确保 standalone 目录完整）
echo "[4/5] 处理静态资源..."
echo "----------------------------------------"
if [ -d ".next/standalone" ]; then
    STANDALONE_DIR=".next/standalone"
    
    # 检查是否有嵌套的项目目录
    if [ -d ".next/standalone/saas-demo" ]; then
        STANDALONE_DIR=".next/standalone/saas-demo"
        echo "发现嵌套的 standalone 目录: $STANDALONE_DIR"
    fi
    
    # 确保 .next 目录存在
    mkdir -p "$STANDALONE_DIR/.next/static"
    mkdir -p "$STANDALONE_DIR/.next/server"
    
    # 复制静态资源
    if [ -d ".next/static" ]; then
        echo "复制静态资源..."
        cp -r .next/static/* "$STANDALONE_DIR/.next/static/" 2>/dev/null || true
    fi
    
    # 复制 public 目录
    if [ -d "public" ]; then
        echo "复制 public 目录..."
        cp -r public "$STANDALONE_DIR/" 2>/dev/null || true
    fi
    
    # 复制 server 目录
    if [ -d ".next/server" ]; then
        echo "复制 server 目录..."
        cp -r .next/server/* "$STANDALONE_DIR/.next/server/" 2>/dev/null || true
    fi
    
    echo "✅ 静态资源处理完成"
    echo "standalone 目录: $STANDALONE_DIR"
    ls -lh "$STANDALONE_DIR/server.js" 2>/dev/null || echo "⚠️  server.js 不在预期位置"
else
    echo "❌ .next/standalone 目录不存在"
    exit 1
fi
echo ""

# 5. 验证 ecosystem.config.js 路径
echo "[5/5] 验证 ecosystem.config.js 配置..."
echo "----------------------------------------"
cd "$PROJECT_DIR" || exit 1

if [ -f "ecosystem.config.js" ]; then
    # 检查配置中的路径
    FRONTEND_CWD=$(grep -A 5 '"name": "frontend"' ecosystem.config.js | grep '"cwd":' | cut -d'"' -f4 || echo "")
    FRONTEND_ARGS=$(grep -A 5 '"name": "frontend"' ecosystem.config.js | grep '"args":' | cut -d'"' -f4 || echo "")
    
    echo "配置中的 cwd: $FRONTEND_CWD"
    echo "配置中的 args: $FRONTEND_ARGS"
    
    # 检查实际路径
    if [ -n "$FRONTEND_ARGS" ]; then
        FULL_PATH="$FRONTEND_DIR/$FRONTEND_ARGS"
        if [ -f "$FULL_PATH" ]; then
            echo "✅ 配置文件路径正确: $FULL_PATH"
        else
            echo "❌ 配置文件路径不正确: $FULL_PATH"
            echo "实际 standalone 位置:"
            find "$FRONTEND_DIR/.next" -name "server.js" -type f 2>/dev/null || echo "未找到 server.js"
        fi
    fi
else
    echo "❌ ecosystem.config.js 不存在"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 如果重新构建了前端，请重启 PM2 服务："
echo "   sudo -u ubuntu pm2 restart frontend"
echo ""
echo "2. 如果问题仍然存在，检查："
echo "   ls -la $FRONTEND_DIR/.next/standalone/server.js"
echo "   sudo -u ubuntu pm2 logs frontend --lines 50"

