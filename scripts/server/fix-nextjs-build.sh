#!/bin/bash
# ============================================================
# 修复 Next.js 构建问题
# ============================================================

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

echo "=========================================="
echo "🔧 修复 Next.js 构建问题"
echo "=========================================="
echo ""

cd "$FRONTEND_DIR" || exit 1

# 1. 检查 .next 目录
echo "[1/5] 检查 .next 目录..."
echo "----------------------------------------"
if [ -d ".next" ]; then
    echo "✅ .next 目录存在"
    echo "检查关键文件..."
    
    # 检查 BUILD_ID
    if [ -f ".next/BUILD_ID" ]; then
        BUILD_ID=$(cat .next/BUILD_ID)
        echo "✅ BUILD_ID 存在: $BUILD_ID"
    else
        echo "❌ BUILD_ID 不存在"
    fi
    
    # 检查 server 目录
    if [ -d ".next/standalone" ] || [ -d ".next/server" ]; then
        echo "✅ server 目录存在"
    else
        echo "❌ server 目录不存在"
    fi
    
    # 检查 static 目录
    if [ -d ".next/static" ]; then
        echo "✅ static 目录存在"
    else
        echo "❌ static 目录不存在"
    fi
else
    echo "❌ .next 目录不存在"
fi
echo ""

# 2. 停止现有服务
echo "[2/5] 停止现有服务..."
echo "----------------------------------------"
if command -v pm2 &> /dev/null; then
    pm2 stop next-server 2>/dev/null || true
    pm2 delete next-server 2>/dev/null || true
    echo "✅ 已停止现有服务"
fi
echo ""

# 3. 清理旧的构建文件
echo "[3/5] 清理旧的构建文件..."
echo "----------------------------------------"
if [ -d ".next" ]; then
    echo "备份旧的 .next 目录..."
    if [ -d ".next.backup" ]; then
        rm -rf .next.backup
    fi
    mv .next .next.backup
    echo "✅ 已备份旧的构建文件"
fi
echo ""

# 4. 重新构建
echo "[4/5] 重新构建 Next.js 应用..."
echo "----------------------------------------"
echo "这可能需要几分钟，请耐心等待..."
echo ""

# 检查是否有 package.json
if [ ! -f "package.json" ]; then
    echo "❌ package.json 不存在"
    exit 1
fi

# 安装依赖（如果需要）
if [ ! -d "node_modules" ]; then
    echo "安装依赖..."
    npm install
fi

# 构建应用
echo "开始构建..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ 构建失败"
    echo "查看构建错误："
    npm run build 2>&1 | tail -30
    exit 1
fi

# 验证构建文件
echo ""
echo "验证构建文件..."
if [ -f ".next/BUILD_ID" ]; then
    BUILD_ID=$(cat .next/BUILD_ID)
    echo "✅ BUILD_ID: $BUILD_ID"
else
    echo "❌ BUILD_ID 仍然不存在"
    exit 1
fi

if [ -d ".next/server" ] || [ -d ".next/standalone" ]; then
    echo "✅ server 文件存在"
else
    echo "⚠️  server 文件可能不完整"
fi

if [ -d ".next/static" ]; then
    echo "✅ static 文件存在"
else
    echo "⚠️  static 文件可能不完整"
fi
echo ""

# 5. 启动服务
echo "[5/5] 启动服务..."
echo "----------------------------------------"
if command -v pm2 &> /dev/null; then
    echo "使用 PM2 启动..."
    pm2 start npm --name next-server -- start
    
    sleep 5
    
    # 检查状态
    pm2 list | grep next-server
    
    # 检查端口
    sleep 3
    if sudo ss -tlnp | grep -q ":3000 "; then
        echo ""
        echo "✅ 前端服务已启动，端口 3000 正在监听"
    else
        echo ""
        echo "⚠️  端口 3000 未监听，查看日志..."
        pm2 logs next-server --lines 20 --nostream 2>/dev/null | tail -20
    fi
else
    echo "⚠️  PM2 未安装"
fi
echo ""

# 6. 测试连接
echo "测试服务连接..."
echo "----------------------------------------"
sleep 3

if curl -s http://127.0.0.1:3000 > /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000)
    echo "✅ 前端服务可以响应 (HTTP $HTTP_CODE)"
else
    echo "❌ 前端服务无法响应"
    echo "查看详细日志: pm2 logs next-server"
fi
echo ""

# 7. 重新加载 Nginx
echo "重新加载 Nginx..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
    sudo systemctl reload nginx
    sleep 2
    
    # 测试 HTTPS
    if curl -s -k https://127.0.0.1 > /dev/null; then
        echo "✅ HTTPS 本地连接正常"
    else
        echo "⚠️  HTTPS 本地连接异常"
    fi
else
    echo "❌ Nginx 配置有错误"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在："
echo "  1. 查看 PM2 日志: pm2 logs next-server"
echo "  2. 检查构建文件: ls -la .next/"
echo "  3. 检查端口: sudo ss -tlnp | grep :3000"
echo ""

