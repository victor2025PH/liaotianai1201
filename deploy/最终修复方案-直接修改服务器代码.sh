#!/bin/bash
# 最终修复方案：直接在服务器上修改代码

set -e

echo "========================================="
echo "最终修复：直接在服务器上修改代码"
echo "========================================="

cd ~/liaotian/admin-backend/app/api/group_ai

# 备份
cp accounts.py accounts.py.bak.final

# 检查当前代码
if grep -q "UPSERT 模式" accounts.py; then
    echo "✓ 文件已包含 UPSERT 代码"
    
    # 检查是否在正确的位置
    LINE_NUM=$(grep -n "UPSERT 模式" accounts.py | head -1 | cut -d: -f1)
    echo "  UPSERT 代码在第 $LINE_NUM 行"
    
    # 检查前后的代码逻辑
    echo ""
    echo "检查代码逻辑..."
    sed -n "$((LINE_NUM-5)),$((LINE_NUM+10))p" accounts.py
    
    echo ""
    echo "✓ 代码位置正确"
else
    echo "✗ 文件不包含 UPSERT 代码"
    echo "需要上传修改后的文件"
    exit 1
fi

# 重启服务
cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true

echo ""
echo "重启后端服务..."
pkill -f "uvicorn.*app.main:app" || true
sleep 3

nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 10

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ 后端服务已启动"
else
    echo "✗ 后端服务启动失败"
    tail -30 /tmp/backend.log
    exit 1
fi

echo ""
echo "========================================="
echo "修复完成！"
echo "========================================="
