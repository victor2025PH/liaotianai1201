#!/bin/bash
# 修复standalone模式下的静态文件问题

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 停止服务 ==="
sudo systemctl stop liaotian-frontend

echo ""
echo "=== [2] 检查目录结构 ==="
echo "源静态文件目录:"
ls -la .next/static/chunks/ 2>/dev/null | head -5 || echo "目录不存在"

echo ""
echo "standalone目录结构:"
ls -la .next/standalone/liaotian/saas-demo/.next/ 2>/dev/null || echo "目录不存在"

echo ""
echo "=== [3] 创建standalone静态目录并复制文件 ==="
mkdir -p .next/standalone/liaotian/saas-demo/.next/static
cp -r .next/static/* .next/standalone/liaotian/saas-demo/.next/static/

echo ""
echo "=== [4] 验证文件已复制 ==="
if [ -f ".next/standalone/liaotian/saas-demo/.next/static/chunks/adc3be135379192a.js" ]; then
    echo "✅ adc3be135379192a.js 已复制到standalone目录"
    ls -lh .next/standalone/liaotian/saas-demo/.next/static/chunks/adc3be135379192a.js
else
    echo "❌ 文件复制失败"
    exit 1
fi

echo ""
echo "=== [5] 检查其他关键文件 ==="
MISSING_CHUNKS=("c51be5118db7ed00.js" "8c675dcdd045f661.js" "031b6eff58f475dd.js")
for chunk in "${MISSING_CHUNKS[@]}"; do
    if [ -f ".next/standalone/liaotian/saas-demo/.next/static/chunks/$chunk" ]; then
        echo "✅ $chunk 存在"
    else
        echo "⚠️  $chunk 不存在（可能不是必需的）"
    fi
done

echo ""
echo "=== [6] 重启服务 ==="
sudo systemctl start liaotian-frontend
sleep 5

echo ""
echo "=== [7] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -15

echo ""
echo "=== [8] 测试静态文件访问 ==="
echo "测试本地Next.js服务器:"
curl -I http://localhost:3000/_next/static/chunks/adc3be135379192a.js 2>&1 | head -5

echo ""
echo "=== 完成 ==="

