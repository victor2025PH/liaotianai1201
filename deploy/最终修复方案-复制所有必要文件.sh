#!/bin/bash
# 最终修复方案 - 复制所有必要文件

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 停止服务 ==="
sudo systemctl stop liaotian-frontend

echo ""
echo "=== [2] 检查源.next目录 ==="
echo "源.next目录中的关键文件:"
ls -la .next/ | grep -E "BUILD_ID|routes|static|server" | head -10

echo ""
echo "=== [3] 删除standalone目录中的.next ==="
rm -rf .next/standalone/liaotian/saas-demo/.next

echo ""
echo "=== [4] 创建.next目录并复制所有必要文件 ==="
mkdir -p .next/standalone/liaotian/saas-demo/.next

# 复制BUILD_ID（必需）
if [ -f ".next/BUILD_ID" ]; then
    cp .next/BUILD_ID .next/standalone/liaotian/saas-demo/.next/
    echo "✅ BUILD_ID已复制"
fi

# 复制static目录（必需）
if [ -d ".next/static" ]; then
    cp -r .next/static .next/standalone/liaotian/saas-demo/.next/
    echo "✅ static目录已复制"
fi

# 尝试复制routes目录（如果存在）
if [ -d ".next/routes" ]; then
    cp -r .next/routes .next/standalone/liaotian/saas-demo/.next/
    echo "✅ routes目录已复制"
else
    echo "⚠️  routes目录不存在（可能不是必需的）"
fi

# 检查并复制其他可能需要的文件
for item in "package.json" "server.js.map" "cache" "trace"; do
    if [ -f ".next/$item" ] || [ -d ".next/$item" ]; then
        cp -r ".next/$item" .next/standalone/liaotian/saas-demo/.next/ 2>/dev/null && echo "✅ $item已复制" || true
    fi
done

echo ""
echo "=== [5] 验证文件已复制 ==="
echo "standalone/.next目录内容:"
ls -la .next/standalone/liaotian/saas-demo/.next/ 2>&1 | head -15

echo ""
echo "检查BUILD_ID:"
cat .next/standalone/liaotian/saas-demo/.next/BUILD_ID 2>&1 || echo "❌ BUILD_ID不存在"

echo ""
echo "检查static目录:"
ls -la .next/standalone/liaotian/saas-demo/.next/static/chunks/adc3be135379192a.js 2>&1 | head -3

echo ""
echo "=== [6] 手动测试服务器启动 ==="
cd .next/standalone/liaotian/saas-demo
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
echo "测试命令: timeout 3 node server.js"
timeout 3 node server.js 2>&1 || echo "测试完成"

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

