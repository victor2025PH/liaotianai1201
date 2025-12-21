#!/bin/bash

echo "=========================================="
echo "🔍 查找 package.json 文件位置"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

echo "搜索范围: $PROJECT_DIR"
echo ""

# 查找所有 package.json 文件
echo "1️⃣ 查找所有 package.json 文件..."
echo "----------------------------------------"
find "$PROJECT_DIR" -name "package.json" -type f 2>/dev/null | while read -r file; do
  echo "✅ 找到: $file"
  # 显示文件所在目录的内容
  DIR=$(dirname "$file")
  echo "   目录: $DIR"
  echo "   目录内容:"
  ls -la "$DIR" | head -10 | sed 's/^/      /'
  echo ""
done

echo ""

# 检查预期的项目目录
echo "2️⃣ 检查预期的项目目录..."
echo "----------------------------------------"
EXPECTED_DIRS=(
  "tgmini20251220"
  "hbwy20251220"
  "aizkw20251219"
)

for dir in "${EXPECTED_DIRS[@]}"; do
  FULL_PATH="$PROJECT_DIR/$dir"
  echo "检查: $FULL_PATH"
  
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
      else
        echo "  ❌ 子目录中也没有找到"
      fi
    fi
  else
    echo "  ❌ 目录不存在"
  fi
  echo ""
done

echo ""

# 检查根目录
echo "3️⃣ 检查项目根目录..."
echo "----------------------------------------"
echo "根目录: $PROJECT_DIR"
if [ -f "$PROJECT_DIR/package.json" ]; then
  echo "  ✅ 根目录有 package.json"
  echo "  这可能意味着项目文件直接在根目录，而不是在子目录中"
else
  echo "  ❌ 根目录没有 package.json"
fi

echo ""
echo "根目录内容（前 20 项）:"
ls -la "$PROJECT_DIR" | head -20
echo ""

echo "=========================================="
echo "✅ 查找完成"
echo "时间: $(date)"
echo "=========================================="
