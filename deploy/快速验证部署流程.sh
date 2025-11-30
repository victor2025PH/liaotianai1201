#!/bin/bash
# 快速验证部署流程（在服务器上执行）
# 使用方法: bash deploy/快速验证部署流程.sh

echo "========================================="
echo "快速验证部署流程"
echo "========================================="
echo ""

# 1. 检查脚本行尾符
echo "【1】检查脚本行尾符..."
if [ -f ~/liaotian/deploy/从GitHub拉取并部署.sh ]; then
    FILE_TYPE=$(file ~/liaotian/deploy/从GitHub拉取并部署.sh)
    echo "  文件类型: $FILE_TYPE"
    
    CR_COUNT=$(od -c ~/liaotian/deploy/从GitHub拉取并部署.sh | grep -c '\r' || echo "0")
    if [ "$CR_COUNT" -eq "0" ]; then
        echo "  ✓ 行尾符正确（无 CR 字符）"
    else
        echo "  ✗ 发现 $CR_COUNT 个 CR 字符，需要转换"
        echo "  执行转换..."
        sed -i 's/\r$//' ~/liaotian/deploy/从GitHub拉取并部署.sh
        echo "  ✓ 已转换"
    fi
    
    # 检查语法
    if bash -n ~/liaotian/deploy/从GitHub拉取并部署.sh 2>&1; then
        echo "  ✓ 脚本语法正确"
    else
        echo "  ✗ 脚本语法错误"
        exit 1
    fi
else
    echo "  ✗ 脚本文件不存在"
    exit 1
fi
echo ""

# 2. 检查 Git 仓库状态
echo "【2】检查 Git 仓库状态..."
cd ~/liaotian
if [ -d ".git" ]; then
    echo "  ✓ Git 仓库存在"
    
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "master")
    echo "  当前分支: $CURRENT_BRANCH"
    
    REMOTE_URL=$(git remote get-url origin 2>&1)
    echo "  远程仓库: $REMOTE_URL"
    
    LATEST_COMMIT=$(git log -1 --oneline 2>/dev/null)
    echo "  最新提交: $LATEST_COMMIT"
else
    echo "  ✗ Git 仓库不存在"
    exit 1
fi
echo ""

# 3. 检查后端服务状态
echo "【3】检查后端服务状态..."
if pgrep -f 'uvicorn.*app.main:app' > /dev/null; then
    echo "  ✓ 后端服务正在运行"
    BACKEND_PID=$(pgrep -f 'uvicorn.*app.main:app' | head -1)
    echo "  进程 PID: $BACKEND_PID"
else
    echo "  ✗ 后端服务未运行"
fi

# 检查端口
if sudo ss -tlnp | grep -q ':8000 '; then
    echo "  ✓ 端口 8000 正在监听"
else
    echo "  ✗ 端口 8000 未监听"
fi

# 健康检查
if curl -s http://localhost:8000/health | grep -q "ok" 2>/dev/null; then
    echo "  ✓ 健康检查通过"
else
    echo "  ✗ 健康检查失败"
fi
echo ""

# 4. 检查代码版本
echo "【4】检查代码版本..."
if [ -f "admin-backend/app/api/group_ai/accounts.py" ]; then
    UPSERT_COUNT=$(grep -c "UPSERT\|如果不存在.*创建\|account not found.*create" admin-backend/app/api/group_ai/accounts.py 2>/dev/null || echo "0")
    echo "  ✓ accounts.py 存在"
    echo "  包含 UPSERT 相关代码: $UPSERT_COUNT 处"
else
    echo "  ✗ accounts.py 不存在"
fi
echo ""

echo "========================================="
echo "验证完成"
echo "========================================="
echo ""
