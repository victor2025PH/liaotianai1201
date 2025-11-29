#!/bin/bash
# 在服务器上直接修复文件

set -e

FILE="/home/ubuntu/liaotian/saas-demo/src/app/group-ai/accounts/page.tsx"

echo "========================================"
echo "在服务器上直接修复文件"
echo "========================================"
echo ""

# 1. 备份原文件
echo "[1] 备份原文件..."
cp "$FILE" "$FILE.bak.$(date +%Y%m%d_%H%M%S)"
echo "✓ 已备份"
echo ""

# 2. 检查第2023行
echo "[2] 检查第2023行..."
sed -n '2020,2030p' "$FILE" | cat -n
echo ""

# 3. 检查workerAccounts.map出现次数
echo "[3] 检查workerAccounts.map出现次数..."
COUNT=$(grep -c "workerAccounts.map" "$FILE" || echo "0")
echo "出现次数: $COUNT"
echo ""

# 4. 如果出现多次，查找所有位置
if [ "$COUNT" -gt "1" ]; then
    echo "[4] 查找所有workerAccounts.map位置..."
    grep -n "workerAccounts.map" "$FILE"
    echo ""
    echo "需要删除重复的代码块"
    echo ""
fi

# 5. 检查TableBody闭合
echo "[5] 检查TableBody标签..."
grep -n "TableBody" "$FILE" | tail -2
echo ""

# 6. 检查文件行数
echo "[6] 检查文件行数..."
wc -l "$FILE"
echo ""

echo "========================================"
echo "检查完成"
echo "========================================"
echo ""
echo "如果发现问题，请手动修复文件"
echo ""

