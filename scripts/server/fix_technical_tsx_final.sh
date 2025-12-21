#!/bin/bash

# 最终修复 Technical.tsx 中的 JSX 语法错误
# 使用方法: bash scripts/server/fix_technical_tsx_final.sh

set -e

echo "=========================================="
echo "🔧 最终修复 Technical.tsx JSX 语法错误"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"

# 查找所有 Technical.tsx 文件
echo "查找所有 Technical.tsx 文件..."
TECHNICAL_FILES=$(find "$PROJECT_ROOT" -name "Technical.tsx" -type f 2>/dev/null | grep -iE "(hbwy|hongbao)" || echo "")

if [ -z "$TECHNICAL_FILES" ]; then
  echo "❌ 未找到 Technical.tsx 文件"
  exit 1
fi

echo "找到以下文件："
echo "$TECHNICAL_FILES"
echo ""

# 处理每个文件
for TECHNICAL_FILE in $TECHNICAL_FILES; do
  echo "处理文件: $TECHNICAL_FILE"
  
  # 备份文件
  BACKUP_FILE="${TECHNICAL_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
  cp "$TECHNICAL_FILE" "$BACKUP_FILE"
  echo "✅ 已备份: $BACKUP_FILE"
  
  # 显示问题行
  echo ""
  echo "检查问题行..."
  grep -n "&lt;\|require\|emit" "$TECHNICAL_FILE" | head -10 || true
  echo ""
  
  # 修复 HTML 实体
  echo "修复 HTML 实体..."
  # 将 &lt; 替换为 <
  sed -i 's/&lt;/</g' "$TECHNICAL_FILE" 2>/dev/null || true
  # 将 &gt; 替换为 >
  sed -i 's/&gt;/>/g' "$TECHNICAL_FILE" 2>/dev/null || true
  
  # 修复 require 语句 - 移除 span 标签，保留代码
  echo "修复 require 语句..."
  # 模式1: require(<span className="...">code</span>, "message");
  sed -i 's/require(<span[^>]*>\([^<]*\)<\/span>, "\([^"]*\)");/require(`\1`, "\2");/g' "$TECHNICAL_FILE" 2>/dev/null || true
  
  # 模式2: require(<span>code</span>, "message");
  sed -i 's/require(<span>\([^<]*\)<\/span>, "\([^"]*\)");/require(`\1`, "\2");/g' "$TECHNICAL_FILE" 2>/dev/null || true
  
  # 修复 emit 语句
  echo "修复 emit 语句..."
  # 移除 <span>emit</span> 中的 span 标签
  sed -i 's/<span[^>]*>emit<\/span>/emit/g' "$TECHNICAL_FILE" 2>/dev/null || true
  
  # 修复后的内容
  echo ""
  echo "修复后的内容（相关行）："
  grep -n "require\|emit" "$TECHNICAL_FILE" | head -10 || true
  echo ""
  echo "---"
  echo ""
done

echo "=========================================="
echo "✅ 所有 Technical.tsx 文件修复完成"
echo "时间: $(date)"
echo "=========================================="
