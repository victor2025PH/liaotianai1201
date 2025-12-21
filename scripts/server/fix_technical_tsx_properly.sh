#!/bin/bash

# 正确修复 Technical.tsx 中的 JSX 语法错误
# 使用方法: bash scripts/server/fix_technical_tsx_properly.sh

set -e

echo "=========================================="
echo "🔧 修复 Technical.tsx JSX 语法错误"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"

# 查找 hbwy 项目目录
HBWY_DIR=$(find "$PROJECT_ROOT" -maxdepth 5 -type f -name "package.json" 2>/dev/null | \
  grep -iE "(hbwy|hongbao)" | head -1 | xargs dirname 2>/dev/null || echo "")

if [ -z "$HBWY_DIR" ]; then
  echo "❌ 未找到 hbwy 项目目录"
  exit 1
fi

echo "找到 hbwy 项目目录: $HBWY_DIR"
cd "$HBWY_DIR" || exit 1

# 查找 Technical.tsx 文件
TECHNICAL_FILE=$(find . -name "Technical.tsx" 2>/dev/null | head -1)

if [ -z "$TECHNICAL_FILE" ]; then
  echo "❌ 未找到 Technical.tsx 文件"
  exit 1
fi

echo "找到 Technical.tsx: $TECHNICAL_FILE"

# 备份文件
BACKUP_FILE="${TECHNICAL_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
cp "$TECHNICAL_FILE" "$BACKUP_FILE"
echo "✅ 已备份文件: $BACKUP_FILE"
echo ""

# 显示问题行
echo "检查问题行..."
grep -n "require\|emit" "$TECHNICAL_FILE" | head -10 || true
echo ""

# 使用 sed 进行修复
echo "开始修复..."

# 修复方法：将 JSX 中的代码表达式改为文本显示
# 问题行示例：
# <p className="p1-4">require(<span className="text-yellow-400">!isBot(msg.sender)</span>, "Bot detected"); </p>
# 应该改为：
# <p className="p1-4">require(`!isBot(msg.sender)`, "Bot detected"); </p>

# 或者更好的方法：使用代码块显示

# 创建临时文件
TEMP_FILE="${TECHNICAL_FILE}.tmp"

# 使用 awk 处理文件
awk '
{
  # 修复 require 语句
  # 匹配: require(<span className="text-yellow-400">!isBot(msg.sender)</span>, "Bot detected");
  if (match($0, /require\s*\(\s*<span[^>]*>([^<]+)<\/span>\s*,\s*"([^"]+)"\s*\)\s*;/, arr)) {
    gsub(/require\s*\(\s*<span[^>]*>[^<]+<\/span>\s*,\s*"[^"]+"\s*\)\s*;/, "require(`" arr[1] "`, \"" arr[2] "\");")
  }
  
  # 修复 emit 语句
  # 匹配: <span className="text-blue-400">emit</span> Claimed(msg.sender, amount);
  if (match($0, /<span[^>]*>emit<\/span>\s*Claimed\(([^)]+)\)\s*;/, arr)) {
    gsub(/<span[^>]*>emit<\/span>\s*Claimed\([^)]+\)\s*;/, "emit Claimed(" arr[1] ");")
  }
  
  # 修复其他可能的 require 语句变体
  # 匹配: require(<span className="text-yellow-400">remainingAmount > 0</span>, "Empty");
  if (match($0, /require\s*\(\s*<span[^>]*>([^<]+)<\/span>\s*,\s*"([^"]+)"\s*\)\s*;/, arr)) {
    gsub(/require\s*\(\s*<span[^>]*>[^<]+<\/span>\s*,\s*"[^"]+"\s*\)\s*;/, "require(`" arr[1] "`, \"" arr[2] "\");")
  }
  
  print
}
' "$TECHNICAL_FILE" > "$TEMP_FILE"

# 如果 awk 方法不行，使用更简单的方法
if ! diff -q "$TECHNICAL_FILE" "$TEMP_FILE" >/dev/null 2>&1; then
  mv "$TEMP_FILE" "$TECHNICAL_FILE"
  echo "✅ 使用 awk 修复完成"
else
  rm -f "$TEMP_FILE"
  
  # 使用 sed 进行简单修复
  echo "尝试使用 sed 修复..."
  
  # 修复 require 语句 - 方法1：移除 span 标签
  sed -i 's/require(<span[^>]*>\([^<]*\)<\/span>, "\([^"]*\)");/require(`\1`, "\2");/g' "$TECHNICAL_FILE" 2>/dev/null || true
  
  # 修复 emit 语句
  sed -i 's/<span[^>]*>emit<\/span> Claimed/emit Claimed/g' "$TECHNICAL_FILE" 2>/dev/null || true
  
  # 修复 require 语句 - 方法2：处理 &lt; 实体
  sed -i 's/require(&lt;span[^>]*>\([^<]*\)&lt;\/span>, "\([^"]*\)");/require(`\1`, "\2");/g' "$TECHNICAL_FILE" 2>/dev/null || true
  
  echo "✅ 使用 sed 修复完成"
fi

echo ""
echo "修复后的文件内容（相关行）："
grep -n "require\|emit" "$TECHNICAL_FILE" | head -10 || true

echo ""
echo "=========================================="
echo "✅ JSX 语法错误修复完成"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "现在可以重新构建项目："
echo "cd $HBWY_DIR"
echo "npm run build"
