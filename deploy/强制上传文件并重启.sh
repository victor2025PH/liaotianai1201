#!/bin/bash
# 强制上传文件并重启服务

echo "========================================="
echo "强制上传 UPSERT 代码并重启服务"
echo "========================================="

cd ~/liaotian/admin-backend/app/api/group_ai

# 检查文件是否包含 UPSERT
if grep -q "UPSERT 模式" accounts.py; then
    echo "✓ 文件已包含 UPSERT 代码"
else
    echo "✗ 文件不包含 UPSERT 代码，需要上传"
    exit 1
fi

# 重启后端服务
cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true

echo "停止旧服务..."
pkill -f "uvicorn.*app.main:app" || true
sleep 3

echo "启动新服务..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 8

# 验证
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ 服务已启动"
else
    echo "✗ 服务启动失败，查看日志:"
    tail -50 /tmp/backend.log
fi

echo "========================================="
