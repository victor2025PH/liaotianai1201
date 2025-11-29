#!/bin/bash
# 等待构建完成并继续部署

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 检查构建是否完成 ==="
if [ -d ".next/standalone" ]; then
    echo "✅ 构建已完成，standalone目录存在"
else
    echo "⏳ 构建未完成，standalone目录不存在"
    echo "请等待构建完成后再执行此脚本"
    exit 1
fi

echo ""
echo "=== [2] 复制必要文件到standalone目录 ==="
mkdir -p .next/standalone/liaotian/saas-demo/.next/server
cp .next/BUILD_ID .next/standalone/liaotian/saas-demo/.next/ 2>&1
cp .next/*.json .next/standalone/liaotian/saas-demo/.next/ 2>&1
cp -r .next/server/* .next/standalone/liaotian/saas-demo/.next/server/ 2>&1
cp -r .next/static .next/standalone/liaotian/saas-demo/.next/ 2>&1
echo "✅ 文件已复制"

echo ""
echo "=== [3] 验证必要文件 ==="
echo "检查pages-manifest.json:"
ls -la .next/standalone/liaotian/saas-demo/.next/server/pages-manifest.json 2>&1 | head -3
echo ""
echo "检查BUILD_ID:"
ls -la .next/standalone/liaotian/saas-demo/.next/BUILD_ID 2>&1 | head -3
echo ""
echo "检查routes-manifest.json:"
ls -la .next/standalone/liaotian/saas-demo/.next/routes-manifest.json 2>&1 | head -3

echo ""
echo "=== [4] 启动服务 ==="
sudo systemctl start liaotian-frontend
sleep 5

echo ""
echo "=== [5] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -15

echo ""
echo "=== [6] 测试服务 ==="
curl -I http://localhost:3000/group-ai/accounts 2>&1 | head -5

echo ""
echo "=== 完成 ==="

