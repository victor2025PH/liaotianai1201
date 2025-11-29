#!/bin/bash
# 完整修复 - 最终版本

set -e

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 查找standalone目录 ==="
STANDALONE_DIR=$(find .next/standalone -name 'server.js' -type f 2>/dev/null | head -1 | xargs dirname)
FULL_STANDALONE_DIR="/home/ubuntu/liaotian/saas-demo/$STANDALONE_DIR"
echo "Standalone目录: $FULL_STANDALONE_DIR"

echo ""
echo "=== [2] 验证server.js存在 ==="
if [ ! -f "$FULL_STANDALONE_DIR/server.js" ]; then
    echo "❌ server.js不存在！"
    exit 1
fi
echo "✅ server.js存在"

echo ""
echo "=== [3] 停止服务 ==="
sudo systemctl stop liaotian-frontend

echo ""
echo "=== [4] 复制静态文件 ==="
mkdir -p "$STANDALONE_DIR/.next/static"
cp -r .next/static/* "$STANDALONE_DIR/.next/static/" 2>&1 | head -5
echo "✅ 静态文件已复制"

echo ""
echo "=== [5] 备份并更新systemd配置 ==="
sudo cp /etc/systemd/system/liaotian-frontend.service /etc/systemd/system/liaotian-frontend.service.bak

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
echo "新配置:"
cat /etc/systemd/system/liaotian-frontend.service | grep -E "WorkingDirectory|ExecStart"

echo ""
echo "=== [6] 重新加载systemd配置 ==="
sudo systemctl daemon-reload

echo ""
echo "=== [7] 启动服务 ==="
sudo systemctl start liaotian-frontend
sleep 5

echo ""
echo "=== [8] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -20

echo ""
echo "=== [9] 检查端口监听 ==="
ss -tlnp | grep ':3000' || echo "⚠️  端口3000未监听"

echo ""
echo "=== [10] 查看最新日志 ==="
if ! sudo systemctl is-active --quiet liaotian-frontend; then
    echo "服务未运行，查看错误日志:"
    sudo journalctl -u liaotian-frontend -n 20 --no-pager | tail -15
fi

echo ""
echo "=== 完成 ==="

