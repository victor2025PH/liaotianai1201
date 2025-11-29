#!/bin/bash
# 诊断并修复部署问题

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 检查文件是否存在 ==="
ls -la src/app/group-ai/accounts/page.tsx 2>&1 | head -3
ls -la /tmp/accounts_page.tsx 2>&1 | head -3

echo ""
echo "=== [2] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -20

echo ""
echo "=== [3] 检查最新日志 ==="
sudo journalctl -u liaotian-frontend -n 20 --no-pager | tail -20

echo ""
echo "=== [4] 检查构建目录 ==="
ls -la .next/standalone/liaotian/saas-demo/.next/server/pages-manifest.json 2>&1 | head -3

echo ""
echo "=== [5] 检查端口 ==="
netstat -tlnp | grep 3000 || ss -tlnp | grep 3000

echo ""
echo "=== [6] 手动测试服务器启动 ==="
cd .next/standalone/liaotian/saas-demo
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
timeout 3 node server.js 2>&1 | head -10 || echo "测试完成"

echo ""
echo "=== [7] 如果构建失败，重新构建 ==="
cd /home/ubuntu/liaotian/saas-demo
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
echo "开始构建..."
npm run build 2>&1 | tail -30

echo ""
echo "=== 完成 ==="

