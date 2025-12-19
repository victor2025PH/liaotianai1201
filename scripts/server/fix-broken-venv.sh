#!/bin/bash
# ============================================================
# 修复损坏的虚拟环境（pip 和 uvicorn 缺失）
# ============================================================

echo "=========================================="
echo "🔧 修复损坏的虚拟环境"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"

# 1. 停止后端服务
echo "[1/8] 停止后端服务..."
echo "----------------------------------------"
sudo -u ubuntu pm2 stop backend 2>/dev/null || true
sudo -u ubuntu pm2 delete backend 2>/dev/null || true
sleep 2

# 清理端口
sudo lsof -t -i:8000 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
sleep 2
echo "✅ 后端服务已停止"
echo ""

# 2. 检查虚拟环境是否存在
echo "[2/8] 检查虚拟环境..."
echo "----------------------------------------"
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 rebuild-backend-venv.sh"
    exit 1
fi
echo "✅ 虚拟环境存在"
echo ""

# 3. 修复 pip（使用 get-pip.py）
echo "[3/8] 修复 pip..."
echo "----------------------------------------"
cd "$BACKEND_DIR" || exit 1

# 激活虚拟环境
source venv/bin/activate

# 检查 pip 是否可用
if ! python -m pip --version >/dev/null 2>&1; then
    echo "pip 模块损坏，正在修复..."
    
    # 下载 get-pip.py
    curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    
    # 使用 get-pip.py 重新安装 pip
    python /tmp/get-pip.py --force-reinstall --no-warn-script-location
    
    if [ $? -eq 0 ]; then
        echo "✅ pip 已修复"
    else
        echo "❌ pip 修复失败，尝试使用 ensurepip..."
        python -m ensurepip --upgrade --default-pip
        if [ $? -eq 0 ]; then
            echo "✅ pip 已通过 ensurepip 修复"
        else
            echo "❌ pip 修复失败，需要重建虚拟环境"
            exit 1
        fi
    fi
else
    echo "✅ pip 正常"
fi

# 验证 pip
python -m pip --version
echo ""

# 4. 升级基础工具
echo "[4/8] 升级基础工具..."
echo "----------------------------------------"
python -m pip install --upgrade pip setuptools wheel --quiet
if [ $? -ne 0 ]; then
    echo "❌ 基础工具升级失败"
    exit 1
fi
echo "✅ 基础工具已升级"
echo ""

# 5. 重新安装 uvicorn
echo "[5/8] 重新安装 uvicorn..."
echo "----------------------------------------"
python -m pip install --upgrade --force-reinstall uvicorn[standard] --quiet
if [ $? -ne 0 ]; then
    echo "❌ uvicorn 安装失败"
    exit 1
fi

# 验证 uvicorn
if python -c "import uvicorn" 2>/dev/null; then
    echo "✅ uvicorn 已安装"
    python -c "import uvicorn; print(f'uvicorn 版本: {uvicorn.__version__}')" 2>/dev/null || true
else
    echo "❌ uvicorn 验证失败"
    exit 1
fi

# 验证 uvicorn 可执行文件
if [ -f "venv/bin/uvicorn" ]; then
    echo "✅ uvicorn 可执行文件存在"
else
    echo "❌ uvicorn 可执行文件不存在"
    exit 1
fi
echo ""

# 6. 重新安装 anyio（修复 anyio._backends）
echo "[6/8] 重新安装 anyio..."
echo "----------------------------------------"
python -m pip install --upgrade --force-reinstall anyio --quiet
if [ $? -ne 0 ]; then
    echo "❌ anyio 安装失败"
    exit 1
fi

# 验证 anyio._backends
if python -c "import anyio._backends" 2>/dev/null; then
    echo "✅ anyio._backends 已修复"
else
    echo "❌ anyio._backends 仍然缺失"
    exit 1
fi
echo ""

# 7. 重新安装其他关键依赖
echo "[7/8] 重新安装其他关键依赖..."
echo "----------------------------------------"
python -m pip install --upgrade --force-reinstall \
    fastapi \
    sqlalchemy \
    python-jose[cryptography] \
    passlib[bcrypt] \
    PyJWT \
    httpx \
    requests \
    --quiet

if [ $? -ne 0 ]; then
    echo "⚠️  部分依赖安装失败，继续..."
fi

# 验证关键依赖
echo "验证关键依赖:"
MISSING=0

check_dep() {
    python -c "import $1" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ $1"
        return 0
    else
        echo "❌ $1 缺失"
        MISSING=1
        return 1
    fi
}

check_dep fastapi
check_dep uvicorn
check_dep sqlalchemy
check_dep jose
check_dep jwt
check_dep passlib
check_dep httpx
check_dep requests
check_dep anyio

# 特别检查 anyio._backends
python -c "import anyio._backends" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ anyio._backends"
else
    echo "❌ anyio._backends 仍然缺失"
    MISSING=1
fi

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "⚠️  部分依赖缺失，尝试从 requirements.txt 重新安装..."
    if [ -f "requirements.txt" ]; then
        python -m pip install -r requirements.txt --force-reinstall --no-deps --quiet 2>/dev/null || true
        python -m pip install -r requirements.txt --quiet 2>/dev/null || true
    fi
fi
echo ""

# 8. 检查 .env 配置
echo "[8/8] 检查配置..."
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

# 9. 启动后端服务
echo "=========================================="
echo "🚀 启动后端服务"
echo "=========================================="
echo ""

cd "$PROJECT_DIR" || exit 1
sudo -u ubuntu pm2 start ecosystem.config.js --only backend
sleep 5

echo "检查服务状态:"
sudo -u ubuntu pm2 list | grep backend
echo ""

# 10. 验证服务
echo "=========================================="
echo "🧪 验证服务"
echo "=========================================="
echo ""

echo "等待服务启动 (15秒)..."
sleep 15

echo "检查端口 8000:"
PORT_8000=$(sudo ss -tlnp | grep ":8000" || echo "")
if [ -n "$PORT_8000" ]; then
    echo "✅ 端口 8000 正在监听"
    echo "   $PORT_8000"
else
    echo "❌ 端口 8000 未监听"
    echo "查看后端日志:"
    sudo -u ubuntu pm2 logs backend --lines 50 --nostream 2>&1 | tail -50
    echo ""
    echo "⚠️  如果日志显示 uvicorn 缺失，请运行: bash scripts/server/rebuild-backend-venv.sh"
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
echo "✅ 虚拟环境修复完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请运行:"
echo "  bash scripts/server/rebuild-backend-venv.sh"
echo ""

