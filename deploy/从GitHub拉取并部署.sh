#!/bin/bash
# 从 GitHub 拉取最新代码并部署
# 使用方法: bash ~/liaotian/deploy/从GitHub拉取并部署.sh

set -e

echo "========================================="
echo "从 GitHub 拉取最新代码并部署"
echo "开始时间: $(date)"
echo "========================================="
echo ""

cd ~/liaotian

# 加载仓库配置
if [ -f "deploy/repo_config.sh" ]; then
    source deploy/repo_config.sh
elif [ -f "$(dirname "$0")/repo_config.sh" ]; then
    source "$(dirname "$0")/repo_config.sh"
else
    # 默认配置
    GITHUB_REPO_URL="https://github.com/victor2025PH/liaotianai1201.git"
    DEFAULT_BRANCH="main"
fi

# 检查 Git 仓库
if [ ! -d ".git" ]; then
    echo "✗ 当前目录不是 Git 仓库"
    echo "  请先克隆仓库: git clone ${GITHUB_REPO_URL} ."
    exit 1
fi

# 检查并更新远程仓库地址（如果配置了）
if [ -n "$GITHUB_REPO_URL" ]; then
    CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
    if [ "$CURRENT_REMOTE" != "$GITHUB_REPO_URL" ]; then
        echo "  更新远程仓库地址..."
        git remote set-url origin "$GITHUB_REPO_URL" 2>/dev/null || git remote add origin "$GITHUB_REPO_URL"
        echo "  ✓ 远程仓库已更新: $GITHUB_REPO_URL"
    fi
fi

# 1. 备份当前代码
echo "【步骤1】备份当前代码..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p ~/backups/$BACKUP_DIR
if [ -f "admin-backend/app/api/group_ai/accounts.py" ]; then
    cp admin-backend/app/api/group_ai/accounts.py ~/backups/$BACKUP_DIR/accounts.py 2>/dev/null || true
    echo "  ✓ 备份 accounts.py"
fi
echo ""

# 2. 从 GitHub 拉取最新代码
echo "【步骤2】从 GitHub 拉取最新代码..."
git fetch --all

# 检查本地修改
echo "  检查本地修改..."
LOCAL_CHANGES=$(git status --porcelain)
if [ -n "$LOCAL_CHANGES" ]; then
    echo "  ⚠ 发现本地修改，正在备份..."
    STASH_NAME="服務器本地修改備份-$(date +%Y%m%d_%H%M%S)"
    git stash save "$STASH_NAME"
    echo "  ✓ 本地修改已備份到 stash"
fi

# 智能分支检测
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")
echo "  当前分支: ${CURRENT_BRANCH:-未设置}"

# 获取远程分支列表
REMOTE_BRANCHES=$(git ls-remote --heads origin 2>/dev/null | sed 's/.*refs\/heads\///' || echo "")

# 确定要拉取的分支
TARGET_BRANCH=""
if echo "$REMOTE_BRANCHES" | grep -q "^main$"; then
    TARGET_BRANCH="main"
    echo "  ✓ 使用 main 分支"
elif echo "$REMOTE_BRANCHES" | grep -q "^master$"; then
    TARGET_BRANCH="master"
    echo "  ✓ 使用 master 分支"
elif [ -n "$REMOTE_BRANCHES" ]; then
    TARGET_BRANCH=$(echo "$REMOTE_BRANCHES" | head -1)
    echo "  ✓ 使用第一个可用分支: $TARGET_BRANCH"
else
    TARGET_BRANCH="${DEFAULT_BRANCH:-main}"
    echo "  ⚠ 未检测到远程分支，使用默认分支: $TARGET_BRANCH"
fi

# 切换到目标分支（如果需要）
if [ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ]; then
    echo "  切换到目标分支: $TARGET_BRANCH"
    if git branch | grep -q "^\s*$TARGET_BRANCH$"; then
        git checkout "$TARGET_BRANCH"
    else
        git checkout -b "$TARGET_BRANCH" "origin/$TARGET_BRANCH" 2>/dev/null || {
            echo "  ⚠ 无法从远程创建分支，尝试其他方法..."
            git checkout -b "$TARGET_BRANCH"
            git branch --set-upstream-to="origin/$TARGET_BRANCH" "$TARGET_BRANCH" || true
        }
    fi
    echo "  ✓ 已切换到分支: $TARGET_BRANCH"
fi

# 拉取代码
echo "  正在拉取分支: $TARGET_BRANCH"
git pull origin "$TARGET_BRANCH" || {
    echo "  ⚠ 拉取 $TARGET_BRANCH 失败，尝试其他分支..."
    for BRANCH in main master develop; do
        if echo "$REMOTE_BRANCHES" | grep -q "^$BRANCH$"; then
            echo "  尝试切换到: $BRANCH"
            git checkout -b "$BRANCH" "origin/$BRANCH" 2>/dev/null || git checkout "$BRANCH"
            echo "  尝试拉取: $BRANCH"
            git pull origin "$BRANCH" && break
        fi
    done
}

# 2.1 修复拉取的脚本文件的行尾符（如果存在）
if [ -f "deploy/从GitHub拉取并部署.sh" ]; then
    echo "  转换脚本行尾符为 Unix 格式..."
    sed -i 's/\r$//' deploy/从GitHub拉取并部署.sh 2>/dev/null || sed -i '' 's/\r$//' deploy/从GitHub拉取并部署.sh 2>/dev/null || true
    chmod +x deploy/从GitHub拉取并部署.sh 2>/dev/null || true
fi

if [ $? -eq 0 ]; then
    echo "  ✓ 代码拉取完成"
    echo ""
    echo "  最近的提交:"
    git log --oneline -3 | head -3
else
    echo "  ✗ 代码拉取失败"
    exit 1
fi
echo ""

# 3. 验证关键文件
echo "【步骤3】验证关键文件..."
if [ -f "admin-backend/app/api/group_ai/accounts.py" ]; then
    UPSERT_COUNT=$(grep -c "UPSERT" admin-backend/app/api/group_ai/accounts.py 2>/dev/null || echo "0")
    echo "  ✓ accounts.py 存在（包含 $UPSERT_COUNT 处 UPSERT）"
else
    echo "  ✗ accounts.py 不存在"
fi
echo ""

# 4. 重启后端服务
echo "【步骤4】重启后端服务..."
cd ~/liaotian/admin-backend

if [ ! -d ".venv" ]; then
    echo "  ⚠ 虚拟环境不存在，正在创建..."
    python3 -m venv .venv
fi

source .venv/bin/activate 2>/dev/null || true

echo "  停止旧服务..."
pkill -9 -f 'uvicorn.*app.main:app' || true
pkill -9 -f 'python.*uvicorn.*app.main' || true
sleep 3

echo "  清理 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "  启动新服务..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "  后端进程 PID: $BACKEND_PID"

echo "  等待服务启动（最多30秒）..."
STARTED=0
for i in {1..15}; do
    sleep 2
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✓ 后端服务已启动（等待了 $((i*2)) 秒）"
        STARTED=1
        break
    fi
done

if [ $STARTED -eq 0 ]; then
    echo "  ⚠ 服务启动超时，查看日志..."
    tail -30 /tmp/backend.log
fi
echo ""

# 5. 验证服务
echo "【步骤5】验证服务..."
if curl -s http://localhost:8000/health | grep -q "ok" 2>/dev/null; then
    echo "  ✓ 后端服务正常运行"
    
    # 显示健康检查响应
    echo ""
    echo "  健康检查响应:"
    curl -s http://localhost:8000/health | head -3
else
    echo "  ✗ 后端服务未正常响应"
    echo "  查看日志:"
    tail -50 /tmp/backend.log | grep -E "ERROR|Exception|Traceback" | tail -10
    exit 1
fi
echo ""

echo "========================================="
echo "部署完成！"
echo "完成时间: $(date)"
echo "========================================="
echo ""
echo "备份位置: ~/backups/$BACKUP_DIR"
echo "后端日志: /tmp/backend.log"
echo ""
