#!/bin/bash
# 修复routes-manifest.json - 一键执行

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 停止服务 ==="
sudo systemctl stop liaotian-frontend

echo ""
echo "=== [2] 检查源.next目录中的JSON文件 ==="
ls -la .next/*.json 2>&1 | head -10

echo ""
echo "=== [3] 复制所有JSON文件到standalone/.next目录 ==="
cp .next/*.json .next/standalone/liaotian/saas-demo/.next/ 2>&1
echo "✅ JSON文件已复制"

echo ""
echo "=== [4] 验证文件已复制 ==="
ls -la .next/standalone/liaotian/saas-demo/.next/*.json 2>&1 | head -10

echo ""
echo "=== [5] 检查所有必要文件 ==="
echo "BUILD_ID:"
ls -la .next/standalone/liaotian/saas-demo/.next/BUILD_ID 2>&1 | head -3
echo ""
echo "routes-manifest.json:"
ls -la .next/standalone/liaotian/saas-demo/.next/routes-manifest.json 2>&1 | head -3
echo ""
echo "static目录:"
ls -la .next/standalone/liaotian/saas-demo/.next/static/chunks/adc3be135379192a.js 2>&1 | head -3

echo ""
echo "=== [6] 手动测试服务器启动 ==="
cd .next/standalone/liaotian/saas-demo
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
echo "测试命令: timeout 5 node server.js"
timeout 5 node server.js 2>&1 | head -10 || echo "测试完成"

echo ""
echo "=== [7] 重启服务 ==="
cd /home/ubuntu/liaotian/saas-demo
sudo systemctl start liaotian-frontend
sleep 5

echo ""
echo "=== [8] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -15

echo ""
echo "=== [9] 测试静态文件访问 ==="
curl -I http://localhost:3000/_next/static/chunks/adc3be135379192a.js 2>&1 | head -5

echo ""
echo "=== 完成 ==="

