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

# 检查 Git 仓库
if [ ! -d ".git" ]; then
    echo "✗ 当前目录不是 Git 仓库"
    echo "  请先克隆仓库: git clone https://github.com/victor2025PH/loaotian1127.git ."
    exit 1
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
BRANCH=$(git branch --show-current 2>/dev/null || echo "master")
echo "  当前分支: $BRANCH"
git pull origin $BRANCH || git pull origin master || git pull origin main

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
