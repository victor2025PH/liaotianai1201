#!/bin/bash
# ============================================================
# 修复高 CPU 使用率问题
# ============================================================

set -e

echo "=========================================="
echo "🔧 修复高 CPU 使用率问题"
echo "=========================================="
echo ""

# 1. 检查并重启 Nginx
echo "[1/4] 检查并重启 Nginx..."
echo "----------------------------------------"
if systemctl is-active --quiet nginx; then
    echo "重启 Nginx..."
    sudo systemctl restart nginx
    sleep 2
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已重启"
    else
        echo "❌ Nginx 重启失败"
    fi
else
    echo "启动 Nginx..."
    sudo systemctl start nginx
fi
echo ""

# 2. 检查并重启 PM2 服务
echo "[2/4] 检查并重启 PM2 服务..."
echo "----------------------------------------"
if command -v pm2 &> /dev/null; then
    echo "重启所有 PM2 进程..."
    pm2 restart all
    sleep 3
    echo "✅ PM2 服务已重启"
    pm2 list
else
    echo "⚠️  PM2 未安装"
fi
echo ""

# 3. 检查是否有僵尸进程
echo "[3/4] 检查僵尸进程..."
echo "----------------------------------------"
ZOMBIE_COUNT=$(ps aux | awk '$8 ~ /^Z/ {count++} END {print count+0}')
if [ "$ZOMBIE_COUNT" -gt 0 ]; then
    echo "⚠️  发现 $ZOMBIE_COUNT 个僵尸进程"
    echo "僵尸进程列表:"
    ps aux | awk '$8 ~ /^Z/ {print $2, $11}'
    echo "建议重启相关服务"
else
    echo "✅ 未发现僵尸进程"
fi
echo ""

# 4. 等待并检查 CPU 使用率
echo "[4/4] 等待并检查 CPU 使用率..."
echo "----------------------------------------"
echo "等待 5 秒后检查 CPU 使用率..."
sleep 5

echo "当前 CPU 使用率 (top 5):"
ps aux --sort=-%cpu | head -6 | awk '{printf "%-8s %6s %-s\n", $2, $3"%", $11}'
echo ""

CURRENT_CPU=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
echo "系统总体 CPU 使用率: ${CURRENT_CPU}%"

if (( $(echo "$CURRENT_CPU > 80" | bc -l) )); then
    echo "⚠️  CPU 使用率仍然很高 (${CURRENT_CPU}%)"
    echo "建议："
    echo "  1. 运行诊断脚本: sudo bash scripts/server/diagnose-high-cpu.sh"
    echo "  2. 检查是否有异常进程"
    echo "  3. 考虑重启服务器"
else
    echo "✅ CPU 使用率已恢复正常"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""

