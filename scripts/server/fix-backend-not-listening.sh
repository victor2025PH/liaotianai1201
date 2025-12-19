#!/bin/bash
# ============================================================
# 修复后端服务未监听端口 8000 的问题
# ============================================================

echo "=========================================="
echo "🔧 修复后端服务未监听端口 8000"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"

# 1. 停止后端服务
echo "[1/6] 停止后端服务..."
echo "----------------------------------------"
sudo -u ubuntu pm2 stop backend 2>/dev/null || true
sudo -u ubuntu pm2 delete backend 2>/dev/null || true
sleep 2

# 清理端口
sudo lsof -t -i:8000 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
sleep 2
echo "✅ 后端服务已停止"
echo ""

# 2. 检查 uvicorn 可执行文件
echo "[2/6] 检查 uvicorn..."
echo "----------------------------------------"
UVICORN_PATH="$BACKEND_DIR/venv/bin/uvicorn"
if [ ! -f "$UVICORN_PATH" ]; then
    echo "❌ uvicorn 可执行文件不存在: $UVICORN_PATH"
    exit 1
fi
echo "✅ uvicorn 可执行文件存在"

# 检查 uvicorn 脚本的第一行（shebang）
SHEBANG=$(head -1 "$UVICORN_PATH" 2>/dev/null || echo "")
echo "uvicorn shebang: $SHEBANG"

# 检查 Python 解释器
PYTHON_PATH="$BACKEND_DIR/venv/bin/python3"
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Python 解释器不存在: $PYTHON_PATH"
    exit 1
fi
echo "✅ Python 解释器存在: $PYTHON_PATH"
$PYTHON_PATH --version
echo ""

# 3. 手动测试 uvicorn 启动
echo "[3/6] 手动测试 uvicorn 启动..."
echo "----------------------------------------"
cd "$BACKEND_DIR" || exit 1

# 激活虚拟环境
source venv/bin/activate

# 测试 uvicorn 是否可以导入
if ! python -c "import uvicorn" 2>/dev/null; then
    echo "❌ uvicorn 模块无法导入"
    exit 1
fi
echo "✅ uvicorn 模块可以导入"

# 测试 uvicorn 命令
if ! uvicorn --version >/dev/null 2>&1; then
    echo "❌ uvicorn 命令无法执行"
    exit 1
fi
echo "✅ uvicorn 命令可以执行"
uvicorn --version
echo ""

# 4. 修复 PM2 配置
echo "[4/6] 修复 PM2 配置..."
echo "----------------------------------------"
cd "$PROJECT_DIR" || exit 1

# 备份现有配置
if [ -f "ecosystem.config.js" ]; then
    cp ecosystem.config.js ecosystem.config.js.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ 已备份现有配置"
fi

# 创建修复后的配置（使用 Python 解释器）
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: "backend",
      cwd: "/home/ubuntu/telegram-ai-system/admin-backend",
      // 使用 Python 解释器执行 uvicorn 模块
      script: "/home/ubuntu/telegram-ai-system/admin-backend/venv/bin/python3",
      args: "-m uvicorn app.main:app --host 0.0.0.0 --port 8000",
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
      // Next.js 16 standalone 模式
      script: "/usr/bin/node",
      args: ".next/standalone/server.js",
      env: {
        PORT: 3000,
        NODE_ENV: "production",
        NODE_OPTIONS: "--max-old-space-size=1024"
      },
      error_file: "/home/ubuntu/telegram-ai-system/logs/frontend-error.log",
      out_file: "/home/ubuntu/telegram-ai-system/logs/frontend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      instances: 1,
      exec_mode: "fork"
    }
  ]
};
EOF

chown ubuntu:ubuntu ecosystem.config.js
chmod 644 ecosystem.config.js
echo "✅ PM2 配置已更新（使用 Python 解释器）"
echo ""

# 5. 启动后端服务
echo "[5/6] 启动后端服务..."
echo "----------------------------------------"
sudo -u ubuntu pm2 start ecosystem.config.js --only backend
sleep 5

echo "检查服务状态:"
sudo -u ubuntu pm2 list | grep backend
echo ""

# 6. 验证服务
echo "[6/6] 验证服务..."
echo "----------------------------------------"

echo "等待服务启动 (20秒)..."
sleep 20

echo "检查端口 8000:"
PORT_8000=$(sudo ss -tlnp | grep ":8000" || echo "")
if [ -n "$PORT_8000" ]; then
    echo "✅ 端口 8000 正在监听"
    echo "   $PORT_8000"
else
    echo "❌ 端口 8000 仍未监听"
    echo ""
    echo "查看后端日志:"
    sudo -u ubuntu pm2 logs backend --lines 100 --nostream 2>&1 | tail -100
    echo ""
    echo "查看后端错误日志:"
    if [ -f "$PROJECT_DIR/logs/backend-error.log" ]; then
        tail -50 "$PROJECT_DIR/logs/backend-error.log" 2>/dev/null || true
    fi
    echo ""
    echo "查看后端输出日志:"
    if [ -f "$PROJECT_DIR/logs/backend-out.log" ]; then
        tail -50 "$PROJECT_DIR/logs/backend-out.log" 2>/dev/null || true
    fi
    exit 1
fi
echo ""

echo "测试 /health:"
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "✅ 后端健康检查成功 (HTTP $HEALTH_RESPONSE)"
    curl -s http://127.0.0.1:8000/health | head -3
else
    echo "❌ 后端健康检查失败: HTTP $HEALTH_RESPONSE"
    echo "查看后端日志:"
    sudo -u ubuntu pm2 logs backend --lines 30 --nostream 2>&1 | tail -30
fi
echo ""

echo "测试 /api/v1/auth/login:"
LOGIN_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@example.com","password":"changeme123"}' 2>&1)

if echo "$LOGIN_RESPONSE" | grep -q "access_token\|token"; then
    echo "✅ 登录 API 正常"
    echo "$LOGIN_RESPONSE" | head -3
elif echo "$LOGIN_RESPONSE" | grep -q "401\|Unauthorized"; then
    echo "⚠️  登录 API 返回 401（用户名或密码错误，但 API 正常）"
elif echo "$LOGIN_RESPONSE" | grep -q "500\|Internal Server Error"; then
    echo "❌ 登录 API 仍然返回 500 错误"
    echo "$LOGIN_RESPONSE" | head -10
else
    echo "⚠️  未知响应:"
    echo "$LOGIN_RESPONSE" | head -10
fi
echo ""

echo "=========================================="
echo "✅ 后端服务修复完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请检查:"
echo "1. 后端日志: sudo -u ubuntu pm2 logs backend --lines 100"
echo "2. 错误日志: tail -100 $PROJECT_DIR/logs/backend-error.log"
echo "3. 输出日志: tail -100 $PROJECT_DIR/logs/backend-out.log"
echo "4. PM2 状态: sudo -u ubuntu pm2 list"
echo ""

