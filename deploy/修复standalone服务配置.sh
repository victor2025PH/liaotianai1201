#!/bin/bash
# 修复standalone模式的服务配置

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 检查standalone server.js ==="
if [ -f ".next/standalone/liaotian/saas-demo/server.js" ]; then
    echo "✅ server.js存在"
    ls -la .next/standalone/liaotian/saas-demo/server.js
else
    echo "❌ server.js不存在"
    exit 1
fi

echo ""
echo "=== [2] 检查Node路径 ==="
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
NODE_PATH=$(which node)
echo "Node路径: $NODE_PATH"

echo ""
echo "=== [3] 备份当前服务配置 ==="
sudo cp /etc/systemd/system/liaotian-frontend.service /etc/systemd/system/liaotian-frontend.service.bak
echo "✅ 已备份"

echo ""
echo "=== [4] 创建新的服务配置 ==="
sudo tee /etc/systemd/system/liaotian-frontend.service > /dev/null <<EOF
[Unit]
Description=Liaotian Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/liaotian/saas-demo
Environment=PORT=3000
Environment="NVM_DIR=\$HOME/.nvm"
Environment="PATH=\$HOME/.nvm/versions/node/v20.19.6/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$NODE_PATH /home/ubuntu/liaotian/saas-demo/.next/standalone/liaotian/saas-demo/server.js
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "✅ 新配置已创建"

echo ""
echo "=== [5] 重新加载systemd ==="
sudo systemctl daemon-reload
echo "✅ 已重新加载"

echo ""
echo "=== [6] 停止旧服务 ==="
sudo systemctl stop liaotian-frontend
sleep 2

echo ""
echo "=== [7] 启动新服务 ==="
sudo systemctl start liaotian-frontend
sleep 5

echo ""
echo "=== [8] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -20

echo ""
echo "=== [9] 检查端口 ==="
if ss -tlnp | grep -q ':3000'; then
    echo "✅ 端口3000正在监听"
    ss -tlnp | grep ':3000'
else
    echo "❌ 端口3000未监听"
    echo "查看最新日志:"
    sudo journalctl -u liaotian-frontend -n 10 --no-pager
fi

echo ""
echo "=== 完成 ==="

