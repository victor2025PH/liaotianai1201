#!/bin/bash
# 完整部署角色选择功能

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 停止服务 ==="
sudo systemctl stop liaotian-frontend

echo ""
echo "=== [2] 替换文件 ==="
cp /tmp/accounts_page.tsx src/app/group-ai/accounts/page.tsx
echo "✅ 文件已替换"

echo ""
echo "=== [3] 加载NVM ==="
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20

echo ""
echo "=== [4] 重新构建 ==="
npm run build

echo ""
echo "=== [5] 复制必要文件到standalone目录 ==="
mkdir -p .next/standalone/liaotian/saas-demo/.next/server
cp .next/BUILD_ID .next/standalone/liaotian/saas-demo/.next/ 2>/dev/null || echo "⚠ BUILD_ID可能不存在"
cp .next/*.json .next/standalone/liaotian/saas-demo/.next/ 2>/dev/null || echo "⚠ JSON文件可能不存在"
cp -r .next/server/* .next/standalone/liaotian/saas-demo/.next/server/ 2>/dev/null || echo "⚠ server目录可能不存在"
cp -r .next/static .next/standalone/liaotian/saas-demo/.next/ 2>/dev/null || echo "⚠ static目录可能不存在"
echo "✅ 文件已复制"

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

