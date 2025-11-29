#!/bin/bash
# 诊断并修复服务启动失败

echo "=== [1] 查看最新错误日志 ==="
sudo journalctl -u liaotian-frontend -n 20 --no-pager | tail -15

echo ""
echo "=== [2] 检查systemd配置 ==="
cat /etc/systemd/system/liaotian-frontend.service | grep -E "WorkingDirectory|ExecStart"

echo ""
echo "=== [3] 检查standalone目录和文件 ==="
cd /home/ubuntu/liaotian/saas-demo/.next/standalone/liaotian/saas-demo
echo "当前目录: $(pwd)"
ls -la server.js 2>&1 | head -3
ls -la .next/static/chunks/adc3be135379192a.js 2>&1 | head -3

echo ""
echo "=== [4] 手动测试服务器启动 ==="
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
echo "测试命令: node server.js"
echo "（如果成功，会看到Next.js启动信息；如果有错误，会显示错误信息）"
timeout 5 node server.js 2>&1 || echo "服务器启动测试完成（超时或错误）"

echo ""
echo "=== [5] 检查文件权限 ==="
ls -la . | head -10

echo ""
echo "=== 诊断完成 ==="

