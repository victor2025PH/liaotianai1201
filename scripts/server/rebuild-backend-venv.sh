#!/bin/bash
# ============================================================
# 完全重建后端虚拟环境
# ============================================================

echo "=========================================="
echo "🔧 完全重建后端虚拟环境"
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

# 2. 备份现有虚拟环境（如果需要）
echo "[2/7] 备份现有虚拟环境..."
echo "----------------------------------------"
if [ -d "$BACKEND_DIR/venv" ]; then
    BACKUP_DIR="${BACKEND_DIR}/venv.backup.$(date +%Y%m%d_%H%M%S)"
    echo "备份到: $BACKUP_DIR"
    mv "$BACKEND_DIR/venv" "$BACKUP_DIR" 2>/dev/null || true
    echo "✅ 虚拟环境已备份"
else
    echo "✅ 虚拟环境不存在，无需备份"
fi
echo ""

# 3. 完全删除旧虚拟环境
echo "[3/7] 完全删除旧虚拟环境..."
echo "----------------------------------------"
if [ -d "$BACKEND_DIR/venv" ]; then
    rm -rf "$BACKEND_DIR/venv"
    echo "✅ 旧虚拟环境已删除"
else
    echo "✅ 虚拟环境已不存在"
fi
echo ""

# 4. 创建新的虚拟环境
echo "[4/7] 创建新的虚拟环境..."
echo "----------------------------------------"
cd "$BACKEND_DIR" || exit 1

# 确保使用正确的 Python 版本
PYTHON_CMD=$(which python3)
if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python3 未找到"
    exit 1
fi

echo "使用 Python: $PYTHON_CMD"
$PYTHON_CMD --version

echo "创建虚拟环境..."
$PYTHON_CMD -m venv venv

if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境创建失败"
    exit 1
fi

echo "✅ 虚拟环境已创建"
echo ""

# 5. 激活虚拟环境并升级基础工具
echo "[5/7] 升级基础工具..."
echo "----------------------------------------"
source venv/bin/activate

echo "升级 pip..."
pip install --upgrade pip setuptools wheel --quiet
if [ $? -ne 0 ]; then
    echo "❌ pip 升级失败"
    exit 1
fi
echo "✅ pip 已升级"

echo "升级 setuptools..."
pip install --upgrade setuptools --quiet
echo "✅ setuptools 已升级"
echo ""

# 6. 安装依赖（分步安装，避免冲突）
echo "[6/7] 安装依赖..."
echo "----------------------------------------"

# 先安装基础依赖
echo "安装基础依赖..."
pip install --upgrade pip setuptools wheel --quiet

# 安装核心框架
echo "安装核心框架..."
pip install fastapi uvicorn[standard] --quiet
if [ $? -ne 0 ]; then
    echo "❌ 核心框架安装失败"
    exit 1
fi
echo "✅ 核心框架已安装"

# 安装数据库相关
echo "安装数据库相关..."
pip install sqlalchemy --quiet
if [ $? -ne 0 ]; then
    echo "❌ 数据库依赖安装失败"
    exit 1
fi
echo "✅ 数据库依赖已安装"

# 安装认证相关
echo "安装认证相关..."
pip install python-jose[cryptography] passlib[bcrypt] PyJWT --quiet
if [ $? -ne 0 ]; then
    echo "❌ 认证依赖安装失败"
    exit 1
fi
echo "✅ 认证依赖已安装"

# 安装 HTTP 客户端
echo "安装 HTTP 客户端..."
pip install httpx requests --quiet
if [ $? -ne 0 ]; then
    echo "❌ HTTP 客户端安装失败"
    exit 1
fi
echo "✅ HTTP 客户端已安装"

# 安装其他依赖（从 requirements.txt）
echo "安装其他依赖..."
if [ -f "requirements.txt" ]; then
    # 先尝试安装所有依赖
    pip install -r requirements.txt --quiet
    
    if [ $? -ne 0 ]; then
        echo "⚠️  部分依赖安装失败，尝试逐个安装..."
        # 如果批量安装失败，尝试逐个安装关键依赖
        while IFS= read -r line; do
            # 跳过注释和空行
            [[ "$line" =~ ^#.*$ ]] && continue
            [[ -z "$line" ]] && continue
            
            # 提取包名（去掉版本号）
            package=$(echo "$line" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1 | tr -d ' ')
            if [ -n "$package" ]; then
                echo "  安装: $package"
                pip install "$package" --quiet 2>/dev/null || true
            fi
        done < requirements.txt
    fi
    echo "✅ 其他依赖已安装"
else
    echo "⚠️  requirements.txt 不存在"
fi
echo ""

# 7. 验证关键依赖
echo "[7/7] 验证关键依赖..."
echo "----------------------------------------"
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

echo "检查关键依赖:"
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
    echo "❌ anyio._backends 缺失，重新安装 anyio..."
    pip install --upgrade --force-reinstall anyio --quiet
    python -c "import anyio._backends" 2>/dev/null && echo "✅ anyio._backends 已修复" || echo "❌ anyio._backends 仍然缺失"
fi

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "⚠️  部分依赖缺失，尝试修复..."
    pip install --upgrade --force-reinstall fastapi uvicorn sqlalchemy python-jose[cryptography] passlib[bcrypt] PyJWT httpx requests anyio --quiet
fi
echo ""

# 8. 检查 .env 配置
echo "=========================================="
echo "🔧 检查配置"
echo "=========================================="
echo ""

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
echo "✅ 虚拟环境重建完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请检查:"
echo "1. 后端日志: sudo -u ubuntu pm2 logs backend --lines 100"
echo "2. 依赖列表: $BACKEND_DIR/venv/bin/pip list"
echo "3. Python 版本: $BACKEND_DIR/venv/bin/python --version"
echo ""

