#!/bin/bash
# 诊断 PM2 被杀死的问题

echo "=========================================="
echo "PM2 被杀死问题诊断"
echo "=========================================="
echo ""

# 1. 检查系统资源限制
echo "1. 检查系统资源限制"
echo "----------------------------------------"
ulimit -a
echo ""

# 2. 检查内存
echo "2. 检查内存使用"
echo "----------------------------------------"
free -h
echo ""

# 3. 检查 Swap
echo "3. 检查 Swap"
echo "----------------------------------------"
swapon --show
echo ""

# 4. 检查进程
echo "4. 检查 Node.js 和 PM2 进程"
echo "----------------------------------------"
ps aux | grep -E "node|pm2" | grep -v grep || echo "没有相关进程"
echo ""

# 5. 检查 PM2 安装
echo "5. 检查 PM2 安装"
echo "----------------------------------------"
which pm2 || echo "PM2 未找到"
pm2 --version 2>/dev/null || echo "PM2 无法执行"
echo ""

# 6. 检查 Node.js
echo "6. 检查 Node.js"
echo "----------------------------------------"
which node || echo "Node.js 未找到"
node --version 2>/dev/null || echo "Node.js 无法执行"
echo ""

# 7. 检查系统日志
echo "7. 检查最近的系统日志（OOM 相关）"
echo "----------------------------------------"
sudo dmesg | grep -i "killed\|oom" | tail -n 10 2>/dev/null || echo "无法查看系统日志"
echo ""

# 8. 检查磁盘空间
echo "8. 检查磁盘空间"
echo "----------------------------------------"
df -h / | tail -n 1
echo ""

echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "如果 PM2 无法执行，可能的原因："
echo "1. 内存不足（即使显示正常，实际可用内存可能不足）"
echo "2. 系统资源限制（ulimit）"
echo "3. PM2 安装损坏"
echo "4. Node.js 环境问题"
echo ""

