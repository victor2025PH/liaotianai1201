#!/bin/bash
# ============================================================
# 拉取最新代码并修复 502 错误
# ============================================================

set +e  # 不在第一个错误时退出

echo "=========================================="
echo "📥 拉取最新代码并修复 502 错误"
echo "=========================================="
echo ""

# 检测项目目录
PROJECT_DIR=""
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
elif [ -d "/home/ubuntu/telegram-ai-system" ]; then
  PROJECT_DIR="/home/ubuntu/telegram-ai-system"
elif [ -d "$(pwd)/.git" ]; then
  PROJECT_DIR="$(pwd)"
else
  echo "❌ 未找到项目目录"
  echo "请手动指定项目目录或进入项目目录后执行此脚本"
  exit 1
fi

echo "项目目录: $PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1

# Step 1: 拉取最新代码
echo ""
echo "[1/3] 拉取最新代码..."
git pull origin main || {
  echo "  ⚠️  Git pull 失败，尝试检查网络连接"
  echo "  如果失败，请手动执行: cd $PROJECT_DIR && git pull origin main"
}

# Step 2: 检查修复脚本是否存在
echo ""
echo "[2/3] 检查修复脚本..."
FIX_SCRIPT="$PROJECT_DIR/scripts/server/fix-frontend-502.sh"
if [ -f "$FIX_SCRIPT" ]; then
  echo "  ✅ 找到修复脚本: $FIX_SCRIPT"
  chmod +x "$FIX_SCRIPT"
else
  echo "  ❌ 修复脚本不存在: $FIX_SCRIPT"
  echo "  请检查代码是否已拉取成功"
  exit 1
fi

# Step 3: 执行修复脚本
echo ""
echo "[3/3] 执行修复脚本..."
bash "$FIX_SCRIPT"

echo ""
echo "=========================================="
echo "✅ 完成"
echo "=========================================="

