#!/bin/bash
# 检查standalone结构并修复

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 检查源.next目录结构 ==="
echo "源.next目录内容:"
ls -la .next/ | head -20

echo ""
echo "=== [2] 检查standalone目录结构 ==="
echo "standalone目录内容:"
ls -la .next/standalone/liaotian/saas-demo/ | head -20

echo ""
echo "=== [3] 检查standalone目录中的.next ==="
echo "standalone/.next目录内容:"
ls -la .next/standalone/liaotian/saas-demo/.next/ 2>&1 | head -20

echo ""
echo "=== [4] 检查server.js引用的路径 ==="
echo "server.js中关于.next的引用:"
grep -E "\.next|BUILD_ID|routes|static" .next/standalone/liaotian/saas-demo/server.js | head -10

echo ""
echo "=== [5] 检查源.next目录中的文件 ==="
echo "BUILD_ID:"
ls -la .next/BUILD_ID 2>&1
echo ""
echo "routes目录:"
ls -la .next/routes 2>&1 | head -5 || echo "routes目录不存在"
echo ""
echo "static目录:"
ls -la .next/static 2>&1 | head -5

echo ""
echo "=== [6] 检查standalone目录需要的文件 ==="
cd .next/standalone/liaotian/saas-demo
echo "当前目录: $(pwd)"
echo ""
echo "检查server.js需要的文件:"
if [ -f "server.js" ]; then
    echo "server.js存在"
    # 尝试读取server.js看看它需要什么
    head -50 server.js | grep -E "require|import|\.next" | head -10
fi

echo ""
echo "=== 诊断完成 ==="

