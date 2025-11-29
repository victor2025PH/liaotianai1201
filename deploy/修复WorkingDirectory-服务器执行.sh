#!/bin/bash
# 修复WorkingDirectory配置 - 在服务器上执行

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 查找standalone目录 ==="
STANDALONE_DIR=$(find .next/standalone -name 'server.js' -type f 2>/dev/null | head -1 | xargs dirname)
FULL_STANDALONE_DIR="/home/ubuntu/liaotian/saas-demo/$STANDALONE_DIR"
echo "Standalone目录: $FULL_STANDALONE_DIR"

echo ""
echo "=== [2] 停止服务 ==="
sudo systemctl stop liaotian-frontend

echo ""
echo "=== [3] 检查当前配置 ==="
echo "当前WorkingDirectory:"
grep "WorkingDirectory" /etc/systemd/system/liaotian-frontend.service

echo ""
echo "=== [4] 更新WorkingDirectory ==="
sudo sed -i "s|WorkingDirectory=.*|WorkingDirectory=$FULL_STANDALONE_DIR|" /etc/systemd/system/liaotian-frontend.service

echo ""
echo "=== [5] 验证配置已更新 ==="
echo "更新后的WorkingDirectory:"
grep "WorkingDirectory" /etc/systemd/system/liaotian-frontend.service
echo ""
echo "ExecStart:"
grep "ExecStart" /etc/systemd/system/liaotian-frontend.service

echo ""
echo "=== [6] 验证server.js存在 ==="
ls -la "$FULL_STANDALONE_DIR/server.js" || echo "❌ server.js不存在！"

echo ""
echo "=== [7] 重新加载systemd配置 ==="
sudo systemctl daemon-reload

echo ""
echo "=== [8] 启动服务 ==="
sudo systemctl start liaotian-frontend
sleep 5

echo ""
echo "=== [9] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -20

echo ""
echo "=== [10] 检查端口监听 ==="
ss -tlnp | grep ':3000' || echo "⚠️  端口3000未监听"

echo ""
echo "=== [11] 查看最新日志（如果有错误） ==="
sudo journalctl -u liaotian-frontend -n 10 --no-pager | tail -10

echo ""
echo "=== 完成 ==="

