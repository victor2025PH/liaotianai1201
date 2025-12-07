#!/bin/bash
# One-click deployment and verification
# Unified workflow for local → GitHub → Server

set -e

echo "========================================"
echo "一条龙部署验证流程"
echo "========================================"
echo ""

cd ~/liaotian || {
    echo "❌ 无法进入项目目录"
    exit 1
}

# Step 1: Ensure on main branch
echo "=== 步骤 1: 确保在 main 分支 ==="
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo "⚠️  当前分支是 $CURRENT_BRANCH，切换到 main..."
    git checkout main 2>/dev/null || git checkout -b main origin/main
    echo "✅ 已切换到 main 分支"
else
    echo "✅ 当前在 main 分支"
fi
echo ""

# Step 2: Fetch and pull latest code
echo "=== 步骤 2: 获取并拉取最新代码 ==="
git fetch origin main
echo "✅ 远程信息已获取"

# Check if there are new commits
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/main)

if [[ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]]; then
    echo "检测到新提交，拉取中..."
    git pull origin main
    echo "✅ 代码已更新"
    echo "新提交:"
    git log $LOCAL_COMMIT..$REMOTE_COMMIT --oneline
else
    echo "✅ 本地代码已是最新"
fi
echo ""

# Step 3: Verify branch sync
echo "=== 步骤 3: 验证分支同步 ==="
git status
echo ""

# Step 4: Verify critical files
echo "=== 步骤 4: 验证关键文件 ==="
FILES=(
    "scripts/server_git_check.sh"
    "deploy/fix_and_deploy_frontend_complete.sh"
)

MISSING_FILES=0
for file in "${FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file"
        if [[ "$file" == *.sh ]]; then
            chmod +x "$file" 2>/dev/null || true
        fi
    else
        echo "❌ $file 缺失"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [[ $MISSING_FILES -gt 0 ]]; then
    echo ""
    echo "⚠️  有 $MISSING_FILES 个文件缺失"
    echo "尝试从远程检出..."
    for file in "${FILES[@]}"; do
        if [[ ! -f "$file" ]]; then
            git checkout origin/main -- "$file" 2>/dev/null && {
                echo "✅ 已检出: $file"
                chmod +x "$file" 2>/dev/null || true
            } || echo "❌ 无法检出: $file"
        fi
    done
fi
echo ""

# Step 5: Show current state
echo "=== 步骤 5: 当前状态 ==="
echo "分支: $(git rev-parse --abbrev-ref HEAD)"
echo "提交: $(git log -1 --oneline)"
echo "远程: $(git remote get-url origin)"
echo ""

# Step 6: Deployment option
echo "=== 步骤 6: 部署选项 ==="
if [[ -f "deploy/fix_and_deploy_frontend_complete.sh" ]]; then
    read -p "是否立即执行部署? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "开始部署..."
        echo "========================================"
        bash deploy/fix_and_deploy_frontend_complete.sh
    else
        echo ""
        echo "跳过部署。可以稍后运行:"
        echo "  bash deploy/fix_and_deploy_frontend_complete.sh"
    fi
else
    echo "⚠️  部署脚本不存在，跳过自动部署"
fi

echo ""
echo "========================================"
echo "✅ 一条龙流程完成！"
echo "========================================"
