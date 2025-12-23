#!/bin/bash
# 检查 AI 监控系统前端状态

set -e

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_ROOT/ai-monitor-frontend"

echo "🔍 检查 AI 监控系统前端状态..."

# 1. 检查目录
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ 前端目录不存在: $FRONTEND_DIR"
    exit 1
fi

# 2. 检查 PM2 进程
echo "📊 PM2 进程状态:"
pm2 list | grep ai-monitor-frontend || echo "⚠️  ai-monitor-frontend 进程不存在"

# 3. 检查端口
echo "🔌 检查端口 3006:"
if lsof -i :3006 2>/dev/null | grep -q LISTEN; then
    echo "✅ 端口 3006 正在监听"
else
    echo "❌ 端口 3006 未监听"
fi

# 4. HTTP 测试
echo "🌐 HTTP 测试:"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3006 || echo "000")
echo "HTTP 状态码: $HTTP_STATUS"

echo ""
echo "📋 建议操作:"
echo "  1. 如果进程不存在: bash scripts/deploy_ai_monitor.sh"
echo "  2. 如果构建失败: cd ai-monitor-frontend && npm install && npm run build"
echo "  3. 如果端口被占用但不是 ai-monitor-frontend: 检查其他进程"

