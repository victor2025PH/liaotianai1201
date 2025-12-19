#!/bin/bash
# ============================================================
# 修复后端依赖问题
# ============================================================

echo "=========================================="
echo "🔧 修复后端依赖问题"
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
echo "✅ 后端服务已停止"
echo ""

# 2. 检查虚拟环境
echo "[2/6] 检查虚拟环境..."
echo "----------------------------------------"
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    cd "$BACKEND_DIR" || exit 1
    python3 -m venv venv
    echo "✅ 虚拟环境已创建"
else
    echo "✅ 虚拟环境存在"
fi
echo ""

# 3. 重新安装依赖
echo "[3/6] 重新安装依赖..."
echo "----------------------------------------"
cd "$BACKEND_DIR" || exit 1
source venv/bin/activate

echo "升级 pip..."
pip install --upgrade pip --quiet

echo "检查关键依赖..."
MISSING_DEPS=0

# 检查 anyio
python -c "import anyio._backends" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ anyio._backends 缺失"
    MISSING_DEPS=1
else
    echo "✅ anyio 正常"
fi

# 检查 jwt
python -c "import jwt" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ jwt 缺失"
    MISSING_DEPS=1
else
    echo "✅ jwt 正常"
fi

# 检查其他关键依赖
python -c "import fastapi" 2>/dev/null || { echo "❌ fastapi 缺失"; MISSING_DEPS=1; }
python -c "import sqlalchemy" 2>/dev/null || { echo "❌ sqlalchemy 缺失"; MISSING_DEPS=1; }
python -c "import passlib" 2>/dev/null || { echo "❌ passlib 缺失"; MISSING_DEPS=1; }
python -c "import uvicorn" 2>/dev/null || { echo "❌ uvicorn 缺失"; MISSING_DEPS=1; }

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo "重新安装所有依赖..."
    pip install --upgrade pip setuptools wheel --quiet
    pip install -r requirements.txt --force-reinstall --no-cache-dir
    
    if [ $? -eq 0 ]; then
        echo "✅ 依赖安装完成"
    else
        echo "❌ 依赖安装失败"
        exit 1
    fi
else
    echo "✅ 所有依赖正常"
fi
echo ""

# 4. 特别修复 anyio 和 jwt
echo "[4/6] 修复 anyio 和 jwt..."
echo "----------------------------------------"
echo "重新安装 anyio..."
pip install --upgrade --force-reinstall anyio --quiet
if [ $? -eq 0 ]; then
    echo "✅ anyio 已重新安装"
else
    echo "❌ anyio 安装失败"
fi

echo "安装 PyJWT..."
pip install PyJWT --quiet
if [ $? -eq 0 ]; then
    echo "✅ PyJWT 已安装"
else
    echo "❌ PyJWT 安装失败"
fi

echo "安装 python-jose (JWT 支持)..."
pip install python-jose[cryptography] --quiet
if [ $? -eq 0 ]; then
    echo "✅ python-jose 已安装"
else
    echo "❌ python-jose 安装失败"
fi

# 验证
echo "验证依赖..."
python -c "import anyio._backends; print('✅ anyio._backends OK')" 2>/dev/null || echo "❌ anyio._backends 仍然缺失"
python -c "import jwt; print('✅ jwt OK')" 2>/dev/null || echo "❌ jwt 仍然缺失"
echo ""

# 5. 检查 .env 配置
echo "[5/6] 检查 .env 配置..."
echo "----------------------------------------"
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "创建 .env 文件..."
    cat > "$BACKEND_DIR/.env" <<EOF
JWT_SECRET=production_secret_key_change_me_$(date +%s)
LOG_LEVEL=INFO
CORS_ORIGINS=https://aikz.usdt2026.cc,http://aikz.usdt2026.cc,http://localhost:3000
DATABASE_URL=sqlite:///./admin.db
EOF
    echo "✅ .env 文件已创建"
else
    echo "✅ .env 文件存在"
    
    # 确保 JWT_SECRET 存在
    if ! grep -q "JWT_SECRET" "$BACKEND_DIR/.env"; then
        echo "添加 JWT_SECRET..."
        echo "JWT_SECRET=production_secret_key_change_me_$(date +%s)" >> "$BACKEND_DIR/.env"
        echo "✅ JWT_SECRET 已添加"
    fi
fi
echo ""

# 6. 启动后端服务
echo "[6/6] 启动后端服务..."
echo "----------------------------------------"
cd "$PROJECT_DIR" || exit 1
sudo -u ubuntu pm2 start ecosystem.config.js --only backend
sleep 5

echo "检查服务状态:"
sudo -u ubuntu pm2 list | grep backend
echo ""

# 7. 验证服务
echo "=========================================="
echo "🧪 验证服务"
echo "=========================================="
echo ""

echo "等待服务启动 (10秒)..."
sleep 10

echo "检查端口 8000:"
PORT_8000=$(sudo ss -tlnp | grep ":8000" || echo "")
if [ -n "$PORT_8000" ]; then
    echo "✅ 端口 8000 正在监听"
    echo "   $PORT_8000"
else
    echo "❌ 端口 8000 未监听"
    echo "查看后端日志:"
    sudo -u ubuntu pm2 logs backend --lines 30 --nostream 2>&1 | tail -30
fi
echo ""

echo "测试 /health:"
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "✅ 后端健康检查成功 (HTTP $HEALTH_RESPONSE)"
    curl -s http://127.0.0.1:8000/health | head -3
else
    echo "❌ 后端健康检查失败: HTTP $HEALTH_RESPONSE"
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
echo "1. 后端日志: sudo -u ubuntu pm2 logs backend --lines 100"
echo "2. 依赖列表: $BACKEND_DIR/venv/bin/pip list | grep -E 'anyio|jwt|fastapi'"
echo "3. 虚拟环境: ls -la $BACKEND_DIR/venv/bin/"
echo ""

