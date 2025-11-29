#!/bin/bash
# 修复standalone模式下的静态文件

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 检查静态文件 ==="
echo "检查.next/static/chunks:"
ls -la .next/static/chunks/ 2>/dev/null | head -5 || echo "目录不存在"

echo ""
echo "检查standalone静态目录:"
ls -la .next/standalone/liaotian/saas-demo/.next/static/chunks/ 2>/dev/null | head -5 || echo "目录不存在"

echo ""
echo "=== [2] 检查缺失的chunk文件 ==="
MISSING_CHUNKS=("c51be5118db7ed00.js" "adc3be135379192a.js" "8c675dcdd045f661.js" "031b6eff58f475dd.js")

for chunk in "${MISSING_CHUNKS[@]}"; do
    if [ -f ".next/static/chunks/$chunk" ]; then
        echo "✅ $chunk 存在于 .next/static/chunks/"
        if [ -f ".next/standalone/liaotian/saas-demo/.next/static/chunks/$chunk" ]; then
            echo "   ✅ 也存在于 standalone 目录"
        else
            echo "   ❌ 不存在于 standalone 目录，需要复制"
            mkdir -p .next/standalone/liaotian/saas-demo/.next/static/chunks/
            cp .next/static/chunks/$chunk .next/standalone/liaotian/saas-demo/.next/static/chunks/
        fi
    else
        echo "❌ $chunk 不存在于 .next/static/chunks/"
    fi
done

echo ""
echo "=== [3] 复制所有静态文件到standalone目录 ==="
if [ -d ".next/static" ] && [ -d ".next/standalone/liaotian/saas-demo/.next" ]; then
    echo "复制静态文件..."
    cp -r .next/static .next/standalone/liaotian/saas-demo/.next/ 2>&1 | head -10
    echo "✅ 静态文件已复制"
else
    echo "❌ 目录不存在，需要重新构建"
fi

echo ""
echo "=== [4] 重启服务 ==="
sudo systemctl restart liaotian-frontend
sleep 5

echo ""
echo "=== [5] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -15

echo ""
echo "=== 完成 ==="

