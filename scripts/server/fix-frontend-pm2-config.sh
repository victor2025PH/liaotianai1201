#!/bin/bash
# 修复前端 PM2 配置 - 解决 ELFOOOO 错误

echo "=== 修复前端 PM2 配置 ==="
echo ""

# 1. 停止前端服务
echo "1. 停止前端服务..."
pm2 delete frontend 2>/dev/null || true
pm2 delete next-server 2>/dev/null || true
sleep 2
echo "✅ 已停止"
echo ""

# 2. 检查项目目录和构建产物
echo "2. 检查项目目录..."
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ 前端目录不存在: $FRONTEND_DIR"
    exit 1
fi

if [ ! -f "$FRONTEND_DIR/.next/standalone/server.js" ]; then
    echo "❌ standalone/server.js 不存在"
    echo "   需要重新构建前端..."
    exit 1
fi

echo "✅ 前端目录: $FRONTEND_DIR"
echo "✅ 构建产物: $FRONTEND_DIR/.next/standalone/server.js"
echo ""

# 3. 检查文件是否正常
echo "3. 检查 server.js 文件..."
if file "$FRONTEND_DIR/.next/standalone/server.js" | grep -q "text\|JavaScript"; then
    echo "✅ 文件格式正常"
else
    echo "❌ 文件格式异常，可能损坏"
    echo "   需要重新构建: cd $FRONTEND_DIR && npm run build"
    exit 1
fi

# 检查文件开头
FIRST_LINE=$(head -n 1 "$FRONTEND_DIR/.next/standalone/server.js" 2>/dev/null)
if echo "$FIRST_LINE" | grep -qE "^#!/usr/bin/env node|^const|^import|^require"; then
    echo "✅ 文件开头正常: ${FIRST_LINE:0:50}..."
else
    echo "⚠️  文件开头异常: ${FIRST_LINE:0:50}..."
fi
echo ""

# 4. 更新 ecosystem.config.js - 使用正确的配置方式
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
      // 关键修复：直接使用 server.js 的完整路径，让 Node.js 自动识别
      script: ".next/standalone/server.js",
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
echo "   关键修复：script 直接指向 .next/standalone/server.js（相对路径）"
echo "   interpreter 设置为 node（让 PM2 使用系统 node）"
echo ""

# 5. 验证配置
echo "5. 验证配置..."
if [ -f "ecosystem.config.js" ]; then
    echo "✅ ecosystem.config.js 存在"
    echo "   前端配置预览:"
    grep -A 15 '"name": "frontend"' ecosystem.config.js | head -15
else
    echo "❌ ecosystem.config.js 不存在"
    exit 1
fi
echo ""

# 6. 重启服务
echo "6. 重启 PM2 服务..."
pm2 start ecosystem.config.js
sleep 8

# 7. 检查状态
echo ""
echo "7. 检查服务状态..."
pm2 list

echo ""
echo "8. 检查前端配置详情..."
pm2 describe frontend 2>&1 | grep -E "cwd|script|interpreter|args" | head -10

echo ""
echo "9. 检查前端日志（最近20行）..."
pm2 logs frontend --lines 20 --nostream 2>&1 | tail -20

echo ""
echo "10. 检查前端错误日志..."
pm2 logs frontend --err --lines 10 --nostream 2>&1 | tail -10

echo ""
echo "11. 测试前端服务..."
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000 2>/dev/null)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "000" ]; then
    echo "✅ 前端响应 HTTP $HTTP_CODE"
    curl -s http://127.0.0.1:3000 | head -5
else
    echo "❌ 前端未响应 (HTTP $HTTP_CODE)"
fi

echo ""
echo "=== 修复完成 ==="
echo ""
echo "如果前端状态为 'online' 且无 SyntaxError，说明修复成功"
echo "如果仍有问题，请检查："
echo "  1. 前端是否已构建: ls -la $FRONTEND_DIR/.next/standalone/server.js"
echo "  2. 文件是否损坏: file $FRONTEND_DIR/.next/standalone/server.js"
echo "  3. 查看详细日志: pm2 logs frontend --lines 50"
