#!/bin/bash
# 修复缺少构建元数据 - 一键执行

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 停止服务 ==="
sudo systemctl stop liaotian-frontend

echo ""
echo "=== [2] 检查源.next目录内容 ==="
echo "BUILD_ID:"
ls -la .next/BUILD_ID 2>&1 | head -3
echo ""
echo "routes目录:"
ls -la .next/routes 2>&1 | head -5

echo ""
echo "=== [3] 删除standalone目录中的.next ==="
rm -rf .next/standalone/liaotian/saas-demo/.next

echo ""
echo "=== [4] 创建.next目录并复制必要的构建文件 ==="
mkdir -p .next/standalone/liaotian/saas-demo/.next

# 复制BUILD_ID（必需）
if [ -f ".next/BUILD_ID" ]; then
    cp .next/BUILD_ID .next/standalone/liaotian/saas-demo/.next/
    echo "✅ BUILD_ID已复制"
fi

# 复制routes目录（必需）
if [ -d ".next/routes" ]; then
    cp -r .next/routes .next/standalone/liaotian/saas-demo/.next/
    echo "✅ routes目录已复制"
fi

# 复制static目录（必需）
if [ -d ".next/static" ]; then
    cp -r .next/static .next/standalone/liaotian/saas-demo/.next/
    echo "✅ static目录已复制"
fi

# 复制其他可能需要的文件
for file in "package.json" "server.js.map" "standalone"; do
    if [ -f ".next/$file" ] || [ -d ".next/$file" ]; then
        cp -r ".next/$file" .next/standalone/liaotian/saas-demo/.next/ 2>/dev/null || true
    fi
done

echo ""
echo "=== [5] 验证文件已复制 ==="
ls -la .next/standalone/liaotian/saas-demo/.next/ 2>&1 | head -10

echo ""
echo "检查BUILD_ID:"
cat .next/standalone/liaotian/saas-demo/.next/BUILD_ID 2>&1 || echo "❌ BUILD_ID不存在"

echo ""
echo "检查static目录:"
ls -la .next/standalone/liaotian/saas-demo/.next/static/chunks/adc3be135379192a.js 2>&1 | head -3

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

