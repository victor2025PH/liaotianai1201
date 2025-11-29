#!/bin/bash
# 分步诊断502问题 - 每一步结果都保存到文件

cd ~/liaotian/saas-demo

# 步骤1: 检查进程和端口
echo "=== 步骤1: 检查前端进程 ===" > /tmp/diagnose_step1.txt
ps aux | grep -E 'next.*dev|node.*3000' | grep -v grep >> /tmp/diagnose_step1.txt 2>&1 || echo "无进程" >> /tmp/diagnose_step1.txt
echo "" >> /tmp/diagnose_step1.txt
echo "=== 检查端口3000 ===" >> /tmp/diagnose_step1.txt
sudo ss -tlnp | grep 3000 >> /tmp/diagnose_step1.txt 2>&1 || echo "端口未监听" >> /tmp/diagnose_step1.txt

# 步骤2: 查看日志
echo "=== 前端日志最后100行 ===" > /tmp/diagnose_step2.txt
if [ -f /tmp/frontend.log ]; then
    tail -100 /tmp/frontend.log >> /tmp/diagnose_step2.txt
else
    echo "日志文件不存在" >> /tmp/diagnose_step2.txt
fi

# 步骤3: 检查配置
echo "=== package.json dev脚本 ===" > /tmp/diagnose_step3.txt
grep -A 1 '"dev"' package.json >> /tmp/diagnose_step3.txt 2>&1 || echo "未找到" >> /tmp/diagnose_step3.txt
echo "" >> /tmp/diagnose_step3.txt
echo "=== Node.js版本 ===" >> /tmp/diagnose_step3.txt
node -v >> /tmp/diagnose_step3.txt 2>&1 || echo "未安装" >> /tmp/diagnose_step3.txt
echo "" >> /tmp/diagnose_step3.txt
echo "=== npm版本 ===" >> /tmp/diagnose_step3.txt
npm -v >> /tmp/diagnose_step3.txt 2>&1 || echo "未安装" >> /tmp/diagnose_step3.txt
echo "" >> /tmp/diagnose_step3.txt
echo "=== node_modules检查 ===" >> /tmp/diagnose_step3.txt
if [ -d node_modules ] && [ -f node_modules/.bin/next ]; then
    echo "node_modules和Next.js存在" >> /tmp/diagnose_step3.txt
else
    echo "node_modules或Next.js不存在" >> /tmp/diagnose_step3.txt
fi

# 步骤4: 停止旧进程并前台运行
echo "=== 停止旧进程 ===" > /tmp/diagnose_step4.txt
pkill -f "next.*dev|node.*3000" >> /tmp/diagnose_step4.txt 2>&1 || echo "无进程需要停止" >> /tmp/diagnose_step4.txt
sleep 2

echo "=== 前台运行npm run dev（30秒） ===" >> /tmp/diagnose_step4.txt
timeout 30 npm run dev >> /tmp/diagnose_step4.txt 2>&1 || echo "进程退出或超时" >> /tmp/diagnose_step4.txt

# 步骤5: 测试连接
echo "=== 测试后端连接 ===" > /tmp/diagnose_step5.txt
curl -s -o /dev/null -w '后端健康检查: %{http_code}\n' http://localhost:8000/health >> /tmp/diagnose_step5.txt 2>&1 || echo "后端连接失败" >> /tmp/diagnose_step5.txt
echo "" >> /tmp/diagnose_step5.txt
echo "=== 测试前端连接 ===" >> /tmp/diagnose_step5.txt
curl -s -o /dev/null -w '前端服务: %{http_code}\n' http://localhost:3000 >> /tmp/diagnose_step5.txt 2>&1 || echo "前端连接失败" >> /tmp/diagnose_step5.txt
echo "" >> /tmp/diagnose_step5.txt
echo "=== 测试域名连接 ===" >> /tmp/diagnose_step5.txt
curl -s -o /dev/null -w '域名访问: %{http_code}\n' http://aikz.usdt2026.cc/group-ai/accounts >> /tmp/diagnose_step5.txt 2>&1 || echo "域名连接失败" >> /tmp/diagnose_step5.txt

echo "诊断完成，结果已保存到 /tmp/diagnose_step*.txt"
