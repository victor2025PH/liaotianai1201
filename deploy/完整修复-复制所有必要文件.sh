#!/bin/bash
# 完整修复 - 复制所有必要文件

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 停止服务 ==="
sudo systemctl stop liaotian-frontend

echo ""
echo "=== [2] 检查源.next目录结构 ==="
echo "检查server目录:"
ls -la .next/server/ 2>&1 | head -10

echo ""
echo "=== [3] 创建.next目录结构 ==="
mkdir -p .next/standalone/liaotian/saas-demo/.next/server

echo ""
echo "=== [4] 复制所有必要文件 ==="

# 复制BUILD_ID
if [ -f ".next/BUILD_ID" ]; then
    cp .next/BUILD_ID .next/standalone/liaotian/saas-demo/.next/
    echo "✅ BUILD_ID已复制"
fi

# 复制所有JSON文件
if ls .next/*.json 1> /dev/null 2>&1; then
    cp .next/*.json .next/standalone/liaotian/saas-demo/.next/
    echo "✅ JSON文件已复制"
fi

# 复制server目录
if [ -d ".next/server" ]; then
    cp -r .next/server/* .next/standalone/liaotian/saas-demo/.next/server/
    echo "✅ server目录已复制"
fi

# 复制static目录
if [ -d ".next/static" ]; then
    cp -r .next/static .next/standalone/liaotian/saas-demo/.next/
    echo "✅ static目录已复制"
fi

echo ""
echo "=== [5] 验证文件已复制 ==="
echo "检查BUILD_ID:"
ls -la .next/standalone/liaotian/saas-demo/.next/BUILD_ID 2>&1 | head -3
echo ""
echo "检查routes-manifest.json:"
ls -la .next/standalone/liaotian/saas-demo/.next/routes-manifest.json 2>&1 | head -3
echo ""
echo "检查server/pages-manifest.json:"
ls -la .next/standalone/liaotian/saas-demo/.next/server/pages-manifest.json 2>&1 | head -3
echo ""
echo "检查static文件:"
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
echo "=== [9] 查看最新日志（如果有错误） ==="
if ! sudo systemctl is-active --quiet liaotian-frontend; then
    echo "服务未运行，查看错误日志:"
    sudo journalctl -u liaotian-frontend -n 10 --no-pager | tail -10
fi

echo ""
echo "=== [10] 测试静态文件访问 ==="
curl -I http://localhost:3000/_next/static/chunks/adc3be135379192a.js 2>&1 | head -5

echo ""
echo "=== 完成 ==="

