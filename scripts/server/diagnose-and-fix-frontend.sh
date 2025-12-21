#!/bin/bash
# 诊断并修复前端服务问题

echo "=== 前端服务问题诊断和修复 ==="
echo ""

# 1. 检查 PM2 配置
echo "1. 检查 PM2 frontend 配置..."
pm2 describe frontend 2>&1 | head -30
echo ""

# 2. 检查工作目录和文件
echo "2. 检查前端文件..."
FRONTEND_DIR="/home/ubuntu/aizkw20251219"
if [ -d "$FRONTEND_DIR" ]; then
    echo "✅ 找到前端目录: $FRONTEND_DIR"
    echo "   检查 standalone server..."
    if [ -f "$FRONTEND_DIR/.next/standalone/server.js" ]; then
        echo "   ✅ standalone/server.js 存在"
        ls -lh "$FRONTEND_DIR/.next/standalone/server.js" | head -1
        
        # 检查文件是否有无效字符
        echo "   检查文件开头（前20个字符）..."
        head -c 20 "$FRONTEND_DIR/.next/standalone/server.js" | od -c | head -3
    else
        echo "   ❌ standalone/server.js 不存在"
        echo "   需要重新构建前端"
    fi
else
    echo "❌ 前端目录不存在: $FRONTEND_DIR"
    echo "   检查其他可能的位置..."
    for dir in "/home/ubuntu/telegram-ai-system/saas-demo" "/home/ubuntu/saas-demo"; do
        if [ -d "$dir" ]; then
            echo "   找到: $dir"
            FRONTEND_DIR="$dir"
            break
        fi
    done
fi
echo ""

# 3. 检查错误日志
echo "3. 检查前端错误日志..."
if [ -f "/home/ubuntu/aizkw20251219/logs/frontend-error.log" ]; then
    echo "   最近10行错误日志:"
    tail -10 "/home/ubuntu/aizkw20251219/logs/frontend-error.log" 2>/dev/null | head -10
fi
echo ""

# 4. 检查 PM2 ecosystem 配置
echo "4. 检查 ecosystem.config.js..."
if [ -f "/home/ubuntu/telegram-ai-system/ecosystem.config.js" ]; then
    echo "   找到 ecosystem.config.js"
    grep -A 10 '"name": "frontend"' /home/ubuntu/telegram-ai-system/ecosystem.config.js 2>/dev/null || echo "   未找到 frontend 配置"
else
    echo "   ❌ ecosystem.config.js 不存在"
fi
echo ""

# 5. 修复方案
echo "5. 开始修复..."
echo ""

# 停止错误的 frontend 进程
echo "   停止错误的 frontend 进程..."
pm2 delete frontend 2>/dev/null || true
sleep 2

# 检查正确的项目目录
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 项目目录不存在: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR" || exit 1

# 检查正确的 frontend 目录
SAAS_DEMO_DIR="$PROJECT_DIR/saas-demo"
if [ ! -d "$SAAS_DEMO_DIR" ]; then
    echo "❌ saas-demo 目录不存在: $SAAS_DEMO_DIR"
    echo "   检查是否有其他前端目录..."
    exit 1
fi

# 检查构建产物
if [ ! -f "$SAAS_DEMO_DIR/.next/standalone/server.js" ]; then
    echo "❌ standalone/server.js 不存在"
    echo "   需要重新构建前端..."
    echo "   执行: cd $SAAS_DEMO_DIR && npm run build"
    exit 1
fi

# 检查文件是否有问题
echo "   检查 standalone/server.js 文件..."
if file "$SAAS_DEMO_DIR/.next/standalone/server.js" | grep -q "text"; then
    echo "   ✅ 文件格式正常"
else
    echo "   ⚠️  文件格式可能有问题"
fi

# 检查文件开头
FIRST_CHARS=$(head -c 50 "$SAAS_DEMO_DIR/.next/standalone/server.js" 2>/dev/null)
if echo "$FIRST_CHARS" | grep -q "^#!/usr/bin/env node\|^const\|^import\|^require"; then
    echo "   ✅ 文件开头正常"
else
    echo "   ❌ 文件开头异常: $FIRST_CHARS"
    echo "   文件可能损坏，需要重新构建"
    exit 1
fi

# 更新或创建 ecosystem.config.js
echo ""
echo "   更新 ecosystem.config.js..."
cat > "$PROJECT_DIR/ecosystem.config.js" << 'EOF'
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
      max_memory_restart: "1G",
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

echo "   ✅ ecosystem.config.js 已更新"
echo ""

# 重启 frontend
echo "   重启 frontend 服务..."
pm2 delete frontend 2>/dev/null || true
sleep 2
pm2 start ecosystem.config.js --only frontend
sleep 5

# 检查状态
echo ""
echo "6. 检查修复结果..."
pm2 list | grep -E "frontend|backend"

echo ""
echo "7. 检查前端错误日志（最近10行）..."
pm2 logs frontend --err --lines 10 --nostream 2>&1 | tail -10

echo ""
echo "8. 测试前端服务..."
sleep 3
curl -s http://127.0.0.1:3000 | head -20 || echo "❌ 前端未响应"

echo ""
echo "=== 诊断和修复完成 ==="
echo ""
echo "如果前端仍然 errored，请检查："
echo "1. 前端是否已构建: ls -la $SAAS_DEMO_DIR/.next/standalone/server.js"
echo "2. 端口 3000 是否被占用: lsof -ti :3000"
echo "3. 查看详细日志: pm2 logs frontend --lines 50"
