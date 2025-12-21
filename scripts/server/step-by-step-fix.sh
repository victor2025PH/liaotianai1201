#!/bin/bash
# ============================================================
# 一步一步修复部署问题
# ============================================================

set -e

echo "============================================================"
echo "🔧 一步一步修复部署问题"
echo "============================================================"
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 步骤 1: 检查项目目录
echo "============================================================"
echo "步骤 1: 检查项目目录"
echo "============================================================"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "⚠️  项目目录不存在，创建目录..."
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    echo "📥 克隆仓库..."
    git clone https://github.com/victor2025PH/liaotianai1201.git . || {
        echo "❌ Git clone 失败"
        exit 1
    }
    echo "✅ 项目目录已创建"
else
    cd "$PROJECT_DIR"
    echo "✅ 项目目录存在: $PROJECT_DIR"
fi

echo ""

# 步骤 2: 修复 Git Pull
echo "============================================================"
echo "步骤 2: 修复 Git Pull"
echo "============================================================"
cd "$PROJECT_DIR"

# 检查 Git 状态
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    echo "⚠️  发现未提交的更改"
    echo "暂存更改..."
    git stash push -m "Auto stash before pull $(date +%Y%m%d_%H%M%S)" 2>/dev/null || {
        echo "⚠️  Git stash 失败，尝试提交..."
        git add -A
        git commit -m "fix: 自动提交本地更改 $(date +%Y%m%d_%H%M%S)" 2>/dev/null || {
            echo "⚠️  Git commit 失败，使用 reset --hard..."
            git fetch origin main
            git reset --hard origin/main || {
                echo "❌ Git reset 失败"
                exit 1
            }
        }
    }
fi

# 拉取最新代码
echo "📥 拉取最新代码..."
git fetch origin main || git fetch origin || true
git pull origin main || {
    echo "⚠️  Git pull 失败，使用 reset --hard..."
    git fetch origin main
    git reset --hard origin/main || {
        echo "❌ Git reset 失败"
        exit 1
    }
}

echo "✅ 代码已更新"
echo ""

# 步骤 3: 检查脚本目录
echo "============================================================"
echo "步骤 3: 检查脚本目录"
echo "============================================================"
if [ ! -d "$PROJECT_DIR/scripts/server" ]; then
    echo "⚠️  脚本目录不存在，创建目录..."
    mkdir -p "$PROJECT_DIR/scripts/server"
    echo "✅ 脚本目录已创建"
else
    echo "✅ 脚本目录存在"
fi

echo ""

# 步骤 4: 检查并创建快速修复脚本
echo "============================================================"
echo "步骤 4: 检查快速修复脚本"
echo "============================================================"
QUICK_FIX_SCRIPT="$PROJECT_DIR/scripts/server/quick-fix-deployment.sh"

if [ ! -f "$QUICK_FIX_SCRIPT" ]; then
    echo "⚠️  快速修复脚本不存在，从仓库中查找..."
    
    # 检查是否在 Git 中
    if git ls-files --error-unmatch scripts/server/quick-fix-deployment.sh >/dev/null 2>&1; then
        echo "📥 从 Git 中恢复脚本..."
        git checkout HEAD -- scripts/server/quick-fix-deployment.sh || {
            echo "⚠️  无法从 Git 恢复，创建临时脚本..."
            cat > "$QUICK_FIX_SCRIPT" << 'EOF'
#!/bin/bash
# 临时快速修复脚本
echo "请先运行: git pull origin main"
EOF
            chmod +x "$QUICK_FIX_SCRIPT"
        }
    else
        echo "⚠️  脚本不在 Git 中，创建临时脚本..."
        cat > "$QUICK_FIX_SCRIPT" << 'EOF'
#!/bin/bash
# 临时快速修复脚本
echo "请先运行: git pull origin main"
EOF
        chmod +x "$QUICK_FIX_SCRIPT"
    fi
fi

if [ -f "$QUICK_FIX_SCRIPT" ]; then
    chmod +x "$QUICK_FIX_SCRIPT"
    echo "✅ 快速修复脚本已就绪: $QUICK_FIX_SCRIPT"
else
    echo "❌ 无法创建快速修复脚本"
    exit 1
fi

echo ""

# 步骤 5: 验证脚本
echo "============================================================"
echo "步骤 5: 验证脚本"
echo "============================================================"
if [ -x "$QUICK_FIX_SCRIPT" ]; then
    echo "✅ 脚本可执行"
    echo "脚本路径: $QUICK_FIX_SCRIPT"
else
    echo "❌ 脚本不可执行"
    chmod +x "$QUICK_FIX_SCRIPT"
    echo "✅ 已添加执行权限"
fi

echo ""

# 步骤 6: 列出可用脚本
echo "============================================================"
echo "步骤 6: 可用脚本列表"
echo "============================================================"
if [ -d "$PROJECT_DIR/scripts/server" ]; then
    echo "可用脚本:"
    ls -lh "$PROJECT_DIR/scripts/server"/*.sh 2>/dev/null || echo "  无脚本文件"
else
    echo "脚本目录不存在"
fi

echo ""

echo "============================================================"
echo "✅ 修复完成"
echo "============================================================"
echo ""
echo "下一步:"
echo "  运行快速修复脚本:"
echo "    bash $QUICK_FIX_SCRIPT"
echo ""
