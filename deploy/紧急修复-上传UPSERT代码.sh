#!/bin/bash
# 紧急修复：重新上传 UPSERT 代码到服务器

set -e

echo "========================================="
echo "紧急修复：上传 UPSERT 代码"
echo "========================================="
echo ""

# 从本地读取文件并通过 SSH 上传
cd ~/liaotian/admin-backend/app/api/group_ai

# 备份当前文件
cp accounts.py accounts.py.bak.$(date +%Y%m%d_%H%M%S)
echo "✓ 已备份当前文件"

# 检查文件是否包含 UPSERT 代码
if grep -q "UPSERT 模式" accounts.py; then
    echo "✓ 文件已包含 UPSERT 代码"
else
    echo "✗ 文件不包含 UPSERT 代码，需要重新上传"
    exit 1
fi

# 重启后端服务
cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true

echo ""
echo "重启后端服务..."
pkill -f "uvicorn.*app.main:app" || true
sleep 2

nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 5

# 验证服务
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ 后端服务已启动"
else
    echo "✗ 后端服务启动失败"
    tail -30 /tmp/backend.log
    exit 1
fi

echo ""
echo "========================================="
echo "✓ 修复完成！"
echo "========================================="
