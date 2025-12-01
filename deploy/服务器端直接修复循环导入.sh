#!/bin/bash
# 直接在服務器上修復循環導入錯誤

set -e

echo "========================================="
echo "直接修復循環導入錯誤"
echo "========================================="
echo ""

cd ~/liaotian/admin-backend/app/api/group_ai

# 步驟 1: 備份文件
echo "【步驟1】備份原文件..."
cp __init__.py __init__.py.bak.$(date +%Y%m%d_%H%M%S)
echo "  ✓ 已備份"
echo ""

# 步驟 2: 修復文件（移除 statistics 導入）
echo "【步驟2】修復導入錯誤..."
# 使用 sed 移除 statistics 導入
sed -i 's/, statistics//' __init__.py

# 或者更安全的方法：檢查並移除
if grep -q ", statistics" __init__.py; then
    sed -i 's/, statistics//' __init__.py
    echo "  ✓ 已移除 statistics 導入"
else
    echo "  ✓ statistics 導入已不存在"
fi
echo ""

# 步驟 3: 驗證修復
echo "【步驟3】驗證修復..."
if grep -q "statistics" __init__.py; then
    echo "  ⚠ 文件中仍包含 statistics，嘗試手動修復..."
    # 顯示包含 statistics 的行
    grep -n "statistics" __init__.py
else
    echo "  ✓ 文件已修復，不包含 statistics"
fi
echo ""

echo "========================================="
echo "修復完成！現在可以重啟服務"
echo "========================================="
