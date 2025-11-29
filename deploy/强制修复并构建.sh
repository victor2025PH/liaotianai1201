#!/bin/bash
# 强制修复并构建

set -e

echo "========================================"
echo "强制修复并构建"
echo "========================================"
echo ""

cd /home/ubuntu/liaotian/saas-demo

# 1. 验证文件
echo "[1] 验证文件..."
wc -l src/app/group-ai/accounts/page.tsx
sed -n '2023p' src/app/group-ai/accounts/page.tsx
echo ""

# 2. 检查workerAccounts.map
echo "[2] 检查workerAccounts.map..."
grep -n "workerAccounts.map" src/app/group-ai/accounts/page.tsx
echo ""

# 3. 检查所有))}位置
echo "[3] 检查所有))}位置..."
grep -n "))}" src/app/group-ai/accounts/page.tsx | tail -5
echo ""

# 4. 加载nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20

# 5. 清理
echo "[4] 清理..."
rm -rf .next node_modules/.cache
echo "✓ 已清理"
echo ""

# 6. 构建
echo "[5] 构建..."
npm run build 2>&1 | tee /tmp/build_output.txt

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo "✓ 构建成功"
    
    # 7. 验证
    if [ -f ".next/BUILD_ID" ]; then
        echo "✓ BUILD_ID存在"
        
        # 8. 重启服务
        echo ""
        echo "[6] 重启服务..."
        sudo systemctl restart liaotian-frontend
        sleep 5
        
        # 9. 检查状态
        echo "[7] 检查服务状态..."
        sudo systemctl status liaotian-frontend --no-pager | head -20
    else
        echo "✗ BUILD_ID不存在"
        exit 1
    fi
else
    echo ""
    echo "✗ 构建失败"
    echo "错误信息（最后30行）："
    tail -30 /tmp/build_output.txt
    exit 1
fi

echo ""
echo "========================================"
echo "完成！"
echo "========================================"

