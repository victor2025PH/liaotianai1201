#!/bin/bash
# 完成修复 - 在服务器上执行

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 检查当前配置 ==="
cat /etc/systemd/system/liaotian-frontend.service | grep -E "WorkingDirectory|ExecStart"

echo ""
echo "=== [2] 重新加载systemd配置 ==="
sudo systemctl daemon-reload

echo ""
echo "=== [3] 启动服务 ==="
sudo systemctl start liaotian-frontend
sleep 5

echo ""
echo "=== [4] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -20

echo ""
echo "=== [5] 检查端口监听 ==="
ss -tlnp | grep ':3000' || echo "端口3000未监听"

echo ""
echo "=== [6] 查看最新日志 ==="
sudo journalctl -u liaotian-frontend -n 20 --no-pager

echo ""
echo "=== [7] 测试静态文件 ==="
curl -I http://localhost:3000/_next/static/chunks/adc3be135379192a.js 2>&1 | head -5

echo ""
echo "=== 完成 ==="

