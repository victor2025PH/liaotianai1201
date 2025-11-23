#!/bin/bash
# 安装 pip 并部署服务

set -e

DEPLOY_DIR="${1:-/home/ubuntu}"

cd "$DEPLOY_DIR"

echo "=== 停止旧服务 ==="
pkill -f 'uvicorn' || true
sleep 2

echo ""
echo "=== 检查 Python 环境 ==="
python3 --version
which python3

echo ""
echo "=== 安装 pip ==="
# 尝试不同的方法安装 pip
if ! python3 -m pip --version 2>/dev/null; then
    echo "pip 未安装，正在安装..."
    # 方法 1: 使用 get-pip.py (Ubuntu 24.04 需要 --break-system-packages)
    curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    python3 /tmp/get-pip.py --user --break-system-packages 2>&1 || {
        echo "get-pip.py 失败，尝试使用 apt..."
        sudo apt-get update -qq
        sudo apt-get install -y python3-pip
    }
    rm -f /tmp/get-pip.py
fi

echo ""
echo "=== 验证 pip 安装 ==="
python3 -m pip --version

echo ""
echo "=== 安装依赖 ==="
python3 -m pip install --user --upgrade --break-system-packages pip
python3 -m pip install --user --upgrade --break-system-packages uvicorn fastapi

echo ""
echo "=== 验证安装 ==="
python3 -c "import uvicorn; print('✓ uvicorn:', uvicorn.__version__)"
python3 -c "import fastapi; print('✓ fastapi:', fastapi.__version__)"

echo ""
echo "=== 检查配置文件 ==="
cd admin-backend
if [ ! -f ".env" ]; then
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "change_me")
    cat > .env << EOF
DATABASE_URL=sqlite:///./admin.db
JWT_SECRET=$JWT_SECRET
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
    echo ".env 已创建"
else
    echo ".env 已存在"
fi

echo ""
echo "=== 启动服务 ==="
mkdir -p ../logs
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
echo $! > ../backend.pid
sleep 10

echo ""
echo "=== 检查进程 ==="
if ps -p $(cat ../backend.pid 2>/dev/null) > /dev/null 2>&1; then
    echo "✓ 进程运行中 (PID: $(cat ../backend.pid))"
else
    echo "✗ 进程已退出"
fi

echo ""
echo "=== 检查端口 ==="
if ss -tlnp 2>/dev/null | grep -q ':8000'; then
    echo "✓ 端口 8000 监听中"
    ss -tlnp 2>/dev/null | grep ':8000'
else
    echo "✗ 端口 8000 未监听"
fi

echo ""
echo "=== 启动日志（最后 30 行）==="
tail -30 ../logs/backend.log 2>/dev/null || echo "日志文件不存在"

echo ""
echo "=== 健康检查 ==="
curl -s http://localhost:8000/health 2>&1 | head -5 || echo "健康检查失败"

