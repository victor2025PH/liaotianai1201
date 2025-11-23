#!/bin/bash
# 启动服务的简化脚本

set -e

DEPLOY_DIR="${1:-/home/ubuntu}"

cd "$DEPLOY_DIR"

echo "=== 设置 PATH ==="
export PATH=$HOME/.local/bin:$PATH

echo ""
echo "=== 创建 .env 文件 ==="
cd admin-backend
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

echo ""
echo "=== 停止旧服务 ==="
pkill -f 'uvicorn' || true
sleep 2

echo ""
echo "=== 启动服务 ==="
cd "$DEPLOY_DIR"
mkdir -p logs
cd admin-backend
export PATH=$HOME/.local/bin:$PATH
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
echo $! > ../backend.pid
sleep 12

echo ""
echo "=== 检查进程 ==="
if ps -p $(cat ../backend.pid 2>/dev/null) > /dev/null 2>&1; then
    echo "✓ 进程运行中 (PID: $(cat ../backend.pid))"
    ps aux | grep uvicorn | grep -v grep
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
echo "=== 启动日志（最后 50 行）==="
tail -50 ../logs/backend.log 2>/dev/null || echo "日志文件不存在"

echo ""
echo "=== 健康检查 ==="
curl -s http://localhost:8000/health 2>&1 | head -5 || echo "健康检查失败"


