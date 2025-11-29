#!/bin/bash
# 检查构建错误

cd /home/ubuntu/liaotian/saas-demo

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20

echo "=== 检查文件 ==="
ls -la src/app/group-ai/accounts/page.tsx
echo ""

echo "=== 检查目录结构 ==="
ls -la src/app/group-ai/accounts/
echo ""

echo "=== 检查构建后的路由 ==="
ls -la .next/server/app/group-ai/accounts/ 2>&1
echo ""

echo "=== 查找所有 accounts 相关的路由文件 ==="
find .next/server/app/group-ai/accounts -name 'page.js' 2>&1
echo ""

echo "=== 检查 app-paths-manifest.json ==="
cat .next/server/app-paths-manifest.json 2>/dev/null | grep -o '"group-ai/accounts[^"]*"' | head -10
echo ""

echo "=== 重新构建并查看详细输出 ==="
npm run build 2>&1 | tee /tmp/build_full.log | tail -100

echo ""
echo "=== 检查构建日志中的错误 ==="
grep -i "error\|failed\|warning" /tmp/build_full.log | tail -20

