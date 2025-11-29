#!/bin/bash
# 正确修复standalone结构 - 根据Dockerfile的配置

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 停止服务 ==="
sudo systemctl stop liaotian-frontend

echo ""
echo "=== [2] 检查standalone目录结构 ==="
echo "standalone目录内容:"
ls -la .next/standalone/liaotian/saas-demo/ | head -15

echo ""
echo "=== [3] 根据Dockerfile配置修复 ==="
echo "Dockerfile显示："
echo "  - COPY --from=builder /app/.next/standalone ./"
echo "  - COPY --from=builder /app/.next/static ./.next/static"
echo ""
echo "这意味着："
echo "  - static目录应该在standalone根目录的.next/static"
echo "  - BUILD_ID应该在standalone根目录的.next/BUILD_ID"

echo ""
echo "=== [4] 删除错误的.next目录 ==="
rm -rf .next/standalone/liaotian/saas-demo/.next

echo ""
echo "=== [5] 创建正确的.next目录结构 ==="
mkdir -p .next/standalone/liaotian/saas-demo/.next

# 复制BUILD_ID到.next目录
if [ -f ".next/BUILD_ID" ]; then
    cp .next/BUILD_ID .next/standalone/liaotian/saas-demo/.next/
    echo "✅ BUILD_ID已复制到.next目录"
fi

# 复制static目录到.next目录
if [ -d ".next/static" ]; then
    cp -r .next/static .next/standalone/liaotian/saas-demo/.next/
    echo "✅ static目录已复制到.next目录"
fi

echo ""
echo "=== [6] 验证文件结构 ==="
echo "standalone目录结构:"
ls -la .next/standalone/liaotian/saas-demo/ | head -10
echo ""
echo ".next目录结构:"
ls -la .next/standalone/liaotian/saas-demo/.next/ | head -10
echo ""
echo "检查BUILD_ID:"
cat .next/standalone/liaotian/saas-demo/.next/BUILD_ID 2>&1 || echo "❌ BUILD_ID不存在"
echo ""
echo "检查static文件:"
ls -la .next/standalone/liaotian/saas-demo/.next/static/chunks/adc3be135379192a.js 2>&1 | head -3

echo ""
echo "=== [7] 手动测试服务器启动 ==="
cd .next/standalone/liaotian/saas-demo
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
echo "测试命令: timeout 3 node server.js"
timeout 3 node server.js 2>&1 || echo "测试完成"

echo ""
echo "=== [8] 重启服务 ==="
cd /home/ubuntu/liaotian/saas-demo
sudo systemctl start liaotian-frontend
sleep 5

echo ""
echo "=== [9] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -15

echo ""
echo "=== [10] 查看最新日志（如果有错误） ==="
if ! sudo systemctl is-active --quiet liaotian-frontend; then
    echo "服务未运行，查看错误日志:"
    sudo journalctl -u liaotian-frontend -n 10 --no-pager | tail -10
fi

echo ""
echo "=== [11] 测试静态文件访问 ==="
curl -I http://localhost:3000/_next/static/chunks/adc3be135379192a.js 2>&1 | head -5

echo ""
echo "=== 完成 ==="

