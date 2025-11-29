#!/bin/bash
# 诊断并修复502错误

cd /home/ubuntu/liaotian/saas-demo

echo "=== [1] 检查服务状态 ==="
sudo systemctl status liaotian-frontend --no-pager | head -20

echo ""
echo "=== [2] 检查服务日志 ==="
sudo journalctl -u liaotian-frontend -n 30 --no-pager

echo ""
echo "=== [3] 检查端口监听 ==="
ss -tlnp | grep ':3000' || echo "端口3000未监听"

echo ""
echo "=== [4] 查找standalone目录 ==="
STANDALONE_DIR=$(find .next/standalone -name 'server.js' -type f 2>/dev/null | head -1 | xargs dirname)
if [ -z "$STANDALONE_DIR" ]; then
    echo "❌ 找不到server.js文件"
    exit 1
fi
echo "Standalone目录: $STANDALONE_DIR"

echo ""
echo "=== [5] 检查静态文件 ==="
if [ -f "$STANDALONE_DIR/.next/static/chunks/adc3be135379192a.js" ]; then
    echo "✅ 静态文件存在"
else
    echo "❌ 静态文件不存在，正在复制..."
    mkdir -p "$STANDALONE_DIR/.next/static"
    cp -r .next/static/* "$STANDALONE_DIR/.next/static/"
fi

echo ""
echo "=== [6] 检查systemd服务配置 ==="
cat /etc/systemd/system/liaotian-frontend.service | grep -E "WorkingDirectory|ExecStart"

echo ""
echo "=== [7] 检查server.js文件 ==="
ls -la "$STANDALONE_DIR/server.js"

echo ""
echo "=== [8] 尝试手动启动服务器（测试） ==="
cd "$STANDALONE_DIR"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
echo "测试命令: node server.js"
echo "（按Ctrl+C停止测试）"
