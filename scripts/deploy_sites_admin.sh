#!/bin/bash
# 部署三个展示网站管理后台前端

set -e

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_ROOT/sites-admin-frontend"

echo "🚀 开始部署三个展示网站管理后台前端..."

# 1. 进入前端目录
cd "$FRONTEND_DIR" || {
    echo "❌ 无法进入前端目录: $FRONTEND_DIR"
    exit 1
}

# 2. 检查 Node.js 版本
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi

NODE_VERSION=$(node -v)
echo "✅ Node.js 版本: $NODE_VERSION"

# 3. 安装依赖
echo "📦 安装依赖..."
if [ ! -d "node_modules" ]; then
    npm install
else
    npm install --production=false
fi

# 4. 构建项目
echo "🔨 构建项目..."
npm run build

if [ ! -d ".next" ]; then
    echo "❌ 构建失败：.next 目录不存在"
    exit 1
fi

echo "✅ 构建完成"

# 5. 修正文件权限
echo "🔒 修正文件权限..."
CURRENT_USER=$(logname 2>/dev/null || whoami)
sudo chown -R $CURRENT_USER:$CURRENT_USER .next public package.json node_modules 2>/dev/null || {
    chown -R $CURRENT_USER:$CURRENT_USER .next public package.json node_modules 2>/dev/null || true
}

# 6. 停止旧进程（如果存在）
echo "🛑 停止旧进程..."
pm2 delete sites-admin-frontend 2>/dev/null || true
sleep 2

# 7. 启动服务（监听所有接口，允许外部访问）
echo "🚀 启动服务..."
export HOSTNAME=0.0.0.0
export PORT=3007
export HOST=0.0.0.0
pm2 start npm --name "sites-admin-frontend" \
    --cwd "$FRONTEND_DIR" \
    --update-env \
    --max-memory-restart 1G \
    --error "$PROJECT_ROOT/logs/sites-admin-frontend-error.log" \
    --output "$PROJECT_ROOT/logs/sites-admin-frontend-out.log" \
    --merge-logs \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
    -- start || {
    echo "❌ PM2 启动失败"
    tail -20 "$PROJECT_ROOT/logs/sites-admin-frontend-error.log" 2>/dev/null || echo "无法读取错误日志"
    exit 1
}

# 8. 保存 PM2 配置
pm2 save

# 9. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 10. 健康检查
echo "⏳ 等待服务完全启动..."
sleep 3

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3007 || echo "000")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "404" ]; then
    echo "✅ 三个展示网站管理后台前端启动成功 (Port 3007, HTTP $HTTP_STATUS)!"
    echo "   访问地址: http://127.0.0.1:3007"
else
    echo "⚠️  三个展示网站管理后台前端可能未完全启动 (HTTP $HTTP_STATUS)"
    echo "检查 PM2 状态:"
    pm2 list | grep sites-admin-frontend || echo "进程不存在"
    echo "检查错误日志:"
    tail -30 "$PROJECT_ROOT/logs/sites-admin-frontend-error.log" 2>/dev/null || echo "无法读取错误日志"
    echo "检查输出日志:"
    tail -30 "$PROJECT_ROOT/logs/sites-admin-frontend-out.log" 2>/dev/null || echo "无法读取输出日志"
    echo ""
    echo "💡 如果进程存在但无法访问，请等待几秒后重试:"
    echo "   curl http://127.0.0.1:3007"
fi

echo "🎉 三个展示网站管理后台前端部署完成！"

