#!/bin/bash
# 检查后端健康状态

echo "=== 检查后端服务状态 ==="
echo ""

# 1. PM2 状态
echo "1. PM2 进程状态:"
pm2 list | grep backend
echo ""

# 2. 检查后端 API 健康端点
echo "2. 测试后端健康端点:"
curl -s http://127.0.0.1:8000/health || echo "❌ 后端未响应"
echo ""
echo ""

# 3. 检查后端日志（最近20行，无错误）
echo "3. 后端标准输出日志（最近20行）:"
pm2 logs backend --lines 20 --nostream --out 2>/dev/null | tail -20
echo ""

# 4. 检查后端错误日志
echo "4. 后端错误日志（最近20行）:"
pm2 logs backend --lines 20 --nostream --err 2>/dev/null | tail -20
echo ""

# 5. 检查端口占用
echo "5. 端口 8000 占用情况:"
lsof -ti :8000 2>/dev/null && echo "✅ 端口 8000 已被占用（后端正在运行）" || echo "❌ 端口 8000 未被占用"
echo ""

# 6. 检查进程
echo "6. 后端进程信息:"
ps aux | grep -E "uvicorn|gunicorn|python.*main.py" | grep -v grep | head -3
echo ""

echo "=== 检查完成 ==="
