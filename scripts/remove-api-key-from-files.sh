#!/bin/bash
# ============================================================
# 从文件中移除硬编码的 OpenAI API Key
# ============================================================
# 功能：替换所有文件中的实际 API Key 为占位符
# 使用方法：bash scripts/remove-api-key-from-files.sh
# ============================================================

set -e

echo "============================================================"
echo "🔧 从文件中移除硬编码的 OpenAI API Key"
echo "============================================================"
echo ""

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# 要替换的 API Key
OLD_API_KEY="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"
NEW_PLACEHOLDER="YOUR_OPENAI_API_KEY"

# 要处理的文件列表
FILES=(
    "AI_ROBOT_SETUP.md"
    "docs/IMMEDIATE_FIX_STEPS.md"
    "scripts/fix-openai-api-key-in-history.sh"
)

FIXED_COUNT=0

for FILE in "${FILES[@]}"; do
    FILE_PATH="$REPO_ROOT/$FILE"
    
    if [ ! -f "$FILE_PATH" ]; then
        echo "⚠️  文件不存在: $FILE"
        continue
    fi
    
    echo "处理: $FILE"
    
    # 检查是否包含 API Key
    if grep -q "$OLD_API_KEY" "$FILE_PATH" 2>/dev/null; then
        echo "  ❌ 发现硬编码的 API Key"
        
        # 备份文件
        cp "$FILE_PATH" "${FILE_PATH}.backup"
        
        # 替换 API Key
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s|$OLD_API_KEY|$NEW_PLACEHOLDER|g" "$FILE_PATH"
        else
            # Linux
            sed -i "s|$OLD_API_KEY|$NEW_PLACEHOLDER|g" "$FILE_PATH"
        fi
        
        echo "  ✅ 已替换为占位符"
        FIXED_COUNT=$((FIXED_COUNT + 1))
    else
        echo "  ✅ 未发现硬编码的 API Key"
    fi
    
    echo ""
done

echo "============================================================"
if [ $FIXED_COUNT -gt 0 ]; then
    echo "✅ 修复了 $FIXED_COUNT 个文件"
    echo ""
    echo "下一步："
    echo "  1. 检查修改: git diff"
    echo "  2. 提交更改: git add . && git commit -m 'fix: 移除硬编码的 API Key'"
    echo "  3. 推送到 GitHub: git push origin main"
else
    echo "✅ 所有文件都已清理"
fi
echo "============================================================"
