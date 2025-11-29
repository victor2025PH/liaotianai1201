#!/bin/bash
# 修复systemd服务配置

cd /home/ubuntu/liaotian/saas-demo

# 查找standalone目录
STANDALONE_DIR=$(find .next/standalone -name 'server.js' -type f 2>/dev/null | head -1 | xargs dirname)

if [ -z "$STANDALONE_DIR" ]; then
    echo "❌ 找不到server.js文件"
    exit 1
fi

FULL_STANDALONE_DIR="/home/ubuntu/liaotian/saas-demo/$STANDALONE_DIR"
echo "Standalone目录: $FULL_STANDALONE_DIR"

# 备份原配置
sudo cp /etc/systemd/system/liaotian-frontend.service /etc/systemd/system/liaotian-frontend.service.bak

# 创建新配置
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
echo "重新加载systemd配置..."
sudo systemctl daemon-reload

echo ""
echo "启动服务..."
sudo systemctl start liaotian-frontend
sleep 5

echo ""
echo "检查服务状态..."
sudo systemctl status liaotian-frontend --no-pager | head -15

