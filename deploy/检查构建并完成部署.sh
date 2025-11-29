#!/bin/bash
# 检查构建状态并完成部署

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 检查构建状态 ==="
if [ -f ".next/BUILD_ID" ]; then
    echo "✅ 构建已完成"
    ls -la .next/BUILD_ID | head -3
else
    echo "❌ 构建未完成，需要重新构建"
    echo ""
    echo "=== [2] 开始构建 ==="
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    nvm use 20
    npm run build
    echo ""
    echo "构建完成，请等待构建完成后再次执行此脚本"
    exit 0
fi

echo ""
echo "=== [3] 检查standalone目录 ==="
if [ -d ".next/standalone" ]; then
    echo "✅ standalone目录已存在"
else
    echo "❌ standalone目录不存在，构建可能使用了不同的配置"
    echo "检查.next目录结构:"
    ls -la .next/ | head -10
    exit 1
fi

echo ""
echo "=== [4] 复制必要文件到standalone目录 ==="
mkdir -p .next/standalone/liaotian/saas-demo/.next/server
cp .next/BUILD_ID .next/standalone/liaotian/saas-demo/.next/ 2>&1
cp .next/*.json .next/standalone/liaotian/saas-demo/.next/ 2>&1
cp -r .next/server/* .next/standalone/liaotian/saas-demo/.next/server/ 2>&1
cp -r .next/static .next/standalone/liaotian/saas-demo/.next/ 2>&1
echo "✅ 文件已复制"

echo ""
echo "=== [5] 验证必要文件 ==="
echo "检查pages-manifest.json:"
ls -la .next/standalone/liaotian/saas-demo/.next/server/pages-manifest.json 2>&1 | head -3

echo ""
echo "=== [6] 启动服务 ==="
sudo systemctl start liaotian-frontend
sleep 5

echo ""
echo "=== [7] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -15

echo ""
echo "=== [8] 测试服务 ==="
curl -I http://localhost:3000/group-ai/accounts 2>&1 | head -5

echo ""
echo "=== 完成 ==="

