#!/bin/bash
# 查找项目实际路径

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"

echo "=========================================="
echo "🔍 查找项目实际路径"
echo "=========================================="
echo ""

echo "查找所有 package.json 文件（排除 node_modules）:"
echo "----------------------------------------"
find "$PROJECT_ROOT" -name "package.json" -not -path "*/node_modules/*" 2>/dev/null | while read -r file; do
    dir=$(dirname "$file")
    rel_dir=${dir#$PROJECT_ROOT/}
    echo "  ✅ $rel_dir"
    echo "     完整路径: $dir"
    echo ""
done

echo ""
echo "检查预期路径:"
echo "----------------------------------------"

# 检查 hongbao
echo "hongbao (hbwy20251220):"
if [ -f "$PROJECT_ROOT/hbwy20251220/package.json" ]; then
    echo "  ✅ 找到: hbwy20251220/package.json"
elif [ -f "$PROJECT_ROOT/react-vite-template/hbwy20251220/package.json" ]; then
    echo "  ✅ 找到: react-vite-template/hbwy20251220/package.json"
else
    echo "  ❌ 未找到标准路径，搜索中..."
    found=$(find "$PROJECT_ROOT" -maxdepth 5 -name "package.json" -not -path "*/node_modules/*" 2>/dev/null | grep -iE "(hbwy|hongbao)" | head -1)
    if [ -n "$found" ]; then
        echo "  ✅ 找到: $found"
    else
        echo "  ❌ 未找到"
    fi
fi

echo ""

# 检查 aizkw
echo "aizkw (aizkw20251219):"
if [ -f "$PROJECT_ROOT/aizkw20251219/package.json" ]; then
    echo "  ✅ 找到: aizkw20251219/package.json"
elif [ -f "$PROJECT_ROOT/migrations/aizkw20251219/package.json" ]; then
    echo "  ✅ 找到: migrations/aizkw20251219/package.json"
else
    echo "  ❌ 未找到标准路径，搜索中..."
    found=$(find "$PROJECT_ROOT" -maxdepth 5 -name "package.json" -not -path "*/node_modules/*" 2>/dev/null | grep -iE "aizkw" | head -1)
    if [ -n "$found" ]; then
        echo "  ✅ 找到: $found"
    else
        echo "  ❌ 未找到"
    fi
fi

echo ""

