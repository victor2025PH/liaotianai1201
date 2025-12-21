#!/bin/bash
# 修复前端工作目录错误

echo "=== 修复前端工作目录错误 ==="
echo ""

# 1. 停止错误的 frontend 进程
echo "1. 停止错误的 frontend 进程..."
pm2 delete frontend 2>/dev/null || true
pm2 delete next-server 2>/dev/null || true
sleep 2
echo "✅ 已停止"
echo ""

# 2. 检查正确的项目目录
echo "2. 检查项目目录..."
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 项目目录不存在: $PROJECT_DIR"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ 前端目录不存在: $FRONTEND_DIR"
    exit 1
fi

echo "✅ 项目目录: $PROJECT_DIR"
echo "✅ 前端目录: $FRONTEND_DIR"
echo ""

# 3. 检查构建产物
echo "3. 检查前端构建产物..."
if [ ! -f "$FRONTEND_DIR/.next/standalone/server.js" ]; then
    echo "❌ standalone/server.js 不存在"
    echo "   需要重新构建前端..."
    echo "   执行: cd $FRONTEND_DIR && npm run build"
    exit 1
fi

echo "✅ 构建产物存在: $FRONTEND_DIR/.next/standalone/server.js"
ls -lh "$FRONTEND_DIR/.next/standalone/server.js" | head -1
echo ""

# 4. 更新 ecosystem.config.js
echo "4. 更新 ecosystem.config.js..."
cd "$PROJECT_DIR" || exit 1

cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: "backend",
      cwd: "/home/ubuntu/telegram-ai-system/admin-backend",
      script: "/home/ubuntu/telegram-ai-system/admin-backend/venv/bin/uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
      env: {
        PORT: 8000,
        PYTHONPATH: "/home/ubuntu/telegram-ai-system/admin-backend",
        PYTHONUNBUFFERED: "1",
        NODE_ENV: "production"
      },
      error_file: "/home/ubuntu/telegram-ai-system/logs/backend-error.log",
      out_file: "/home/ubuntu/telegram-ai-system/logs/backend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      autorestart: true,
      watch: false,
      max_memory_restart: "800M",
      instances: 1,
      exec_mode: "fork"
    },
    {
      name: "frontend",
      cwd: "/home/ubuntu/telegram-ai-system/saas-demo",
      script: "/usr/bin/node",
      args: ".next/standalone/server.js",
      interpreter: "node",
      env: {
        PORT: 3000,
        NODE_ENV: "production",
        NODE_OPTIONS: "--max-old-space-size=3072",
        HOSTNAME: "0.0.0.0"
      },
      error_file: "/home/ubuntu/telegram-ai-system/logs/frontend-error.log",
      out_file: "/home/ubuntu/telegram-ai-system/logs/frontend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      autorestart: true,
      watch: false,
      max_memory_restart: "2G",
      instances: 1,
      exec_mode: "fork"
    }
  ]
};
EOF

echo "✅ ecosystem.config.js 已更新"
echo "   前端工作目录: /home/ubuntu/telegram-ai-system/saas-demo"
echo ""

# 5. 重启服务
echo "5. 重启 PM2 服务..."
pm2 start ecosystem.config.js
sleep 5

# 6. 检查状态
echo ""
echo "6. 检查服务状态..."
pm2 list

echo ""
echo "7. 检查前端日志（最近20行）..."
pm2 logs frontend --lines 20 --nostream 2>&1 | tail -20

echo ""
echo "8. 测试前端服务..."
sleep 3
curl -s http://127.0.0.1:3000 | head -10 || echo "❌ 前端未响应"

echo ""
echo "=== 修复完成 ==="
echo ""
echo "如果前端状态为 'online'，说明修复成功"
echo "如果仍有问题，请检查："
echo "  1. 前端是否已构建: ls -la $FRONTEND_DIR/.next/standalone/server.js"
echo "  2. 端口 3000 是否被占用: lsof -ti :3000"
echo "  3. 查看详细日志: pm2 logs frontend --lines 50"
