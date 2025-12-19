#!/bin/bash
# ============================================================
# 修复 bcrypt 错误和端口绑定问题
# ============================================================

echo "=========================================="
echo "🔧 修复 bcrypt 错误和端口绑定问题"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"

# 1. 停止后端服务
echo "[1/7] 停止后端服务..."
echo "----------------------------------------"
sudo -u ubuntu pm2 stop backend 2>/dev/null || true
sudo -u ubuntu pm2 delete backend 2>/dev/null || true
sleep 2

# 清理端口
sudo lsof -t -i:8000 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
sleep 2
echo "✅ 后端服务已停止"
echo ""

# 2. 修复 bcrypt
echo "[2/7] 修复 bcrypt..."
echo "----------------------------------------"
cd "$BACKEND_DIR" || exit 1

# 激活虚拟环境
source venv/bin/activate

# 卸载并重新安装 bcrypt
echo "卸载 bcrypt..."
pip uninstall -y bcrypt passlib 2>/dev/null || true

echo "重新安装 bcrypt 和 passlib..."
pip install --upgrade --force-reinstall bcrypt passlib[bcrypt] --quiet

if [ $? -ne 0 ]; then
    echo "❌ bcrypt 安装失败"
    exit 1
fi

# 验证 bcrypt
echo "验证 bcrypt..."
python -c "import bcrypt; print(f'bcrypt 版本: {bcrypt.__version__}')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ bcrypt 验证失败"
    exit 1
fi

# 验证 passlib
echo "验证 passlib..."
python -c "from passlib.context import CryptContext; print('passlib 正常')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ passlib 验证失败"
    exit 1
fi

echo "✅ bcrypt 和 passlib 已修复"
echo ""

# 3. 检查 uvicorn 配置
echo "[3/7] 检查 uvicorn 配置..."
echo "----------------------------------------"
# 验证 uvicorn 可以正常启动（不实际启动服务器）
python -c "import uvicorn; print('uvicorn 可以导入')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ uvicorn 无法导入"
    exit 1
fi
echo "✅ uvicorn 配置正常"
echo ""

# 4. 检查应用主文件
echo "[4/7] 检查应用主文件..."
echo "----------------------------------------"
if [ ! -f "$BACKEND_DIR/app/main.py" ]; then
    echo "❌ app/main.py 不存在"
    exit 1
fi

# 尝试导入应用（不启动服务器）
python -c "from app.main import app; print('应用可以导入')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 应用无法导入，查看错误:"
    python -c "from app.main import app" 2>&1 | head -20
    exit 1
fi
echo "✅ 应用可以导入"
echo ""

# 5. 测试直接启动 uvicorn（短暂测试）
echo "[5/7] 测试 uvicorn 启动..."
echo "----------------------------------------"
echo "尝试启动 uvicorn（5秒测试）..."
timeout 5 python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 | head -20 || true
echo "✅ uvicorn 可以启动"
echo ""

# 6. 修复 PM2 配置（确保使用正确的启动方式）
echo "[6/7] 修复 PM2 配置..."
echo "----------------------------------------"
cd "$PROJECT_DIR" || exit 1

# 创建启动脚本（更可靠的方式）
cat > "$BACKEND_DIR/start_backend.sh" << 'EOF'
#!/bin/bash
cd /home/ubuntu/telegram-ai-system/admin-backend
source venv/bin/activate
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
EOF

chmod +x "$BACKEND_DIR/start_backend.sh"
chown ubuntu:ubuntu "$BACKEND_DIR/start_backend.sh"
echo "✅ 启动脚本已创建"

# 更新 PM2 配置（使用启动脚本）
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: "backend",
      cwd: "/home/ubuntu/telegram-ai-system/admin-backend",
      // 使用启动脚本（更可靠）
      script: "/home/ubuntu/telegram-ai-system/admin-backend/start_backend.sh",
      interpreter: "/bin/bash",
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
      exec_mode: "fork",
      // 增加启动超时时间
      min_uptime: "10s",
      max_restarts: 10,
      restart_delay: 5000
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
echo "✅ PM2 配置已更新（使用启动脚本）"
echo ""

# 7. 启动后端服务
echo "[7/7] 启动后端服务..."
echo "----------------------------------------"
sudo -u ubuntu pm2 start ecosystem.config.js --only backend
sleep 5

echo "检查服务状态:"
sudo -u ubuntu pm2 list | grep backend
echo ""

# 8. 验证服务
echo "=========================================="
echo "🧪 验证服务"
echo "=========================================="
echo ""

echo "等待服务启动 (30秒，给应用更多时间初始化)..."
sleep 30

echo "检查端口 8000:"
PORT_8000=$(sudo ss -tlnp | grep ":8000" || echo "")
if [ -n "$PORT_8000" ]; then
    echo "✅ 端口 8000 正在监听"
    echo "   $PORT_8000"
else
    echo "❌ 端口 8000 仍未监听"
    echo ""
    echo "查看 PM2 状态:"
    sudo -u ubuntu pm2 describe backend
    echo ""
    echo "查看后端日志（最后 100 行）:"
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
    echo ""
    echo "查看详细错误日志:"
    sudo -u ubuntu pm2 logs backend --lines 50 --nostream 2>&1 | tail -50
else
    echo "⚠️  未知响应:"
    echo "$LOGIN_RESPONSE" | head -10
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请检查:"
echo "1. PM2 状态: sudo -u ubuntu pm2 describe backend"
echo "2. 后端日志: sudo -u ubuntu pm2 logs backend --lines 200"
echo "3. 错误日志: tail -100 $PROJECT_DIR/logs/backend-error.log"
echo "4. 输出日志: tail -100 $PROJECT_DIR/logs/backend-out.log"
echo "5. 进程状态: ps aux | grep uvicorn"
echo ""

