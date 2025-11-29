#!/bin/bash
# 一键修复静态文件 - 直接复制整个脚本到服务器执行

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 停止服务 ==="
sudo systemctl stop liaotian-frontend

echo ""
echo "=== [2] 检查源静态文件 ==="
if [ ! -f ".next/static/chunks/adc3be135379192a.js" ]; then
    echo "⚠️  源文件不存在，需要重新构建"
    echo "开始重新构建..."
    rm -rf .next node_modules/.cache
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    nvm use 20
    npm run build
    echo "✅ 构建完成"
else
    echo "✅ 源文件存在"
fi

echo ""
echo "=== [3] 删除旧的静态文件目录 ==="
rm -rf .next/standalone/liaotian/saas-demo/.next

echo ""
echo "=== [4] 创建.next目录并复制静态文件 ==="
mkdir -p .next/standalone/liaotian/saas-demo/.next
cp -r .next/static .next/standalone/liaotian/saas-demo/.next/

echo ""
echo "=== [5] 验证文件已复制 ==="
if [ -f ".next/standalone/liaotian/saas-demo/.next/static/chunks/adc3be135379192a.js" ]; then
    echo "✅ adc3be135379192a.js 已复制"
    ls -lh .next/standalone/liaotian/saas-demo/.next/static/chunks/adc3be135379192a.js
else
    echo "❌ 文件复制失败"
    exit 1
fi

echo ""
echo "=== [6] 重启服务 ==="
sudo systemctl start liaotian-frontend
sleep 5

echo ""
echo "=== [7] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -15

echo ""
echo "=== [8] 测试静态文件访问 ==="
curl -I http://localhost:3000/_next/static/chunks/adc3be135379192a.js 2>&1 | head -5

echo ""
echo "=== 完成 ==="

