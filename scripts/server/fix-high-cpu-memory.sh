#!/bin/bash
# ============================================================
# 修复高 CPU/内存使用问题
# ============================================================

set -e

echo "=========================================="
echo "🔧 修复高 CPU/内存使用问题"
echo "=========================================="
echo ""

# 1. 检查高 CPU 占用的进程
echo "[1/6] 检查高 CPU 占用的进程..."
echo "  CPU 占用 Top 10:"
ps aux --sort=-%cpu | head -11 | tail -10 | awk '{printf "    %-20s PID:%-8s CPU:%-6s MEM:%-6s\n", $11, $2, $3"%", $4"%"}'
echo ""

# 2. 检查高内存占用的进程
echo "[2/6] 检查高内存占用的进程..."
echo "  内存占用 Top 10:"
ps aux --sort=-%mem | head -11 | tail -10 | awk '{printf "    %-20s PID:%-8s CPU:%-6s MEM:%-6s\n", $11, $2, $3"%", $4"%"}'
echo ""

# 3. 检查可疑进程
echo "[3/6] 检查可疑进程..."
SUSPICIOUS_PROCESSES=$(ps aux | grep -iE "MUTA71VL|CX81yM9aE|miner|crypto|bitcoin|monero" | grep -v grep || true)
if [ -n "$SUSPICIOUS_PROCESSES" ]; then
    echo "  ⚠️  发现可疑进程，建议终止:"
    echo "$SUSPICIOUS_PROCESSES" | while read line; do
        PID=$(echo "$line" | awk '{print $2}')
        CMD=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
        CPU=$(echo "$line" | awk '{print $3}')
        MEM=$(echo "$line" | awk '{print $4}')
        echo "    PID: $PID, CPU: ${CPU}%, MEM: ${MEM}%"
        echo "    命令: $CMD"
        echo "    终止命令: sudo kill -9 $PID"
    done
else
    echo "  ✅ 未发现明显的可疑进程"
fi
echo ""

# 4. 检查系统负载
echo "[4/6] 检查系统负载..."
LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}')
CPU_CORES=$(nproc)
LOAD_1=$(echo "$LOAD_AVG" | awk '{print $1}' | sed 's/,//')
LOAD_THRESHOLD=$(echo "$CPU_CORES * 2" | bc)

echo "  系统负载: $LOAD_AVG"
echo "  CPU 核心数: $CPU_CORES"
if (( $(echo "$LOAD_1 > $LOAD_THRESHOLD" | bc -l) )); then
    echo "  ⚠️  系统负载过高！"
else
    echo "  ✅ 系统负载正常"
fi
echo ""

# 5. 检查内存使用
echo "[5/6] 检查内存使用..."
MEM_INFO=$(free -m)
MEM_TOTAL=$(echo "$MEM_INFO" | grep Mem | awk '{print $2}')
MEM_USED=$(echo "$MEM_INFO" | grep Mem | awk '{print $3}')
MEM_PERCENT=$(echo "scale=2; $MEM_USED * 100 / $MEM_TOTAL" | bc)

echo "  总内存: ${MEM_TOTAL}MB"
echo "  已使用: ${MEM_USED}MB (${MEM_PERCENT}%)"
if (( $(echo "$MEM_PERCENT > 90" | bc -l) )); then
    echo "  ⚠️  内存使用率过高！"
    echo "  建议:"
    echo "    1. 终止不必要的进程"
    echo "    2. 增加 swap 空间"
    echo "    3. 优化应用内存使用"
else
    echo "  ✅ 内存使用正常"
fi
echo ""

# 6. 提供修复建议
echo "[6/6] 修复建议..."
echo ""

# 检查是否需要终止可疑进程
if [ -n "$SUSPICIOUS_PROCESSES" ]; then
    echo "⚠️  发现可疑进程，建议立即终止:"
    echo "$SUSPICIOUS_PROCESSES" | while read line; do
        PID=$(echo "$line" | awk '{print $2}')
        echo "  sudo kill -9 $PID"
    done
    echo ""
fi

# 检查是否需要增加 swap
if (( $(echo "$MEM_PERCENT > 85" | bc -l) )); then
    SWAP_TOTAL=$(echo "$MEM_INFO" | grep Swap | awk '{print $2}')
    if [ "$SWAP_TOTAL" -eq 0 ]; then
        echo "⚠️  内存使用率高且无 swap，建议添加 swap:"
        echo "  sudo fallocate -l 4G /swapfile"
        echo "  sudo chmod 600 /swapfile"
        echo "  sudo mkswap /swapfile"
        echo "  sudo swapon /swapfile"
        echo "  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab"
        echo ""
    fi
fi

# 检查是否需要重启服务
echo "如果问题持续，可以尝试："
echo "  1. 重启高资源占用的服务:"
echo "     sudo systemctl restart luckyred-api"
echo "     sudo systemctl restart telegram-bot"
echo ""
echo "  2. 清理系统缓存:"
echo "     sudo sync"
echo "     echo 3 | sudo tee /proc/sys/vm/drop_caches"
echo ""
echo "  3. 检查并优化应用配置"
echo ""

echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""

