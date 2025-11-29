#!/bin/bash
# 修复并构建脚本

set -e

echo "========================================"
echo "修复并构建前端"
echo "========================================"
echo ""

cd /home/ubuntu/liaotian/saas-demo

# 1. 加载nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20

# 2. 验证文件
echo "[1] 验证文件..."
if [ ! -f "src/app/group-ai/accounts/page.tsx" ]; then
    echo "✗ 文件不存在"
    exit 1
fi

# 检查行数
LINES=$(wc -l < src/app/group-ai/accounts/page.tsx)
echo "文件行数: $LINES"

# 检查workerAccounts.map出现次数
COUNT=$(grep -c "workerAccounts.map" src/app/group-ai/accounts/page.tsx || echo "0")
echo "workerAccounts.map出现次数: $COUNT"

# 查看第2023行
echo ""
echo "第2023行内容:"
sed -n '2023p' src/app/group-ai/accounts/page.tsx
echo ""

# 3. 清理
echo "[2] 清理旧构建..."
rm -rf .next node_modules/.cache
echo "✓ 已清理"
echo ""

# 4. 构建
echo "[3] 重新构建..."
npm run build

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 构建成功"
    
    # 5. 验证构建
    if [ -f ".next/BUILD_ID" ]; then
        BUILD_ID=$(cat .next/BUILD_ID)
        echo "✓ BUILD_ID: $BUILD_ID"
        
        # 6. 重启服务
        echo ""
        echo "[4] 重启服务..."
        sudo systemctl restart liaotian-frontend
        sleep 5
        
        # 7. 检查状态
        echo "[5] 检查服务状态..."
        sudo systemctl status liaotian-frontend --no-pager | head -20
        
        if sudo systemctl is-active --quiet liaotian-frontend; then
            echo ""
            echo "✓ 服务运行正常"
        else
            echo ""
            echo "✗ 服务未运行"
            sudo journalctl -u liaotian-frontend -n 30 --no-pager
        fi
    else
        echo "✗ BUILD_ID不存在"
        exit 1
    fi
else
    echo ""
    echo "✗ 构建失败"
    exit 1
fi

echo ""
echo "========================================"
echo "完成！"
echo "========================================"

