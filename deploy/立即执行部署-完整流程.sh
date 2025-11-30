#!/bin/bash
# 立即执行部署 - 完整流程
# 此脚本在服务器上执行，确保从GitHub拉取代码并部署

set -e

echo "========================================="
echo "立即执行部署 - 完整流程"
echo "开始时间: $(date)"
echo "========================================="
echo ""

# 步骤 1: 确保在正确的目录
cd ~/liaotian || {
    echo "✗ 错误: 无法切换到 ~/liaotian 目录"
    exit 1
}

echo "【步骤1】检查当前目录..."
echo "  当前目录: $(pwd)"
echo "  ✓ 目录检查完成"
echo ""

# 步骤 2: 从GitHub拉取最新代码
echo "【步骤2】从 GitHub 拉取最新代码..."
echo "  当前分支: $(git branch --show-current 2>/dev/null || echo 'master')"
git fetch origin
BRANCH=$(git branch --show-current 2>/dev/null || echo "master")
git pull origin $BRANCH || git pull origin master || git pull origin main

if [ $? -eq 0 ]; then
    echo "  ✓ 代码拉取完成"
    echo ""
    echo "  最近的提交:"
    git log --oneline -1
    echo ""
else
    echo "  ✗ 代码拉取失败"
    exit 1
fi

# 步骤 3: 确保部署脚本存在且可执行
echo "【步骤3】准备部署脚本..."
if [ -f "deploy/从GitHub拉取并部署.sh" ]; then
    echo "  脚本已存在"
    # 转换行尾符
    sed -i 's/\r$//' deploy/从GitHub拉取并部署.sh 2>/dev/null || sed -i '' 's/\r$//' deploy/从GitHub拉取并部署.sh 2>/dev/null || true
    chmod +x deploy/从GitHub拉取并部署.sh
    echo "  ✓ 脚本已准备（行尾符已转换）"
else
    echo "  ✗ 错误: 部署脚本不存在"
    exit 1
fi
echo ""

# 步骤 4: 执行部署脚本
echo "【步骤4】执行部署脚本..."
echo "========================================="
echo ""

bash deploy/从GitHub拉取并部署.sh

DEPLOY_EXIT_CODE=$?

echo ""
echo "========================================="

if [ $DEPLOY_EXIT_CODE -eq 0 ]; then
    echo "  ✓ 部署完成！"
else
    echo "  ✗ 部署失败（退出码: $DEPLOY_EXIT_CODE）"
    exit $DEPLOY_EXIT_CODE
fi

echo "========================================="
echo "完成时间: $(date)"
echo "========================================="
