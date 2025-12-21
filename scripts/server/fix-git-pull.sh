#!/bin/bash
# ============================================================
# 修复 Git Pull 问题
# ============================================================

set -e

echo "============================================================"
echo "🔧 修复 Git Pull 问题"
echo "============================================================"
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

cd "$PROJECT_DIR" || {
    echo "❌ 项目目录不存在: $PROJECT_DIR"
    exit 1
}

echo "📊 步骤 1: 检查 Git 状态"
echo "----------------------------------------"
git status --short || {
    echo "❌ Git 状态检查失败"
    exit 1
}

echo ""
echo "📊 步骤 2: 检查未提交的更改"
echo "----------------------------------------"

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  发现未提交的更改，正在处理..."
    
    # 列出未提交的文件
    echo "未提交的文件:"
    git status --short
    
    echo ""
    echo "选项："
    echo "  1. 暂存更改 (stash) - 推荐"
    echo "  2. 提交更改 (commit)"
    echo "  3. 放弃更改 (discard) - 危险"
    echo ""
    read -p "请选择 (1/2/3，默认 1): " choice
    choice=${choice:-1}
    
    case $choice in
        1)
            echo "📦 暂存更改..."
            git stash push -m "Auto stash before pull $(date +%Y%m%d_%H%M%S)" || {
                echo "❌ Git stash 失败"
                exit 1
            }
            echo "✅ 更改已暂存"
            ;;
        2)
            echo "💾 提交更改..."
            git add -A
            git commit -m "fix: 自动提交本地更改 $(date +%Y%m%d_%H%M%S)" || {
                echo "❌ Git commit 失败"
                exit 1
            }
            echo "✅ 更改已提交"
            ;;
        3)
            echo "⚠️  放弃更改..."
            read -p "确认放弃所有未提交的更改？(yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                git reset --hard HEAD || {
                    echo "❌ Git reset 失败"
                    exit 1
                }
                git clean -fd || {
                    echo "❌ Git clean 失败"
                    exit 1
                }
                echo "✅ 更改已放弃"
            else
                echo "❌ 操作已取消"
                exit 1
            fi
            ;;
        *)
            echo "❌ 无效选择"
            exit 1
            ;;
    esac
else
    echo "✅ 没有未提交的更改"
fi

echo ""
echo "📥 步骤 3: 拉取最新代码"
echo "----------------------------------------"

# 获取远程分支信息
git fetch origin main || git fetch origin || {
    echo "⚠️  Git fetch 失败，继续尝试 pull..."
}

# 拉取最新代码
git pull origin main || {
    echo "❌ Git pull 失败"
    echo ""
    echo "尝试使用 reset --hard:"
    read -p "是否使用 'git reset --hard origin/main'？(yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        git fetch origin main
        git reset --hard origin/main || {
            echo "❌ Git reset 失败"
            exit 1
        }
        echo "✅ 代码已重置到远程 main 分支"
    else
        echo "❌ Git pull 失败，请手动处理"
        exit 1
    fi
}

echo "✅ 代码拉取成功"
echo ""

echo "📊 步骤 4: 验证拉取结果"
echo "----------------------------------------"
git log --oneline -5
echo ""

echo "============================================================"
echo "✅ Git Pull 修复完成"
echo "============================================================"
