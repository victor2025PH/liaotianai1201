#!/bin/bash
# 服务器端拉取和验证脚本
# 用于确保从GitHub正确拉取文件并验证文件存在

set -e

FILE_PATH="${1:-deploy/fix_and_deploy_frontend_complete.sh}"

echo "========================================"
echo "服务器端 Git 拉取和验证"
echo "========================================"
echo ""

# 1. 检查当前目录
echo "[步骤 1/6] 检查当前目录..."
CURRENT_DIR=$(pwd)
echo "  当前目录: $CURRENT_DIR"

if [[ ! -d ".git" ]]; then
    echo "  ✗ 当前目录不是Git仓库"
    echo "  请切换到项目根目录: cd ~/liaotian"
    exit 1
fi
echo "  ✓ Git仓库确认"

# 2. 检查远程仓库配置
echo ""
echo "[步骤 2/6] 检查远程仓库配置..."
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [[ -z "$REMOTE_URL" ]]; then
    echo "  ✗ 未配置远程仓库"
    exit 1
fi
echo "  远程仓库: $REMOTE_URL"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "  当前分支: $CURRENT_BRANCH"

# 3. 检查是否有未提交的更改
echo ""
echo "[步骤 3/6] 检查工作区状态..."
if [[ -n $(git status --porcelain) ]]; then
    echo "  ⚠ 检测到未提交的更改"
    echo "  建议先保存或提交这些更改"
    read -p "  是否继续? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "  ✓ 工作区干净"
fi

# 4. 拉取最新代码
echo ""
echo "[步骤 4/6] 从GitHub拉取最新代码..."
git fetch origin $CURRENT_BRANCH
if [[ $? -ne 0 ]]; then
    echo "  ✗ 拉取失败"
    exit 1
fi

# 检查是否有新提交
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/$CURRENT_BRANCH)

if [[ "$LOCAL_COMMIT" == "$REMOTE_COMMIT" ]]; then
    echo "  ℹ 本地代码已是最新"
else
    echo "  ✓ 检测到新提交"
    echo "    本地:  $LOCAL_COMMIT"
    echo "    远程: $REMOTE_COMMIT"
    echo ""
    echo "  执行 git pull..."
    git pull origin $CURRENT_BRANCH
    if [[ $? -ne 0 ]]; then
        echo "  ✗ 拉取失败，可能有冲突"
        exit 1
    fi
    echo "  ✓ 拉取成功"
fi

# 5. 验证文件是否存在
echo ""
echo "[步骤 5/6] 验证文件是否存在..."
if [[ -f "$FILE_PATH" ]]; then
    echo "  ✓ 文件存在: $FILE_PATH"
    FILE_SIZE=$(stat -c%s "$FILE_PATH" 2>/dev/null || stat -f%z "$FILE_PATH" 2>/dev/null || echo "unknown")
    echo "  文件大小: $FILE_SIZE 字节"
    
    # 检查文件是否在Git中
    if git ls-files --error-unmatch "$FILE_PATH" &>/dev/null; then
        echo "  ✓ 文件在Git仓库中"
    else
        echo "  ⚠ 文件不在Git仓库中（可能是未跟踪文件）"
    fi
else
    echo "  ✗ 文件不存在: $FILE_PATH"
    echo ""
    echo "  可能的原因:"
    echo "    1. 文件未推送到GitHub"
    echo "    2. 文件路径不正确"
    echo "    3. 文件在不同分支"
    echo ""
    echo "  尝试查找类似文件:"
    find deploy/ -name "*fix*deploy*.sh" 2>/dev/null || echo "    未找到类似文件"
    exit 1
fi

# 6. 检查文件权限
echo ""
echo "[步骤 6/6] 检查文件权限..."
if [[ -x "$FILE_PATH" ]]; then
    echo "  ✓ 文件有执行权限"
else
    echo "  ⚠ 文件没有执行权限，添加执行权限..."
    chmod +x "$FILE_PATH"
    echo "  ✓ 已添加执行权限"
fi

echo ""
echo "========================================"
echo "✓ 验证完成！"
echo "========================================"
echo ""
echo "文件信息:"
echo "  路径: $FILE_PATH"
echo "  大小: $FILE_SIZE 字节"
echo ""
echo "执行文件:"
echo "  bash $FILE_PATH"
