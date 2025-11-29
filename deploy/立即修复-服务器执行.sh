#!/bin/bash
# 立即修复 - 在服务器上执行

echo "=== [1] 停止服务 ==="
sudo systemctl stop liaotian-frontend

echo ""
echo "=== [2] 重写systemd配置 ==="
sudo tee /etc/systemd/system/liaotian-frontend.service > /dev/null <<'EOFSERVICE'
[Unit]
Description=Liaotian Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/liaotian/saas-demo/.next/standalone/liaotian/saas-demo
Environment=PORT=3000
Environment="NVM_DIR=$HOME/.nvm"
Environment="PATH=$HOME/.nvm/versions/node/v20.19.6/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/ubuntu/.nvm/versions/node/v20.19.6/bin/node server.js
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOFSERVICE

echo "✅ 配置已更新"

echo ""
echo "=== [3] 验证配置 ==="
cat /etc/systemd/system/liaotian-frontend.service | grep -E "WorkingDirectory|ExecStart"

echo ""
echo "=== [4] 重新加载并启动 ==="
sudo systemctl daemon-reload
sudo systemctl start liaotian-frontend
sleep 5

echo ""
echo "=== [5] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -20

echo ""
echo "=== [6] 检查端口监听 ==="
ss -tlnp | grep ':3000' || echo "⚠️  端口3000未监听"

echo ""
echo "=== [7] 查看最新日志（如果有错误） ==="
if ! sudo systemctl is-active --quiet liaotian-frontend; then
    echo "服务未运行，查看错误日志:"
    sudo journalctl -u liaotian-frontend -n 10 --no-pager | tail -10
fi

echo ""
echo "=== 完成 ==="

