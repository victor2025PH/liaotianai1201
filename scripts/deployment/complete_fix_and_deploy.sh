#!/bin/bash
# 完整修复和部署脚本

set -e

DEPLOY_DIR="${1:-/home/ubuntu}"

cd "$DEPLOY_DIR"

echo "========================================"
echo "完整修复和部署"
echo "========================================"
echo ""

# 设置 PATH
export PATH=$HOME/.local/bin:$PATH

# 步骤 1: 安装 pip（如果未安装）
echo "[1/8] 检查 pip..."
if ! python3 -m pip --version 2>/dev/null; then
    echo "安装 pip..."
    curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    python3 /tmp/get-pip.py --user --break-system-packages
    rm /tmp/get-pip.py
fi
python3 -m pip --version

# 步骤 2: 安装构建工具（如果需要）
echo ""
echo "[2/8] 检查构建工具..."
if ! command -v gcc &> /dev/null; then
    echo "安装 gcc 和构建工具..."
    sudo apt-get update -qq
    sudo apt-get install -y build-essential python3-dev gcc
fi

# 步骤 3: 安装 admin-backend 依赖
echo ""
echo "[3/8] 安装 admin-backend 依赖..."
cd admin-backend
python3 -m pip install --user --upgrade --break-system-packages -r requirements.txt 2>&1 | tail -10

# 步骤 4: 安装根目录依赖（pyrogram 等）
echo ""
echo "[4/8] 安装根目录依赖..."
cd "$DEPLOY_DIR"
if [ -f "requirements.txt" ]; then
    python3 -m pip install --user --upgrade --break-system-packages -r requirements.txt 2>&1 | tail -10
fi

# 步骤 5: 修复 cache.py
echo ""
echo "[5/8] 修复 cache.py..."
cd admin-backend/app/core
if ! grep -q "def cached(prefix: str = \"cache\"" cache.py; then
    cat >> cache.py << 'ENDFUNC'

def cached(prefix: str = "cache", ttl: Optional[int] = None):
    """
    缓存装饰器（独立函数版本）
    """
    cache_manager = get_cache_manager()
    return cache_manager.cached(prefix=prefix, ttl=ttl)


def invalidate_cache(pattern: str) -> int:
    """
    使缓存失效
    """
    cache_manager = get_cache_manager()
    return asyncio.run(cache_manager.clear_pattern(pattern))
ENDFUNC
    echo "✓ cached 函数已添加"
else
    echo "✓ cached 函数已存在"
fi

# 步骤 6: 创建 .env 文件
echo ""
echo "[6/8] 创建 .env 文件..."
cd "$DEPLOY_DIR/admin-backend"
if [ ! -f ".env" ]; then
    python3 << 'PYEOF'
import secrets
jwt_secret = secrets.token_hex(32)
with open(".env", "w") as f:
    f.write("DATABASE_URL=sqlite:///./admin.db\n")
    f.write(f"JWT_SECRET={jwt_secret}\n")
    f.write("ADMIN_DEFAULT_EMAIL=admin@example.com\n")
    f.write("ADMIN_DEFAULT_PASSWORD=changeme123\n")
    f.write("CORS_ORIGINS=http://localhost:3000,http://localhost:5173\n")
print(".env created")
PYEOF
    echo ".env 已创建"
else
    echo ".env 已存在"
fi

# 步骤 7: 启动服务
echo ""
echo "[7/8] 启动服务..."
cd "$DEPLOY_DIR"
mkdir -p logs
cd admin-backend
pkill -f uvicorn || true
sleep 2
export PATH=$HOME/.local/bin:$PATH
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
echo $! > ../backend.pid
sleep 15

# 步骤 8: 验证服务
echo ""
echo "[8/8] 验证服务..."
cd "$DEPLOY_DIR"
echo "=== 进程检查 ==="
if ps -p $(cat backend.pid 2>/dev/null) > /dev/null 2>&1; then
    echo "✓ 进程运行中 (PID: $(cat backend.pid))"
    ps aux | grep uvicorn | grep -v grep
else
    echo "✗ 进程已退出"
fi

echo ""
echo "=== 端口检查 ==="
if ss -tlnp 2>/dev/null | grep -q ':8000'; then
    echo "✓ 端口 8000 监听中"
    ss -tlnp 2>/dev/null | grep ':8000'
else
    echo "✗ 端口 8000 未监听"
fi

echo ""
echo "=== 启动日志（最后 50 行）==="
tail -50 logs/backend.log 2>/dev/null || echo "日志文件不存在"

echo ""
echo "=== 健康检查 ==="
curl -s http://localhost:8000/health 2>&1 | head -5 || echo "健康检查失败"

echo ""
echo "========================================"
echo "完成"
echo "========================================"


