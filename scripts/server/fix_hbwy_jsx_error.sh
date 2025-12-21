#!/bin/bash

# 修复 hbwy 项目的 JSX 语法错误
# 使用方法: bash scripts/server/fix_hbwy_jsx_error.sh

set -e

echo "=========================================="
echo "🔧 修复 hbwy 项目 JSX 语法错误"
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
  echo "⚠️  未找到 Technical.tsx 文件"
  exit 1
fi

echo "找到 Technical.tsx: $TECHNICAL_FILE"

# 备份文件
cp "$TECHNICAL_FILE" "$TECHNICAL_FILE.bak"
echo "✅ 已备份文件: $TECHNICAL_FILE.bak"

# 读取文件内容
echo ""
echo "检查文件内容..."
grep -n "require\|emit" "$TECHNICAL_FILE" | head -10 || true

echo ""
echo "修复 JSX 语法错误..."

# 修复方法1：将 JSX 中的代码块用反引号包裹
# 查找包含 require(<span 的行
if grep -q 'require(<span' "$TECHNICAL_FILE" 2>/dev/null; then
  echo "修复 require 语句..."
  # 使用 sed 将 require(<span 改为 require(`<span 或使用代码块
  sed -i 's/require(<span className="text-yellow-400">!isBot(msg.sender)<\/span>, "Bot detected");/require(`!isBot(msg.sender)`, "Bot detected");/g' "$TECHNICAL_FILE" 2>/dev/null || true
fi

# 查找包含 emit Claimed 的行
if grep -q 'emit Claimed' "$TECHNICAL_FILE" 2>/dev/null; then
  echo "修复 emit 语句..."
  # 修复 emit 语句
  sed -i 's/<span className="text-blue-400">emit<\/span> Claimed(msg.sender, amount);/emit Claimed(msg.sender, amount);/g' "$TECHNICAL_FILE" 2>/dev/null || true
fi

# 更通用的修复：将 JSX 中的代码表达式改为文本显示
# 如果上述方法不行，使用更保守的方法
echo ""
echo "应用通用修复..."

# 读取文件并修复
python3 << 'PYTHON_SCRIPT'
import re
import sys

file_path = sys.argv[1]

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 修复 require 语句：将 JSX 中的代码改为文本显示
    # 从: require(<span className="text-yellow-400">!isBot(msg.sender)</span>, "Bot detected");
    # 到: require(`!isBot(msg.sender)`, "Bot detected");
    pattern1 = r'require\s*\(\s*<span[^>]*>([^<]+)</span>\s*,\s*"([^"]+)"\s*\);'
    replacement1 = r'require(`\1`, "\2");'
    content = re.sub(pattern1, replacement1, content)
    
    # 修复 emit 语句：移除 JSX 标签，保留代码
    # 从: <span className="text-blue-400">emit</span> Claimed(msg.sender, amount);
    # 到: emit Claimed(msg.sender, amount);
    pattern2 = r'<span[^>]*>emit</span>\s*Claimed\(([^)]+)\);'
    replacement2 = r'emit Claimed(\1);'
    content = re.sub(pattern2, replacement2, content)
    
    # 如果内容有变化，保存
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ 文件已修复")
    else:
        print("⚠️  未发现需要修复的内容")
        
except Exception as e:
    print(f"❌ 修复失败: {e}")
    sys.exit(1)
PYTHON_SCRIPT
"$TECHNICAL_FILE"

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
