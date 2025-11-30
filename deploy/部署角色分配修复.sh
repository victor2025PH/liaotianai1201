#!/bin/bash
# 部署角色分配修复 - 同时检查数据库和运行时管理器

set -e

echo "========================================="
echo "部署角色分配修复"
echo "开始时间: $(date)"
echo "========================================="
echo ""

cd ~/liaotian

# 检查 Git 仓库
if [ ! -d ".git" ]; then
    echo "✗ 当前目录不是 Git 仓库"
    exit 1
fi

echo "【步骤1】从 GitHub 拉取最新代码..."
git fetch origin
BRANCH=$(git branch --show-current 2>/dev/null || echo "master")
echo "  当前分支: $BRANCH"

git pull origin $BRANCH || git pull origin master || git pull origin main

if [ $? -eq 0 ]; then
    echo "  ✓ 代码拉取完成"
    echo ""
    echo "  最近的提交:"
    git log --oneline -3 | head -3
    echo ""
else
    echo "  ✗ 代码拉取失败"
    exit 1
fi

echo "【步骤2】检查后端代码..."
if [ ! -f "admin-backend/app/api/group_ai/role_assignments.py" ]; then
    echo "  ✗ 找不到 role_assignments.py 文件"
    exit 1
fi

# 检查是否包含修复内容
if grep -q "同時檢查運行時管理器和數據庫" admin-backend/app/api/group_ai/role_assignments.py; then
    echo "  ✓ 修复代码已包含"
else
    echo "  ⚠ 警告：可能未找到修复代码，继续部署..."
fi
echo ""

echo "【步骤3】重启后端服务..."
cd ~/liaotian/admin-backend

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "  ✓ 虚拟环境已激活"
else
    echo "  ⚠ 警告：未找到虚拟环境"
fi

# 停止现有服务
pkill -f "uvicorn.*app.main:app" || echo "  没有运行中的后端服务"

# 启动后端服务
echo "  启动后端服务..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

# 等待服务启动
sleep 5

# 检查服务是否启动
if ps -p $BACKEND_PID > /dev/null; then
    echo "  ✓ 后端服务已启动 (PID: $BACKEND_PID)"
else
    echo "  ✗ 后端服务启动失败，查看日志："
    tail -20 /tmp/backend.log
    exit 1
fi

echo ""

echo "【步骤4】验证后端服务..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")

if [ "$HEALTH_CHECK" = "200" ] || [ "$HEALTH_CHECK" = "405" ]; then
    echo "  ✓ 后端健康检查通过 (HTTP $HEALTH_CHECK)"
else
    echo "  ⚠ 后端健康检查返回 HTTP $HEALTH_CHECK"
    echo "  查看日志："
    tail -20 /tmp/backend.log
fi

echo ""

echo "========================================="
echo "部署完成！"
echo "后端服务 PID: $BACKEND_PID"
echo "日志位置: /tmp/backend.log"
echo "========================================="
echo ""
echo "验证步骤："
echo "1. 在浏览器中打开账号管理页面"
echo "2. 尝试为账号分配剧本和角色"
echo "3. 检查 F12 控制台，应该不再出现 400 错误"
echo "4. 查看后端日志：tail -f /tmp/backend.log | grep '角色分配'"
echo ""
