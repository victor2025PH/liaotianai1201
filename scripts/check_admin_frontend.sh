#!/bin/bash
# 检查管理后台前端状态

set -e

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_ROOT/admin-frontend"

echo "🔍 检查管理后台前端状态..."

# 1. 检查目录是否存在
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ 管理后台目录不存在: $FRONTEND_DIR"
    exit 1
fi

# 2. 检查 PM2 进程
echo "📊 PM2 进程状态:"
pm2 list | grep admin-frontend || echo "⚠️  admin-frontend 进程不存在"

# 3. 检查端口
echo "🔌 检查端口 3001:"
if lsof -i :3001 > /dev/null 2>&1; then
    echo "✅ 端口 3001 已被占用"
    lsof -i :3001
else
    echo "❌ 端口 3001 未被占用"
fi

# 4. 检查构建产物
cd "$FRONTEND_DIR" || exit 1

if [ -d ".next" ]; then
    echo "✅ .next 目录存在"
    ls -la .next | head -5
else
    echo "❌ .next 目录不存在，需要构建"
fi

# 5. 检查 package.json
if [ -f "package.json" ]; then
    echo "✅ package.json 存在"
else
    echo "❌ package.json 不存在"
fi

# 6. 测试 HTTP 连接
echo "🌐 测试 HTTP 连接:"
if curl -s http://127.0.0.1:3001 > /dev/null; then
    echo "✅ HTTP 连接成功"
    curl -s http://127.0.0.1:3001 | head -20
else
    echo "❌ HTTP 连接失败"
fi

echo "📋 建议操作:"
echo "  1. 如果进程不存在: bash scripts/deploy_admin_frontend.sh"
echo "  2. 如果构建失败: cd admin-frontend && npm install && npm run build"
echo "  3. 如果端口被占用但不是 admin-frontend: 检查其他进程"

