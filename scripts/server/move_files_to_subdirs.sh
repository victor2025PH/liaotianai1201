#!/bin/bash

set -e

echo "=========================================="
echo "📁 检查并整理项目文件到子目录"
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

cd "$PROJECT_ROOT"

# 检查根目录中是否有项目文件
echo "1️⃣ 检查根目录中的项目文件..."
echo "----------------------------------------"

# 查找根目录中的 package.json（排除 node_modules 和已知的子目录）
ROOT_PACKAGE_JSON=$(find . -maxdepth 1 -name "package.json" -type f 2>/dev/null | grep -v node_modules | head -1)

if [ -n "$ROOT_PACKAGE_JSON" ]; then
  echo "⚠️  在根目录找到 package.json: $ROOT_PACKAGE_JSON"
  echo "   这可能是前端项目的文件，需要移动到子目录"
  
  # 检查 package.json 的内容，判断是哪个项目
  if grep -q "tgmini\|ton-mini" "$ROOT_PACKAGE_JSON" 2>/dev/null; then
    TARGET_DIR="tgmini20251220"
    echo "   检测到可能是 tgmini 项目"
  elif grep -q "hongbao\|hbwy" "$ROOT_PACKAGE_JSON" 2>/dev/null; then
    TARGET_DIR="hbwy20251220"
    echo "   检测到可能是 hongbao 项目"
  elif grep -q "aizkw\|aikz" "$ROOT_PACKAGE_JSON" 2>/dev/null; then
    TARGET_DIR="aizkw20251219"
    echo "   检测到可能是 aizkw 项目"
  else
    echo "   无法确定项目类型，需要手动处理"
    TARGET_DIR=""
  fi
  
  if [ -n "$TARGET_DIR" ]; then
    TARGET_PATH="$PROJECT_ROOT/$TARGET_DIR"
    echo ""
    echo "   建议移动到: $TARGET_PATH"
    echo "   是否自动移动？(y/n)"
    read -r response
    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
      mkdir -p "$TARGET_PATH"
      echo "   移动文件到 $TARGET_PATH..."
      # 移动 package.json 和相关的项目文件
      mv "$ROOT_PACKAGE_JSON" "$TARGET_PATH/" 2>/dev/null || true
      echo "   ✅ 已移动 package.json"
    fi
  fi
else
  echo "✅ 根目录没有 package.json（正常）"
fi
echo ""

# 检查每个子目录
echo "2️⃣ 检查子目录内容..."
echo "----------------------------------------"
SITES=(
  "tgmini20251220"
  "hbwy20251220"
  "aizkw20251219"
)

for site_dir in "${SITES[@]}"; do
  FULL_PATH="$PROJECT_ROOT/$site_dir"
  
  echo "检查: $site_dir"
  if [ -d "$FULL_PATH" ]; then
    FILE_COUNT=$(find "$FULL_PATH" -type f 2>/dev/null | wc -l)
    DIR_COUNT=$(find "$FULL_PATH" -mindepth 1 -type d 2>/dev/null | wc -l)
    
    echo "  文件数量: $FILE_COUNT"
    echo "  子目录数量: $DIR_COUNT"
    
    if [ "$FILE_COUNT" -eq 0 ] && [ "$DIR_COUNT" -eq 0 ]; then
      echo "  ⚠️  目录为空"
    else
      echo "  目录内容（前 10 项）:"
      ls -la "$FULL_PATH" | head -11 | sed 's/^/    /'
    fi
    
    # 检查 package.json
    if [ -f "$FULL_PATH/package.json" ]; then
      echo "  ✅ package.json 存在"
    else
      echo "  ❌ package.json 不存在"
    fi
  else
    echo "  ❌ 目录不存在"
  fi
  echo ""
done

# 查找所有 package.json 文件
echo "3️⃣ 查找所有 package.json 文件..."
echo "----------------------------------------"
find "$PROJECT_ROOT" -name "package.json" -type f 2>/dev/null | while read -r file; do
  echo "找到: $file"
  DIR=$(dirname "$file")
  RELATIVE_DIR="${DIR#$PROJECT_ROOT/}"
  echo "  相对路径: $RELATIVE_DIR"
  
  # 检查是否在预期的子目录中
  if [[ "$RELATIVE_DIR" == "tgmini20251220"* ]] || \
     [[ "$RELATIVE_DIR" == "hbwy20251220"* ]] || \
     [[ "$RELATIVE_DIR" == "aizkw20251219"* ]]; then
    echo "  ✅ 在预期的子目录中"
  else
    echo "  ⚠️  不在预期的子目录中"
    echo "     建议移动到对应的子目录"
  fi
  echo ""
done

echo "=========================================="
echo "✅ 检查完成"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "如果文件在错误的位置，请："
echo "1. 使用 WinSCP 上传文件到正确的子目录"
echo "2. 或者运行构建脚本，它会自动查找文件位置"
echo "3. 运行: sudo bash scripts/server/build_and_start_all.sh"
