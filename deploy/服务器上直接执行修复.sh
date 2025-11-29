#!/bin/bash
# 在服务器上直接执行此脚本来修复standalone静态文件问题

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 停止服务 ==="
sudo systemctl stop liaotian-frontend

echo ""
echo "=== [2] 查找standalone目录 ==="
STANDALONE_DIR=$(find .next/standalone -name 'server.js' -type f 2>/dev/null | head -1 | xargs dirname)
if [ -z "$STANDALONE_DIR" ]; then
    echo "❌ 找不到server.js文件，需要重新构建"
    exit 1
fi
echo "Standalone目录: $STANDALONE_DIR"

echo ""
echo "=== [3] 检查源静态文件 ==="
if [ ! -d ".next/static" ]; then
    echo "❌ .next/static目录不存在，需要重新构建"
    exit 1
fi
echo "源静态文件目录存在"

echo ""
echo "=== [4] 创建standalone静态目录并复制文件 ==="
mkdir -p "$STANDALONE_DIR/.next/static"
cp -r .next/static/* "$STANDALONE_DIR/.next/static/"

echo ""
echo "=== [5] 验证文件已复制 ==="
if [ -f "$STANDALONE_DIR/.next/static/chunks/adc3be135379192a.js" ]; then
    echo "✅ adc3be135379192a.js 已复制"
    ls -lh "$STANDALONE_DIR/.next/static/chunks/adc3be135379192a.js"
else
    echo "❌ 文件复制失败"
    exit 1
fi

echo ""
echo "=== [6] 检查systemd服务配置 ==="
echo "当前工作目录配置:"
grep -E "WorkingDirectory|ExecStart" /etc/systemd/system/liaotian-frontend.service

echo ""
echo "=== [7] 重启服务 ==="
sudo systemctl start liaotian-frontend
sleep 5

echo ""
echo "=== [8] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -15

echo ""
echo "=== [9] 测试静态文件访问 ==="
echo "测试本地Next.js服务器:"
curl -I http://localhost:3000/_next/static/chunks/adc3be135379192a.js 2>&1 | head -10

echo ""
echo "=== [10] 检查端口监听 ==="
ss -tlnp | grep ':3000'

echo ""
echo "=== 完成 ==="
echo "如果curl仍然返回404，请检查systemd服务的WorkingDirectory配置"

