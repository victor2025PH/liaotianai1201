#!/bin/bash
# 在服务器上直接执行此脚本来修复502错误

set -e

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 查找standalone目录 ==="
STANDALONE_DIR=$(find .next/standalone -name 'server.js' -type f 2>/dev/null | head -1 | xargs dirname)

if [ -z "$STANDALONE_DIR" ]; then
    echo "❌ 找不到server.js文件"
    exit 1
fi

FULL_STANDALONE_DIR="/home/ubuntu/liaotian/saas-demo/$STANDALONE_DIR"
echo "Standalone目录: $FULL_STANDALONE_DIR"

echo ""
echo "=== [2] 停止服务 ==="
sudo systemctl stop liaotian-frontend

echo ""
echo "=== [3] 复制静态文件 ==="
mkdir -p "$STANDALONE_DIR/.next/static"
cp -r .next/static/* "$STANDALONE_DIR/.next/static/"
echo "✅ 静态文件已复制"

echo ""
echo "=== [4] 验证静态文件 ==="
if [ -f "$STANDALONE_DIR/.next/static/chunks/adc3be135379192a.js" ]; then
    echo "✅ adc3be135379192a.js 存在"
else
    echo "❌ 静态文件复制失败"
    exit 1
fi

echo ""
echo "=== [5] 备份原配置 ==="
sudo cp /etc/systemd/system/liaotian-frontend.service /etc/systemd/system/liaotian-frontend.service.bak

echo ""
echo "=== [6] 更新systemd服务配置 ==="
sudo tee /etc/systemd/system/liaotian-frontend.service > /dev/null <<EOF
[Unit]
Description=Liaotian Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$FULL_STANDALONE_DIR
Environment=PORT=3000
Environment="NVM_DIR=\$HOME/.nvm"
Environment="PATH=\$HOME/.nvm/versions/node/v20.19.6/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/ubuntu/.nvm/versions/node/v20.19.6/bin/node server.js
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "✅ 服务配置已更新"
echo ""
echo "新配置内容:"
cat /etc/systemd/system/liaotian-frontend.service

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
echo "=== [11] 测试静态文件访问 ==="
curl -I http://localhost:3000/_next/static/chunks/adc3be135379192a.js 2>&1 | head -5

echo ""
echo "=== 完成 ==="
echo "如果服务状态为 active (running)，说明修复成功"
echo "如果仍有问题，请检查日志: sudo journalctl -u liaotian-frontend -n 50 --no-pager"

