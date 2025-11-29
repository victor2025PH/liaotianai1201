#!/bin/bash
# 修复502问题 - 完整自动化脚本
# 在远程服务器 ubuntu@165.154.233.55 上执行

set -e

echo "开始修复502问题..." > /tmp/fix_502_status.txt

# 1. 确保前端端口配置正确
cd ~/liaotian/saas-demo
if ! grep -q '"dev": "next dev -p 3000"' package.json; then
    echo "修复端口配置..." >> /tmp/fix_502_status.txt
    node -e "
    const fs = require('fs');
    const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    pkg.scripts.dev = 'next dev -p 3000';
    fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2) + '\n', 'utf8');
    " || echo "修复端口配置失败" >> /tmp/fix_502_status.txt
fi

# 2. 停止所有旧进程
pkill -f "next.*dev|node.*3000" 2>/dev/null || true
sleep 2

# 3. 确保后端运行
cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "启动后端服务..." >> /tmp/fix_502_status.txt
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    sleep 2
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
    sleep 5
fi

# 4. 启动前端（先测试是否正常）
cd ~/liaotian/saas-demo

# 检查node_modules
if [ ! -d node_modules ] || [ ! -f node_modules/.bin/next ]; then
    echo "安装依赖..." >> /tmp/fix_502_status.txt
    npm install 2>&1 | tail -10 >> /tmp/fix_502_status.txt
fi

# 前台测试运行
echo "测试运行前端..." >> /tmp/fix_502_status.txt
timeout 30 npm run dev > /tmp/frontend_test.log 2>&1 &
TEST_PID=$!
sleep 20

if ps -p $TEST_PID > /dev/null 2>&1; then
    # 检查端口
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "前端测试成功" >> /tmp/fix_502_status.txt
        kill $TEST_PID 2>/dev/null || true
        sleep 2
        
        # 后台启动
        nohup npm run dev > /tmp/frontend.log 2>&1 &
        sleep 15
        
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo "前端启动成功" >> /tmp/fix_502_status.txt
        else
            echo "前端启动失败" >> /tmp/fix_502_status.txt
            tail -30 /tmp/frontend.log >> /tmp/fix_502_status.txt
        fi
    else
        echo "前端测试失败，端口未响应" >> /tmp/fix_502_status.txt
        kill $TEST_PID 2>/dev/null || true
        cat /tmp/frontend_test.log >> /tmp/fix_502_status.txt
    fi
else
    echo "前端测试失败，进程退出" >> /tmp/fix_502_status.txt
    cat /tmp/frontend_test.log >> /tmp/fix_502_status.txt
fi

# 5. 重载Nginx
sudo systemctl reload nginx 2>/dev/null || true

# 6. 验证
echo "" >> /tmp/fix_502_status.txt
echo "验证结果:" >> /tmp/fix_502_status.txt
curl -s -o /dev/null -w '后端: %{http_code}\n' http://localhost:8000/health >> /tmp/fix_502_status.txt 2>&1 || echo "后端: FAILED" >> /tmp/fix_502_status.txt
curl -s -o /dev/null -w '前端: %{http_code}\n' http://localhost:3000 >> /tmp/fix_502_status.txt 2>&1 || echo "前端: FAILED" >> /tmp/fix_502_status.txt
curl -s -o /dev/null -w '域名: %{http_code}\n' http://aikz.usdt2026.cc/group-ai/accounts >> /tmp/fix_502_status.txt 2>&1 || echo "域名: FAILED" >> /tmp/fix_502_status.txt

cat /tmp/fix_502_status.txt
