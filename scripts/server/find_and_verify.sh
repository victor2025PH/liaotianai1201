#!/bin/bash
# 查找项目目录并执行验证

echo "=========================================="
echo "查找项目目录并执行验证"
echo "=========================================="
echo ""

# 可能的项目路径
POSSIBLE_PATHS=(
    "/home/ubuntu/telegram-ai-system"
    "$HOME/telegram-ai-system"
    "/opt/telegram-ai-system"
    "$(pwd)"
)

PROJECT_DIR=""

# 查找项目目录
for path in "${POSSIBLE_PATHS[@]}"; do
    if [ -d "$path" ] && [ -d "$path/.git" ]; then
        PROJECT_DIR="$path"
        echo "✓ 找到项目目录: $PROJECT_DIR"
        break
    fi
done

# 如果没找到，检查当前目录
if [ -z "$PROJECT_DIR" ]; then
    if [ -d ".git" ]; then
        PROJECT_DIR="$(pwd)"
        echo "✓ 当前目录是项目目录: $PROJECT_DIR"
    else
        echo "✗ 未找到项目目录"
        echo ""
        echo "请执行以下命令之一："
        echo "1. 如果项目已存在，导航到项目目录："
        echo "   cd /home/ubuntu/telegram-ai-system"
        echo ""
        echo "2. 如果项目不存在，克隆项目："
        echo "   cd /home/ubuntu"
        echo "   git clone https://github.com/victor2025PH/liaotianai1201.git telegram-ai-system"
        echo "   cd telegram-ai-system"
        exit 1
    fi
fi

# 进入项目目录
cd "$PROJECT_DIR" || exit 1

echo ""
echo "当前目录: $(pwd)"
echo ""

# 检查脚本是否存在
if [ ! -f "scripts/server/verify_deployment.sh" ]; then
    echo "⚠️  验证脚本不存在，拉取最新代码..."
    git pull origin main || {
        echo "✗ Git pull 失败"
        echo "请检查："
        echo "1. 是否在正确的项目目录"
        echo "2. Git 远程仓库配置是否正确"
        exit 1
    }
fi

# 执行验证
if [ -f "scripts/server/verify_deployment.sh" ]; then
    echo "执行部署验证..."
    bash scripts/server/verify_deployment.sh
else
    echo "✗ 验证脚本仍然不存在"
    echo "请检查项目结构或手动拉取代码"
    exit 1
fi

