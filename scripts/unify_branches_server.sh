#!/bin/bash
# Unify branches on server - Switch to main branch and remove master

set -e

echo "========================================"
echo "统一服务器分支到 main"
echo "========================================"
echo ""

cd ~/liaotian || {
    echo "❌ 无法进入项目目录"
    exit 1
}

# 1. 查看当前状态
echo "=== 1. 查看当前分支状态 ==="
echo "当前分支:"
git branch
echo ""
echo "远程分支:"
git branch -r
echo ""

# 2. 检查是否有未提交的更改
echo "=== 2. 检查工作区状态 ==="
if [[ -n $(git status --porcelain) ]]; then
    echo "⚠️  检测到未提交的更改:"
    git status --short
    echo ""
    read -p "是否保存这些更改? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git stash push -m "统一分支前保存的更改 - $(date '+%Y-%m-%d %H:%M:%S')"
        echo "✅ 更改已保存到 stash"
    else
        echo "⚠️  未保存更改，继续操作可能会丢失"
        read -p "继续? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "✅ 工作区干净"
fi
echo ""

# 3. 获取最新远程信息
echo "=== 3. 获取最新远程信息 ==="
git fetch origin main
echo "✅ 远程信息已更新"
echo ""

# 4. 切换到 main 分支
echo "=== 4. 切换到 main 分支 ==="
if git show-ref --verify --quiet refs/heads/main; then
    echo "本地 main 分支已存在，切换中..."
    git checkout main
else
    echo "本地 main 分支不存在，从远程创建..."
    git checkout -b main origin/main
fi
echo "✅ 已切换到 main 分支"
echo ""

# 5. 设置上游分支
echo "=== 5. 设置上游分支 ==="
git branch --set-upstream-to=origin/main main
echo "✅ 已设置 main 跟踪 origin/main"
echo ""

# 6. 拉取最新代码
echo "=== 6. 拉取最新代码 ==="
git pull origin main
echo "✅ 代码已更新"
echo ""

# 7. 处理 master 分支
echo "=== 7. 处理 master 分支 ==="
if git show-ref --verify --quiet refs/heads/master; then
    echo "检测到本地 master 分支"
    
    # 检查 master 是否有未合并的提交
    MASTER_COMMITS=$(git log main..master --oneline 2>/dev/null | wc -l)
    if [[ $MASTER_COMMITS -gt 0 ]]; then
        echo "⚠️  master 分支有 $MASTER_COMMITS 个未合并的提交"
        git log main..master --oneline
        echo ""
        read -p "是否查看这些提交的详细信息? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git log main..master
        fi
        echo ""
        read -p "是否合并 master 到 main? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git merge master --no-edit
            echo "✅ master 已合并到 main"
        fi
    fi
    
    echo ""
    read -p "是否删除本地 master 分支? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git branch -d master 2>/dev/null || git branch -D master
        echo "✅ 本地 master 分支已删除"
    else
        echo "⚠️  保留 master 分支"
    fi
else
    echo "✅ 本地没有 master 分支"
fi
echo ""

# 8. 验证最终状态
echo "=== 8. 验证最终状态 ==="
echo "当前分支:"
git branch
echo ""
echo "远程配置:"
git remote -v
echo ""
echo "分支同步状态:"
git status
echo ""
echo "最后一次提交:"
git log -1 --oneline
echo ""

# 9. 验证关键文件
echo "=== 9. 验证关键文件 ==="
FILES=(
    "scripts/server_git_check.sh"
    "deploy/fix_and_deploy_frontend_complete.sh"
)

for file in "${FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file 存在"
        if [[ "$file" == *.sh ]]; then
            chmod +x "$file"
            echo "   → 已添加执行权限"
        fi
    else
        echo "❌ $file 不存在"
    fi
done
echo ""

echo "========================================"
echo "✅ 分支统一完成！"
echo "========================================"
echo ""
echo "当前状态:"
echo "  分支: $(git rev-parse --abbrev-ref HEAD)"
echo "  远程: $(git remote get-url origin)"
echo "  状态: $(git status -sb | cut -d' ' -f2-)"
echo ""
echo "下一步:"
echo "  运行部署脚本: bash deploy/fix_and_deploy_frontend_complete.sh"
