#!/bin/bash
# 简化版修复502脚本

cd ~/liaotian/saas-demo

# 1. 停止旧进程
pkill -f "next.*dev|node.*3000" 2>/dev/null || true
sleep 2

# 2. 确保依赖已安装
if [ ! -d node_modules ] || [ ! -f node_modules/.bin/next ]; then
    npm install > /tmp/npm_install.log 2>&1
fi

# 3. 后台启动前端
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

# 4. 等待启动
sleep 20

# 5. 验证
echo "前端PID: $FRONTEND_PID" > /tmp/fix_502_result.txt
echo "进程状态: $(ps -p $FRONTEND_PID > /dev/null 2>&1 && echo '运行中' || echo '已退出')" >> /tmp/fix_502_result.txt
echo "端口监听: $(sudo ss -tlnp | grep 3000 | head -1 || echo '未监听')" >> /tmp/fix_502_result.txt
echo "本地连接: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>&1 || echo 'FAILED')" >> /tmp/fix_502_result.txt
echo "后端连接: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health 2>&1 || echo 'FAILED')" >> /tmp/fix_502_result.txt

# 6. 重载Nginx
sudo systemctl reload nginx 2>&1 >> /tmp/fix_502_result.txt
sleep 3

echo "域名连接: $(curl -s -o /dev/null -w '%{http_code}' http://aikz.usdt2026.cc/group-ai/accounts 2>&1 || echo 'FAILED')" >> /tmp/fix_502_result.txt

# 7. 显示日志最后20行
echo "" >> /tmp/fix_502_result.txt
echo "=== 前端日志最后20行 ===" >> /tmp/fix_502_result.txt
tail -20 /tmp/frontend.log >> /tmp/fix_502_result.txt 2>&1 || echo "日志文件不存在" >> /tmp/fix_502_result.txt

cat /tmp/fix_502_result.txt
