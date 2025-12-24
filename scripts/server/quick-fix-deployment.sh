#!/bin/bash
# ============================================================
# 快速修复部署问题
# ============================================================

set -e

echo "============================================================"
echo "🔧 快速修复部署问题"
echo "============================================================"
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 确保项目目录存在
if [ ! -d "$PROJECT_DIR" ]; then
    echo "创建项目目录..."
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    git clone https://github.com/victor2025PH/liaotianai1201.git . || {
        echo "❌ Git clone 失败"
        exit 1
    }
else
    cd "$PROJECT_DIR"
    echo "拉取最新代码..."
    git pull origin main || {
        echo "⚠️  Git pull 失败，继续..."
    }
fi

# 部署配置
SITES=(
    "tgmini20251220:tgmini.usdt2026.cc:3001:tgmini-frontend"
    "hbwy20251220:hongbao.usdt2026.cc:3002:hongbao-frontend"
    "aizkw20251219:aizkw.usdt2026.cc:3003:aizkw-frontend"
)

for SITE_INFO in "${SITES[@]}"; do
    IFS=':' read -r DIR DOMAIN PORT PM2_NAME <<< "$SITE_INFO"
    SITE_DIR="$PROJECT_DIR/$DIR"
    
    echo ""
    echo "============================================================"
    echo "🚀 部署: $DIR"
    echo "域名: $DOMAIN"
    echo "端口: $PORT"
    echo "============================================================"
    
    # 检查目录
    if [ ! -d "$SITE_DIR" ]; then
        echo "❌ 目录不存在: $SITE_DIR"
        continue
    fi
    
    cd "$SITE_DIR"
    
    # 检查 package.json
    if [ ! -f "package.json" ]; then
        echo "❌ package.json 不存在"
        continue
    fi
    
    # 安装依赖
    echo "安装依赖..."
    npm install || {
        echo "❌ npm install 失败"
        continue
    }
    
    # 构建
    echo "构建项目..."
    export NODE_OPTIONS="--max-old-space-size=3072"
    npm run build || {
        echo "❌ npm run build 失败"
        continue
    }
    
    # 检查 dist 目录
    if [ ! -d "dist" ]; then
        echo "❌ dist 目录不存在"
        continue
    fi
    
    # 停止旧进程
    echo "停止旧进程..."
    pm2 delete "$PM2_NAME" 2>/dev/null || true
    
    # 停止占用端口的进程
    if sudo lsof -i :$PORT >/dev/null 2>&1; then
        echo "停止占用端口 $PORT 的进程..."
        sudo lsof -ti :$PORT | xargs sudo kill -9 2>/dev/null || true
        sleep 2
    fi
    
    # 启动服务
    echo "启动服务..."
    pm2 start serve \
        --name "$PM2_NAME" \
        -- "$SITE_DIR/dist" \
        --listen $PORT \
        --single \
        --no-clipboard \
        --no-open || {
        echo "❌ PM2 启动失败"
        continue
    }
    
    pm2 save || true
    
    # 等待启动
    sleep 3
    
    # 检查服务
    if sudo lsof -i :$PORT >/dev/null 2>&1; then
        echo "✅ 服务已启动 (端口 $PORT)"
    else
        echo "❌ 服务启动失败"
        pm2 logs "$PM2_NAME" --lines 10 --nostream 2>/dev/null || true
    fi
done

# 保存 PM2 配置
pm2 save || true

echo ""
echo "============================================================"
echo "✅ 修复完成"
echo "============================================================"
echo ""
echo "PM2 进程列表:"
pm2 list
