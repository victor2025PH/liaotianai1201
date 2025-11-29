#!/bin/bash
# 完整部署角色选择功能 - 服务器端执行

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 停止服务 ==="
sudo systemctl stop liaotian-frontend

echo ""
echo "=== [2] 替换文件 ==="
if [ -f "/tmp/accounts_page.tsx" ]; then
    cp /tmp/accounts_page.tsx src/app/group-ai/accounts/page.tsx
    echo "✅ 文件已替换"
    ls -la src/app/group-ai/accounts/page.tsx | head -3
else
    echo "❌ 错误: /tmp/accounts_page.tsx 不存在"
    exit 1
fi

echo ""
echo "=== [3] 加载NVM ==="
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
echo "✅ Node版本: $(node --version)"

echo ""
echo "=== [4] 清理旧的构建 ==="
rm -rf .next/standalone
echo "✅ 已清理standalone目录"

echo ""
echo "=== [5] 重新构建 ==="
npm run build 2>&1 | tail -20

echo ""
echo "=== [6] 检查构建结果 ==="
if [ ! -d ".next/standalone" ]; then
    echo "❌ 错误: standalone目录不存在，构建可能失败"
    exit 1
fi
echo "✅ standalone目录已创建"

echo ""
echo "=== [7] 复制必要文件到standalone目录 ==="
mkdir -p .next/standalone/liaotian/saas-demo/.next/server
cp .next/BUILD_ID .next/standalone/liaotian/saas-demo/.next/ 2>&1
cp .next/*.json .next/standalone/liaotian/saas-demo/.next/ 2>&1
cp -r .next/server/* .next/standalone/liaotian/saas-demo/.next/server/ 2>&1
cp -r .next/static .next/standalone/liaotian/saas-demo/.next/ 2>&1
echo "✅ 文件已复制"

echo ""
echo "=== [8] 验证必要文件 ==="
echo "检查pages-manifest.json:"
ls -la .next/standalone/liaotian/saas-demo/.next/server/pages-manifest.json 2>&1 | head -3
echo ""
echo "检查BUILD_ID:"
ls -la .next/standalone/liaotian/saas-demo/.next/BUILD_ID 2>&1 | head -3
echo ""
echo "检查routes-manifest.json:"
ls -la .next/standalone/liaotian/saas-demo/.next/routes-manifest.json 2>&1 | head -3

echo ""
echo "=== [9] 启动服务 ==="
sudo systemctl start liaotian-frontend
sleep 5

echo ""
echo "=== [10] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -15

echo ""
echo "=== [11] 测试服务 ==="
curl -I http://localhost:3000/group-ai/accounts 2>&1 | head -5

echo ""
echo "=== 完成 ==="

