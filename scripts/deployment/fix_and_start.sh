#!/bin/bash
# 修复 Query 导入并启动服务

echo "🔧 修复 Query 导入..."
cd /home/ubuntu/admin-backend

# 使用 Python 修复
python3 << 'PYEOF'
import sys
file_path = "/home/ubuntu/admin-backend/app/main.py"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
if "Query" not in lines[0]:
    lines[0] = lines[0].replace(
        "from fastapi import FastAPI, Request",
        "from fastapi import FastAPI, Request, Query"
    )
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("✓ Query 已添加")
else:
    print("✓ Query 已存在")
print("第一行:", lines[0].strip())
PYEOF

echo ""
echo "🚀 停止旧服务..."
pkill -f uvicorn
sleep 2

echo ""
echo "🚀 启动服务..."
cd /home/ubuntu/admin-backend
export PATH=$HOME/.local/bin:$PATH
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &

echo "等待服务启动..."
sleep 12

echo ""
echo "📊 检查服务状态..."
if ps aux | grep uvicorn | grep -v grep > /dev/null; then
    echo "✓ 服务运行中"
    ps aux | grep uvicorn | grep -v grep
else
    echo "✗ 服务未运行"
    echo "错误日志:"
    tail -25 /home/ubuntu/logs/backend.log 2>/dev/null
fi

echo ""
echo "📊 检查端口..."
if ss -tlnp 2>/dev/null | grep :8000 > /dev/null; then
    echo "✓ 端口 8000 监听中"
    ss -tlnp 2>/dev/null | grep :8000
else
    echo "✗ 端口未监听"
fi

echo ""
echo "📊 测试健康检查..."
health=$(curl -s http://localhost:8000/health 2>/dev/null)
if echo "$health" | grep -q "status\|healthy"; then
    echo "✓ 健康检查通过"
    echo "$health" | head -10
else
    echo "✗ 健康检查失败"
    echo "$health"
fi

