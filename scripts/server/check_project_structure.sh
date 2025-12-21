#!/bin/bash

echo "=========================================="
echo "🔍 检查项目文件结构"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 网站配置：目录名
declare -a DIRS=(
  "tgmini20251220"
  "hbwy20251220"
  "aizkw20251219"
)

echo "项目根目录: $PROJECT_DIR"
echo ""

# 检查项目根目录
if [ ! -d "$PROJECT_DIR" ]; then
  echo "❌ 项目根目录不存在: $PROJECT_DIR"
  exit 1
fi

cd "$PROJECT_DIR"

# 检查 Git 状态
echo "1️⃣ 检查 Git 状态..."
echo "----------------------------------------"
if [ -d ".git" ]; then
  echo "✅ Git 仓库存在"
  echo "当前分支: $(git branch --show-current 2>/dev/null || echo '未知')"
  echo "最新提交: $(git log -1 --oneline 2>/dev/null || echo '无')"
else
  echo "⚠️  不是 Git 仓库"
fi
echo ""

# 列出根目录内容
echo "2️⃣ 项目根目录内容..."
echo "----------------------------------------"
ls -la | head -20
echo ""

# 检查每个项目目录
for dir in "${DIRS[@]}"; do
  SITE_DIR="$PROJECT_DIR/$dir"
  
  echo "=========================================="
  echo "📁 检查目录: $dir"
  echo "=========================================="
  echo ""
  
  if [ ! -d "$SITE_DIR" ]; then
    echo "❌ 目录不存在: $SITE_DIR"
    echo ""
    continue
  fi
  
  echo "✅ 目录存在"
  echo ""
  
  # 列出目录内容
  echo "目录内容:"
  ls -la "$SITE_DIR" | head -15
  echo ""
  
  # 检查 package.json
  if [ -f "$SITE_DIR/package.json" ]; then
    echo "✅ package.json 存在"
    echo "   文件大小: $(du -h "$SITE_DIR/package.json" | cut -f1)"
  else
    echo "❌ package.json 不存在"
    
    # 搜索 package.json
    echo "   搜索 package.json..."
    FOUND=$(find "$SITE_DIR" -maxdepth 3 -name "package.json" -type f 2>/dev/null)
    if [ -n "$FOUND" ]; then
      echo "   ✅ 找到 package.json 在:"
      echo "$FOUND" | sed 's/^/      /'
    else
      echo "   ❌ 未找到 package.json"
    fi
  fi
  echo ""
  
  # 检查 dist 目录
  if [ -d "$SITE_DIR/dist" ]; then
    FILE_COUNT=$(find "$SITE_DIR/dist" -type f 2>/dev/null | wc -l)
    if [ "$FILE_COUNT" -gt 0 ]; then
      echo "✅ dist 目录存在 ($FILE_COUNT 个文件)"
      echo "   大小: $(du -sh "$SITE_DIR/dist" | cut -f1)"
    else
      echo "⚠️  dist 目录存在但为空"
    fi
  else
    echo "❌ dist 目录不存在"
  fi
  echo ""
  
  # 检查 node_modules
  if [ -d "$SITE_DIR/node_modules" ]; then
    echo "✅ node_modules 存在"
  else
    echo "⚠️  node_modules 不存在（需要运行 npm install）"
  fi
  echo ""
  
  # 检查是否有子目录包含 package.json
  echo "检查子目录结构..."
  find "$SITE_DIR" -maxdepth 2 -type d | head -10 | sed 's/^/   /'
  echo ""
done

echo "=========================================="
echo "✅ 检查完成"
echo "时间: $(date)"
echo "=========================================="
