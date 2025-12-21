#!/bin/bash

set -e

echo "=========================================="
echo "🔧 修复项目结构"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 确保以 root 权限运行
if [ "$EUID" -ne 0 ]; then
  echo "⚠️  此脚本需要 sudo 权限，请使用: sudo bash $0"
  exit 1
fi

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"

echo "项目根目录: $PROJECT_ROOT"
echo ""

# 步骤 1: 检查并修复 Git 状态
echo "1️⃣ 检查 Git 状态..."
echo "----------------------------------------"
if [ -d "$PROJECT_ROOT/.git" ]; then
  cd "$PROJECT_ROOT"
  echo "当前目录: $(pwd)"
  
  # 检查是否有本地修改
  if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    echo "⚠️  发现本地修改，保存到 stash..."
    git stash || true
  fi
  
  # 拉取最新代码
  echo "拉取最新代码..."
  git fetch origin main || git fetch origin || true
  git reset --hard origin/main || {
    echo "⚠️  git reset 失败，尝试 git pull..."
    git pull origin main || {
      echo "⚠️  Git pull 失败，但继续执行..."
    }
  }
  
  echo "✅ Git 状态已修复"
else
  echo "⚠️  不是 Git 仓库，初始化..."
  mkdir -p "$PROJECT_ROOT"
  cd "$PROJECT_ROOT"
  git init || true
  git remote add origin https://github.com/victor2025PH/liaotianai1201.git || true
  git fetch origin main || true
  git reset --hard origin/main || true
  echo "✅ Git 仓库已初始化"
fi
echo ""

# 步骤 2: 查找所有 package.json 文件
echo "2️⃣ 查找 package.json 文件..."
echo "----------------------------------------"
find "$PROJECT_ROOT" -name "package.json" -type f 2>/dev/null | while read -r file; do
  echo "✅ 找到: $file"
  DIR=$(dirname "$file")
  echo "   目录: $DIR"
  echo "   相对路径: ${DIR#$PROJECT_ROOT/}"
done
echo ""

# 步骤 3: 检查预期的项目目录
echo "3️⃣ 检查预期的项目目录..."
echo "----------------------------------------"
EXPECTED_DIRS=(
  "tgmini20251220"
  "hbwy20251220"
  "aizkw20251219"
)

for dir in "${EXPECTED_DIRS[@]}"; do
  FULL_PATH="$PROJECT_ROOT/$dir"
  echo "检查: $dir"
  
  if [ -d "$FULL_PATH" ]; then
    echo "  ✅ 目录存在"
    
    # 检查 package.json
    if [ -f "$FULL_PATH/package.json" ]; then
      echo "  ✅ package.json 存在"
    else
      echo "  ❌ package.json 不存在"
      
      # 在子目录中搜索
      FOUND=$(find "$FULL_PATH" -maxdepth 3 -name "package.json" -type f 2>/dev/null | head -1)
      if [ -n "$FOUND" ]; then
        echo "  ✅ 在子目录中找到: $FOUND"
        echo "     建议移动文件到: $FULL_PATH/package.json"
      else
        echo "  ❌ 子目录中也没有找到"
        echo "     需要上传文件到: $FULL_PATH"
      fi
    fi
  else
    echo "  ❌ 目录不存在"
    echo "     创建目录..."
    mkdir -p "$FULL_PATH"
    echo "  ✅ 目录已创建: $FULL_PATH"
  fi
  echo ""
done

# 步骤 4: 检查是否有文件在根目录
echo "4️⃣ 检查根目录中的项目文件..."
echo "----------------------------------------"
ROOT_PACKAGE="$PROJECT_ROOT/package.json"
if [ -f "$ROOT_PACKAGE" ]; then
  echo "⚠️  根目录有 package.json"
  echo "   这可能是主仓库的 package.json，不是前端项目的"
  echo "   前端项目的 package.json 应该在子目录中"
else
  echo "✅ 根目录没有 package.json（正常）"
fi
echo ""

# 步骤 5: 列出根目录内容
echo "5️⃣ 项目根目录内容..."
echo "----------------------------------------"
ls -la "$PROJECT_ROOT" | head -30
echo ""

echo "=========================================="
echo "✅ 检查完成"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "如果 package.json 文件在错误的位置，请："
echo "1. 使用 WinSCP 或 scp 上传文件到正确的子目录"
echo "2. 或者运行构建脚本，它会自动查找文件位置"
echo "3. 运行: sudo bash scripts/server/build_and_start_all.sh"
