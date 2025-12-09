#!/bin/bash
# 内存使用情况检查脚本

echo "=========================================="
echo "内存使用情况分析"
echo "=========================================="
echo ""

# 1. 系统总内存
echo "1. 系统内存信息"
echo "----------------------------------------"
free -h
echo ""

# 2. 内存使用最多的进程
echo "2. 内存使用最多的进程（前10个）"
echo "----------------------------------------"
ps aux --sort=-%mem | head -n 11
echo ""

# 3. PM2 进程内存使用
echo "3. PM2 进程内存使用"
echo "----------------------------------------"
if command -v pm2 >/dev/null 2>&1; then
    pm2 list
    echo ""
    pm2 describe backend 2>/dev/null | grep -E "memory|cpu" || echo "backend 进程不存在"
    echo ""
    pm2 describe frontend 2>/dev/null | grep -E "memory|cpu" || echo "frontend 进程不存在"
else
    echo "PM2 未安装"
fi
echo ""

# 4. Node.js 进程内存
echo "4. Node.js 进程内存使用"
echo "----------------------------------------"
ps aux | grep -E "node|npm" | grep -v grep | head -n 5
echo ""

# 5. Python 进程内存
echo "5. Python 进程内存使用"
echo "----------------------------------------"
ps aux | grep -E "python|uvicorn" | grep -v grep | head -n 5
echo ""

# 6. 系统负载
echo "6. 系统负载"
echo "----------------------------------------"
uptime
echo ""

# 7. Swap 使用情况
echo "7. Swap 使用情况"
echo "----------------------------------------"
swapon --show
echo ""

# 8. 磁盘使用情况
echo "8. 磁盘使用情况"
echo "----------------------------------------"
df -h | grep -E "Filesystem|/$"
echo ""

# 9. 内存使用统计
echo "9. 内存使用统计"
echo "----------------------------------------"
TOTAL_MEM=$(free -m | awk 'NR==2{print $2}')
USED_MEM=$(free -m | awk 'NR==2{print $3}')
AVAIL_MEM=$(free -m | awk 'NR==2{print $7}')
MEM_PERCENT=$((USED_MEM * 100 / TOTAL_MEM))

echo "总内存: ${TOTAL_MEM}MB"
echo "已使用: ${USED_MEM}MB"
echo "可用: ${AVAIL_MEM}MB"
echo "使用率: ${MEM_PERCENT}%"

if [ $MEM_PERCENT -gt 90 ]; then
    echo "⚠️  内存使用率超过 90%，建议清理或增加内存"
elif [ $MEM_PERCENT -gt 80 ]; then
    echo "⚠️  内存使用率超过 80%，建议监控"
else
    echo "✓ 内存使用率正常"
fi
echo ""

# 10. 检查大文件（可能占用内存的缓存文件）
echo "10. 检查可能占用内存的大文件"
echo "----------------------------------------"
echo "查找大于 100MB 的文件（前10个）:"
find /home/ubuntu/telegram-ai-system -type f -size +100M 2>/dev/null | head -n 10 || echo "未找到大文件"
echo ""

echo "=========================================="
echo "分析完成"
echo "=========================================="
echo ""
echo "建议："
echo "1. 如果内存使用率 > 90%，考虑增加 Swap 或清理进程"
echo "2. 如果 PM2 进程占用过多内存，考虑重启服务"
echo "3. 如果 Node.js 进程占用过多，检查是否有内存泄漏"
echo "4. 如果 Python 进程占用过多，检查是否有未释放的资源"
echo ""

