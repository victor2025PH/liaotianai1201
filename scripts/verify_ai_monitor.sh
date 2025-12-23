#!/bin/bash
# 验证 AI 监控系统前端部署状态

set -e

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_ROOT/ai-monitor-frontend"

echo "🔍 验证 AI 监控系统前端部署状态..."

# 1. 检查 PM2 进程
echo "📊 PM2 进程状态:"
pm2 list | grep ai-monitor-frontend || echo "⚠️  ai-monitor-frontend 进程不存在"

# 2. 检查端口
echo "🔌 检查端口 3006:"
if lsof -i :3006 2>/dev/null | grep -q LISTEN; then
    echo "✅ 端口 3006 正在监听"
    lsof -i :3006 | grep LISTEN
else
    echo "❌ 端口 3006 未监听"
fi

# 3. 检查目录
echo "📁 检查目录:"
if [ -d "$FRONTEND_DIR" ]; then
    echo "✅ 前端目录存在: $FRONTEND_DIR"
    if [ -d "$FRONTEND_DIR/.next" ]; then
        echo "✅ .next 目录存在"
    else
        echo "❌ .next 目录不存在，需要构建"
    fi
else
    echo "❌ 前端目录不存在: $FRONTEND_DIR"
fi

# 4. HTTP 测试
echo "🌐 HTTP 测试:"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3006 || echo "000")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "404" ]; then
    echo "✅ HTTP 响应正常 (状态码: $HTTP_STATUS)"
else
    echo "❌ HTTP 响应异常 (状态码: $HTTP_STATUS)"
fi

# 5. 检查日志
echo "📋 检查 PM2 日志:"
if pm2 list | grep -q ai-monitor-frontend; then
    echo "最近 10 行日志:"
    pm2 logs ai-monitor-frontend --lines 10 --nostream 2>/dev/null || echo "无法读取日志"
else
    echo "⚠️  进程不存在，无法查看日志"
fi

echo ""
echo "=========================================="
if pm2 list | grep -q "ai-monitor-frontend.*online"; then
    echo "✅ AI 监控系统前端正在运行"
else
    echo "❌ AI 监控系统前端未运行"
fi
echo "=========================================="

echo ""
echo "💡 如果发现问题，可以执行:"
echo "   bash scripts/deploy_ai_monitor.sh"

