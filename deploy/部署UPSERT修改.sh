#!/bin/bash
# 部署 UPSERT 功能修改到服务器
# 在远程服务器 ubuntu@165.154.233.55 上执行

set -e

echo "========================================="
echo "部署 UPSERT 功能修改"
echo "开始时间: $(date)"
echo "========================================="
echo ""

cd ~/liaotian

# 1. 备份原始文件
echo "【步骤1】备份原始文件..."
cp admin-backend/app/api/group_ai/accounts.py admin-backend/app/api/group_ai/accounts.py.bak.$(date +%Y%m%d_%H%M%S)
echo "  ✓ 备份完成"
echo ""

# 2. 从 git 拉取最新代码（如果有）
echo "【步骤2】检查 git 状态..."
cd admin-backend
if git status --short app/api/group_ai/accounts.py 2>/dev/null | grep -q "M"; then
    echo "  ⚠ 文件有本地修改，需要手动应用"
else
    echo "  ✓ 文件状态正常"
fi
cd ..
echo ""

# 3. 重启后端服务
echo "【步骤3】重启后端服务..."
cd admin-backend
source .venv/bin/activate 2>/dev/null || true

# 停止旧进程
pkill -f "uvicorn.*app.main:app" || true
sleep 2

# 启动新进程
echo "  启动后端服务..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 5

# 验证服务是否启动
if curl -s http://localhost:8000/health | grep -q "ok" || curl -s http://localhost:8000/health | grep -q "OK"; then
    echo "  ✓ 后端服务已启动"
else
    echo "  ⚠ 后端服务可能未正常启动，请检查日志:"
    tail -20 /tmp/backend.log
fi
echo ""

echo "========================================="
echo "部署完成！"
echo "完成时间: $(date)"
echo "========================================="
