#!/bin/bash
# 验证管理后台前端部署状态

set -e

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_ROOT/admin-frontend"

echo "🔍 验证管理后台前端部署状态..."
echo ""

# 1. 检查 PM2 进程
echo "📊 PM2 进程状态:"
pm2 list | grep admin-frontend || echo "⚠️  admin-frontend 进程不存在"
echo ""

# 2. 检查端口
echo "🔌 检查端口 3001:"
if lsof -i :3001 > /dev/null 2>&1; then
    echo "✅ 端口 3001 已被占用"
    lsof -i :3001 | head -3
else
    echo "❌ 端口 3001 未被占用"
fi
echo ""

# 3. 检查构建产物
echo "📦 检查构建产物:"
cd "$FRONTEND_DIR" || exit 1

if [ -d ".next" ]; then
    echo "✅ .next 目录存在"
    echo "   大小: $(du -sh .next | cut -f1)"
    echo "   文件数: $(find .next -type f | wc -l)"
else
    echo "❌ .next 目录不存在"
fi
echo ""

# 4. 测试 HTTP 连接
echo "🌐 测试 HTTP 连接:"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3001 || echo "000")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "404" ]; then
    echo "✅ HTTP 连接成功 (状态码: $HTTP_STATUS)"
    echo "   响应内容预览:"
    curl -s http://127.0.0.1:3001 | head -20
else
    echo "❌ HTTP 连接失败 (状态码: $HTTP_STATUS)"
fi
echo ""

# 5. 检查日志
echo "📋 检查 PM2 日志:"
if pm2 list | grep -q admin-frontend; then
    echo "最近 10 行日志:"
    pm2 logs admin-frontend --lines 10 --nostream 2>/dev/null || echo "无法读取日志"
else
    echo "⚠️  进程不存在，无法查看日志"
fi
echo ""

# 6. 检查环境变量
echo "🔧 检查环境变量:"
if [ -f ".env.local" ]; then
    echo "✅ .env.local 存在"
    grep -E "API_BASE_URL|NEXT_PUBLIC" .env.local 2>/dev/null | head -5 || echo "未找到相关配置"
else
    echo "⚠️  .env.local 不存在（使用默认配置）"
fi
echo ""

# 7. 总结
echo "📊 部署状态总结:"
if pm2 list | grep -q "admin-frontend.*online"; then
    echo "✅ 管理后台前端正在运行"
else
    echo "❌ 管理后台前端未运行"
fi

if [ -d ".next" ]; then
    echo "✅ 构建产物存在"
else
    echo "❌ 构建产物不存在"
fi

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "404" ]; then
    echo "✅ HTTP 服务可访问"
else
    echo "❌ HTTP 服务不可访问"
fi

echo ""
echo "💡 如果发现问题，可以执行:"
echo "   bash scripts/deploy_admin_frontend.sh"

