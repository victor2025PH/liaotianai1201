#!/bin/bash
# 简单启动服务脚本

echo "启动后端服务..."
cd ~/liaotian/admin-backend
source .venv/bin/activate
pkill -f uvicorn || true
sleep 2
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 &
echo "后端已启动，日志: /tmp/backend_final.log"
sleep 5
curl http://localhost:8000/health && echo ""
