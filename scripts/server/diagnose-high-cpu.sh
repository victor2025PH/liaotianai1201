#!/bin/bash
# ============================================================
# 诊断高 CPU 使用率问题
# ============================================================

set -e

echo "=========================================="
echo "🔍 诊断高 CPU 使用率问题"
echo "=========================================="
echo ""

# 1. 检查当前 CPU 使用率
echo "[1/6] 检查当前 CPU 使用率..."
echo "----------------------------------------"
echo "系统负载:"
uptime
echo ""

echo "CPU 使用率 (top 10 进程):"
ps aux --sort=-%cpu | head -11 | awk '{printf "%-8s %-8s %6s %6s %-s\n", $1, $2, $3"%", $4"%", $11}'
echo ""

# 2. 检查内存使用率
echo "[2/6] 检查内存使用率..."
echo "----------------------------------------"
free -h
echo ""

echo "内存使用率 (top 10 进程):"
ps aux --sort=-%mem | head -11 | awk '{printf "%-8s %-8s %6s %6s %-s\n", $1, $2, $3"%", $4"%", $11}'
echo ""

# 3. 检查 Nginx 进程
echo "[3/6] 检查 Nginx 进程..."
echo "----------------------------------------"
if pgrep -x nginx > /dev/null; then
    echo "✅ Nginx 进程正在运行"
    echo "Nginx 进程详情:"
    ps aux | grep nginx | grep -v grep
    echo ""
    echo "Nginx 进程数量: $(pgrep -c nginx)"
    echo "Nginx 总 CPU 使用率: $(ps aux | grep nginx | grep -v grep | awk '{sum+=$3} END {print sum"%"}')"
    echo "Nginx 总内存使用: $(ps aux | grep nginx | grep -v grep | awk '{sum+=$4} END {print sum"%"}')"
else
    echo "❌ Nginx 进程未运行"
fi
echo ""

# 4. 检查 PM2 进程
echo "[4/6] 检查 PM2 进程..."
echo "----------------------------------------"
if command -v pm2 &> /dev/null; then
    echo "PM2 进程列表:"
    pm2 list
    echo ""
    echo "PM2 进程详细信息:"
    pm2 jlist | jq -r '.[] | "\(.name): CPU=\(.monit.cpu)%, Memory=\(.monit.memory/1024/1024)MB"' 2>/dev/null || pm2 list
else
    echo "⚠️  PM2 未安装"
fi
echo ""

# 5. 检查系统资源
echo "[5/6] 检查系统资源..."
echo "----------------------------------------"
echo "磁盘使用情况:"
df -h | grep -E '^/dev|Filesystem'
echo ""

echo "网络连接数:"
echo "TCP 连接数: $(ss -s | grep TCP | awk '{print $2}')"
echo "ESTABLISHED 连接数: $(ss -s | grep ESTAB | awk '{print $2}')"
echo ""

# 6. 检查是否有异常进程
echo "[6/6] 检查异常进程..."
echo "----------------------------------------"
echo "CPU 使用率超过 50% 的进程:"
HIGH_CPU=$(ps aux --sort=-%cpu | awk 'NR>1 && $3>50 {print $2, $3"%", $4"%", $11}')
if [ -n "$HIGH_CPU" ]; then
    echo "$HIGH_CPU"
    echo ""
    echo "⚠️  发现高 CPU 使用进程，建议检查："
    echo "   1. 是否有进程陷入死循环"
    echo "   2. 是否有恶意进程"
    echo "   3. 服务是否正常响应"
else
    echo "✅ 未发现异常高 CPU 进程"
fi
echo ""

# 7. 检查 Nginx 错误日志
echo "检查 Nginx 错误日志（最近 20 行）..."
echo "----------------------------------------"
if [ -f /var/log/nginx/error.log ]; then
    echo "最近的错误:"
    sudo tail -20 /var/log/nginx/error.log | grep -i error || echo "无错误日志"
else
    echo "⚠️  Nginx 错误日志不存在"
fi
echo ""

# 8. 检查系统日志
echo "检查系统日志（最近 10 行关键信息）..."
echo "----------------------------------------"
if command -v journalctl &> /dev/null; then
    echo "最近的系统错误:"
    sudo journalctl -p err -n 10 --no-pager 2>/dev/null || echo "无法读取系统日志"
else
    echo "⚠️  journalctl 不可用"
fi
echo ""

echo "=========================================="
echo "✅ 诊断完成"
echo "=========================================="
echo ""
echo "如果发现高 CPU 使用进程，可以："
echo "  1. 查看进程详情: ps aux | grep <PID>"
echo "  2. 查看进程线程: top -H -p <PID>"
echo "  3. 重启服务: pm2 restart all"
echo "  4. 重启 Nginx: sudo systemctl restart nginx"
echo ""

