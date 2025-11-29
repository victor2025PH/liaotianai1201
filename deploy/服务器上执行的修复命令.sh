#!/bin/bash
# 在服务器上执行的修复命令

cd /home/ubuntu/liaotian/saas-demo

# 1. 停止服务
echo "[1] 停止服务..."
sudo systemctl stop liaotian-frontend

# 2. 清理构建缓存
echo "[2] 清理构建缓存..."
rm -rf .next node_modules/.cache

# 3. 检查文件
echo "[3] 检查文件..."
if [ -f "src/app/group-ai/accounts/page.tsx" ]; then
    echo "文件存在"
    wc -l src/app/group-ai/accounts/page.tsx
else
    echo "文件不存在！"
    exit 1
fi

# 4. 加载NVM并构建
echo "[4] 构建（这可能需要几分钟）..."
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
npm run build

# 5. 检查构建结果
if [ -f ".next/BUILD_ID" ]; then
    echo "[OK] 构建成功"
    
    # 检查路由文件
    echo "[5] 检查路由文件..."
    find .next -path '*group-ai/accounts*' -type f 2>/dev/null | head -5
    
    # 6. 重启服务
    echo "[6] 重启服务..."
    sudo systemctl restart liaotian-frontend
    sleep 3
    
    # 7. 检查状态
    echo "[7] 检查服务状态..."
    sudo systemctl status liaotian-frontend --no-pager | head -15
else
    echo "[错误] 构建失败"
    exit 1
fi

echo ""
echo "完成！请访问: http://aikz.usdt2026.cc/group-ai/accounts"

