#!/bin/bash
# 完整部署角色分配修复

set -e

echo "========================================="
echo "完整部署角色分配修复"
echo "开始时间: $(date)"
echo "========================================="
echo ""

cd ~/liaotian

echo "【步骤1】检查当前 Git 状态..."
git fetch origin
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "master")
echo "  当前分支: $CURRENT_BRANCH"

echo ""
echo "【步骤2】拉取最新代码..."
git pull origin $CURRENT_BRANCH || git pull origin master || git pull origin main

echo ""
echo "【步骤3】验证修复代码是否存在..."
if grep -q "同時檢查運行時管理器和數據庫" admin-backend/app/api/group_ai/role_assignments.py; then
    echo "  ✓ 修复代码已存在"
else
    echo "  ✗ 修复代码不存在，请检查代码是否已推送"
    exit 1
fi

echo ""
echo "【步骤4】停止现有后端服务..."
pkill -f "uvicorn.*app.main:app" || echo "  没有运行中的后端服务"
sleep 2

echo ""
echo "【步骤5】启动后端服务..."
cd ~/liaotian/admin-backend

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "  ✓ 虚拟环境已激活"
else
    echo "  ✗ 虚拟环境不存在"
    exit 1
fi

# 启动后端
echo "  正在启动后端服务..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "  后端进程 PID: $BACKEND_PID"

# 等待服务启动
echo "  等待服务启动..."
sleep 10

echo ""
echo "【步骤6】验证后端服务..."
# 检查进程是否存在
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "  ✓ 后端进程正在运行 (PID: $BACKEND_PID)"
else
    echo "  ✗ 后端进程未运行，查看日志："
    tail -30 /tmp/backend.log
    exit 1
fi

# 检查健康接口
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8000/health 2>&1 || echo -e "\n000")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "405" ]; then
    echo "  ✓ 后端健康检查通过 (HTTP $HTTP_CODE)"
else
    echo "  ⚠ 后端健康检查返回 HTTP $HTTP_CODE"
    echo "  查看日志："
    tail -30 /tmp/backend.log
fi

echo ""
echo "========================================="
echo "部署完成！"
echo "后端服务 PID: $BACKEND_PID"
echo "日志位置: /tmp/backend.log"
echo "========================================="
echo ""
echo "查看后端日志："
echo "  tail -f /tmp/backend.log"
echo ""
echo "验证角色分配修复："
echo "  1. 在浏览器中打开账号管理页面"
echo "  2. 尝试为账号分配剧本和角色"
echo "  3. 检查 F12 控制台，应该不再出现 400 错误"
echo "  4. 查看后端日志：tail -f /tmp/backend.log | grep '角色分配'"
echo ""
