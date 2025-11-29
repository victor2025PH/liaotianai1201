#!/bin/bash
# 诊断服务失败原因

echo "=== [1] 检查当前配置 ==="
cat /etc/systemd/system/liaotian-frontend.service | grep -E "WorkingDirectory|ExecStart"

echo ""
echo "=== [2] 检查standalone目录和server.js ==="
STANDALONE_DIR="/home/ubuntu/liaotian/saas-demo/.next/standalone/liaotian/saas-demo"
echo "Standalone目录: $STANDALONE_DIR"
ls -la "$STANDALONE_DIR/server.js" || echo "❌ server.js不存在"

echo ""
echo "=== [3] 检查静态文件 ==="
ls -la "$STANDALONE_DIR/.next/static/chunks/adc3be135379192a.js" 2>&1 | head -3

echo ""
echo "=== [4] 查看最新错误日志 ==="
sudo journalctl -u liaotian-frontend -n 30 --no-pager | tail -20

echo ""
echo "=== [5] 尝试手动启动服务器（测试） ==="
cd "$STANDALONE_DIR"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
echo "测试命令: node server.js"
echo "（如果成功，会看到Next.js启动信息；如果有错误，会显示错误信息）"
echo "（按Ctrl+C停止测试）"
timeout 5 node server.js 2>&1 || echo "服务器启动测试完成（超时或错误）"

echo ""
echo "=== [6] 检查文件权限 ==="
ls -la "$STANDALONE_DIR" | head -10

echo ""
echo "=== 诊断完成 ==="

