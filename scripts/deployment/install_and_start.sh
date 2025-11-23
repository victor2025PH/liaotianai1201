#!/bin/bash
# 安装依赖并启动服务

set -e

DEPLOY_DIR="${1:-/home/ubuntu}"

cd "$DEPLOY_DIR"

echo "=== 停止旧服务 ==="
pkill -f 'uvicorn' || true
sleep 2

echo ""
echo "=== 安装依赖 ==="
python3 -m pip install uvicorn fastapi --user --upgrade

echo ""
echo "=== 验证安装 ==="
python3 -c "import uvicorn; print('uvicorn:', uvicorn.__version__)"

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
fi

echo ""
echo "=== 启动服务 ==="
mkdir -p ../logs
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
echo $! > ../backend.pid
sleep 8

echo ""
echo "=== 检查进程 ==="
ps -p $(cat ../backend.pid 2>/dev/null) && echo "✓ 进程运行中" || echo "✗ 进程已退出"

echo ""
echo "=== 检查端口 ==="
ss -tlnp 2>/dev/null | grep ':8000' && echo "✓ 端口 8000 监听中" || echo "✗ 端口 8000 未监听"

echo ""
echo "=== 启动日志（最后 30 行）==="
tail -30 ../logs/backend.log 2>/dev/null || echo "日志文件不存在"

