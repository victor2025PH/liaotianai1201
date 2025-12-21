#!/bin/bash

# 在本地修复 Technical.tsx 文件并提交到 Git
# 使用方法: bash scripts/local/fix_technical_tsx_local.sh

set -e

echo "=========================================="
echo "🔧 本地修复 Technical.tsx 并提交到 Git"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

# 查找所有 Technical.tsx 文件
echo "查找所有 Technical.tsx 文件..."
TECHNICAL_FILES=$(find . -name "Technical.tsx" -type f 2>/dev/null | grep -iE "(hbwy|hongbao)" || echo "")

if [ -z "$TECHNICAL_FILES" ]; then
  echo "❌ 未找到 Technical.tsx 文件"
  exit 1
fi

echo "找到以下文件："
echo "$TECHNICAL_FILES"
echo ""

# 处理每个文件
FILES_MODIFIED=0
for TECHNICAL_FILE in $TECHNICAL_FILES; do
  echo "处理文件: $TECHNICAL_FILE"
  
  # 检查文件是否在 Git 中
  if ! git ls-files --error-unmatch "$TECHNICAL_FILE" >/dev/null 2>&1; then
    echo "  ⚠️  文件不在 Git 中，跳过"
    continue
  fi
  
  # 备份文件
  BACKUP_FILE="${TECHNICAL_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
  cp "$TECHNICAL_FILE" "$BACKUP_FILE"
  echo "  ✅ 已备份: $BACKUP_FILE"
  
  # 显示问题行
  echo ""
  echo "  检查问题行..."
  grep -n "&lt;\|require\|emit" "$TECHNICAL_FILE" | head -5 || true
  echo ""
  
  # 修复 HTML 实体
  echo "  修复 HTML 实体..."
  # 将 &lt; 替换为 <
  sed -i '' 's/&lt;/</g' "$TECHNICAL_FILE" 2>/dev/null || sed -i 's/&lt;/</g' "$TECHNICAL_FILE" 2>/dev/null || true
  # 将 &gt; 替换为 >
  sed -i '' 's/&gt;/>/g' "$TECHNICAL_FILE" 2>/dev/null || sed -i 's/&gt;/>/g' "$TECHNICAL_FILE" 2>/dev/null || true
  
  # 修复 require 语句 - 移除 span 标签，保留代码
  echo "  修复 require 语句..."
  # 模式1: require(<span className="...">code</span>, "message");
  sed -i '' 's/require(<span[^>]*>\([^<]*\)<\/span>, "\([^"]*\)");/require(`\1`, "\2");/g' "$TECHNICAL_FILE" 2>/dev/null || \
  sed -i 's/require(<span[^>]*>\([^<]*\)<\/span>, "\([^"]*\)");/require(`\1`, "\2");/g' "$TECHNICAL_FILE" 2>/dev/null || true
  
  # 模式2: require(<span>code</span>, "message");
  sed -i '' 's/require(<span>\([^<]*\)<\/span>, "\([^"]*\)");/require(`\1`, "\2");/g' "$TECHNICAL_FILE" 2>/dev/null || \
  sed -i 's/require(<span>\([^<]*\)<\/span>, "\([^"]*\)");/require(`\1`, "\2");/g' "$TECHNICAL_FILE" 2>/dev/null || true
  
  # 修复 emit 语句
  echo "  修复 emit 语句..."
  # 移除 <span>emit</span> 中的 span 标签
  sed -i '' 's/<span[^>]*>emit<\/span>/emit/g' "$TECHNICAL_FILE" 2>/dev/null || \
  sed -i 's/<span[^>]*>emit<\/span>/emit/g' "$TECHNICAL_FILE" 2>/dev/null || true
  
  # 检查是否有修改
  if ! git diff --quiet "$TECHNICAL_FILE"; then
    echo "  ✅ 文件已修改"
    FILES_MODIFIED=$((FILES_MODIFIED + 1))
    
    echo ""
    echo "  修复后的内容（相关行）："
    grep -n "require\|emit" "$TECHNICAL_FILE" | head -5 || true
  else
    echo "  ℹ️  文件无需修改"
  fi
  
  echo ""
  echo "  ---"
  echo ""
done

if [ $FILES_MODIFIED -eq 0 ]; then
  echo "✅ 所有文件都无需修改"
  exit 0
fi

# 显示修改摘要
echo "=========================================="
echo "📊 修改摘要"
echo "=========================================="
git status --short | grep Technical.tsx || true
echo ""

# 询问是否提交
read -p "是否提交这些修改到 Git? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo ""
  echo "提交修改..."
  git add $(echo "$TECHNICAL_FILES" | tr '\n' ' ')
  git commit -m "fix: 修复 Technical.tsx 中的 JSX 语法错误

- 修复 HTML 实体（&lt; -> <）
- 修复 require 语句中的 span 标签
- 修复 emit 语句中的 span 标签" || {
    echo "❌ 提交失败"
    exit 1
  }
  
  echo ""
  echo "✅ 修改已提交到本地 Git"
  echo ""
  read -p "是否推送到远程仓库? (y/n): " -n 1 -r
  echo ""
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin main || {
      echo "❌ 推送失败"
      exit 1
    }
    echo "✅ 修改已推送到远程仓库"
  else
    echo "ℹ️  修改已提交到本地，但未推送。请稍后运行: git push origin main"
  fi
else
  echo "ℹ️  修改已保存，但未提交。请手动检查后提交。"
fi

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 在服务器上运行: git pull origin main"
echo "2. 重新构建项目: cd <project-dir> && npm run build"
echo "3. 重启服务: pm2 restart <service-name>"
