#!/bin/bash
# 诊断502问题 - 在远程服务器上执行
# 执行位置: ubuntu@165.154.233.55

set -e

OUTPUT_FILE="/tmp/diagnose_502_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee "$OUTPUT_FILE") 2>&1

echo "========================================="
echo "诊断 502 Bad Gateway 问题"
echo "开始时间: $(date)"
echo "========================================="
echo ""

# 1. 检查前端服务状态
echo "【步骤1】检查前端服务状态"
echo "─────────────────────────────────────────"
cd ~/liaotian/saas-demo

echo "1.1 检查进程:"
ps aux | grep -E 'next.*dev|node.*3000' | grep -v grep || echo "  ✗ 无前端进程"
echo ""

echo "1.2 检查端口3000:"
if sudo ss -tlnp | grep -q ':3000 '; then
    echo "  ✓ 端口3000正在监听"
    sudo ss -tlnp | grep ':3000 '
else
    echo "  ✗ 端口3000未监听"
fi
echo ""

echo "1.3 测试本地连接:"
curl -I http://localhost:3000 2>&1 | head -5 || echo "  ✗ 连接失败"
echo ""

# 2. 查看前端日志
echo "【步骤2】查看前端日志"
echo "─────────────────────────────────────────"
if [ -f /tmp/frontend.log ]; then
    echo "日志文件存在，最后100行:"
    tail -100 /tmp/frontend.log
else
    echo "  ✗ 日志文件不存在"
fi
echo ""

# 3. 检查配置
echo "【步骤3】检查配置"
echo "─────────────────────────────────────────"
echo "3.1 package.json dev脚本:"
grep -A 1 '"dev"' package.json || echo "  未找到dev脚本"
echo ""

echo "3.2 Node.js版本:"
node -v || echo "  ✗ Node.js未安装"
echo ""

echo "3.3 npm版本:"
npm -v || echo "  ✗ npm未安装"
echo ""

echo "3.4 检查node_modules:"
if [ -d node_modules ]; then
    echo "  ✓ node_modules目录存在"
    MODULE_COUNT=$(ls node_modules 2>/dev/null | wc -l)
    echo "  模块数量: $MODULE_COUNT"
else
    echo "  ✗ node_modules目录不存在"
fi
echo ""

# 4. 前台运行捕获错误
echo "【步骤4】前台运行npm run dev（捕获错误）"
echo "─────────────────────────────────────────"
echo "4.1 停止旧进程..."
pkill -f "next.*dev|node.*3000" 2>/dev/null || echo "  没有旧进程"
sleep 2
echo ""

echo "4.2 前台运行npm run dev（30秒超时）..."
cd ~/liaotian/saas-demo
timeout 30 npm run dev 2>&1 | tee /tmp/frontend_direct_output.log || {
    EXIT_CODE=$?
    echo ""
    echo "进程退出，退出码: $EXIT_CODE"
    echo ""
    echo "完整输出:"
    cat /tmp/frontend_direct_output.log
}

echo ""
echo "========================================="
echo "诊断完成"
echo "输出已保存到: $OUTPUT_FILE"
echo "========================================="
