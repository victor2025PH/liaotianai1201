#!/bin/bash
# 最终修复静态文件 - 在服务器上执行

set -e

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 停止服务 ==="
sudo systemctl stop liaotian-frontend

echo ""
echo "=== [2] 检查源静态文件 ==="
if [ ! -d ".next/static" ]; then
    echo "❌ .next/static目录不存在，需要重新构建"
    exit 1
fi

echo "源静态文件目录存在"
echo "检查chunks目录:"
ls -la .next/static/chunks/ 2>&1 | head -5

echo ""
echo "=== [3] 查找standalone目录 ==="
STANDALONE_DIR=".next/standalone/liaotian/saas-demo"
if [ ! -d "$STANDALONE_DIR" ]; then
    echo "❌ standalone目录不存在"
    exit 1
fi
echo "Standalone目录: $STANDALONE_DIR"

echo ""
echo "=== [4] 删除旧的静态文件目录 ==="
rm -rf "$STANDALONE_DIR/.next"

echo ""
echo "=== [5] 创建.next目录并复制静态文件 ==="
mkdir -p "$STANDALONE_DIR/.next"
cp -r .next/static "$STANDALONE_DIR/.next/"

echo ""
echo "=== [6] 验证文件已复制 ==="
if [ -f "$STANDALONE_DIR/.next/static/chunks/adc3be135379192a.js" ]; then
    echo "✅ adc3be135379192a.js 已复制"
    ls -lh "$STANDALONE_DIR/.next/static/chunks/adc3be135379192a.js"
else
    echo "❌ 文件复制失败，检查源文件:"
    find .next/static -name "adc3be135379192a.js" 2>/dev/null | head -3
    echo ""
    echo "检查目标目录:"
    ls -la "$STANDALONE_DIR/.next/static/chunks/" 2>&1 | head -5
    exit 1
fi

echo ""
echo "=== [7] 检查其他关键文件 ==="
echo "检查chunks目录文件数量:"
ls "$STANDALONE_DIR/.next/static/chunks/" | wc -l

echo ""
echo "=== [8] 重启服务 ==="
sudo systemctl start liaotian-frontend
sleep 5

echo ""
echo "=== [9] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -15

echo ""
echo "=== [10] 测试静态文件访问 ==="
curl -I http://localhost:3000/_next/static/chunks/adc3be135379192a.js 2>&1 | head -5

echo ""
echo "=== 完成 ==="

