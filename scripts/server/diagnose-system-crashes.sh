#!/bin/bash
# ============================================================
# 服务器死机/重启问题诊断脚本
# ============================================================

set -e

echo "=========================================="
echo "🔍 服务器死机/重启问题诊断"
echo "=========================================="
echo ""

# 1. 系统基本信息
echo "[1/10] 系统基本信息..."
echo "  系统版本: $(lsb_release -d 2>/dev/null | cut -f2 || uname -a)"
echo "  内核版本: $(uname -r)"
echo "  运行时间: $(uptime -p 2>/dev/null || uptime | awk -F'up ' '{print $2}' | awk -F',' '{print $1}')"
echo "  最后启动: $(who -b 2>/dev/null | awk '{print $3, $4}' || date -d @$(awk '{print int($1)}' /proc/uptime) '+%Y-%m-%d %H:%M:%S')"
echo ""

# 2. 系统资源使用情况
echo "[2/10] 系统资源使用情况..."
echo "  CPU 使用率:"
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
echo "    当前: ${CPU_USAGE}%"
echo "  内存使用:"
free -h | grep -E "Mem|Swap" | awk '{print "    " $1 ": " $3 " / " $2 " (" $3/$2*100 "%)"}'
echo "  磁盘使用:"
df -h / | tail -1 | awk '{print "    根分区: " $3 " / " $2 " (" $5 " 已使用)"}'
echo "  系统负载:"
uptime | awk -F'load average:' '{print "    " $2}'
echo ""

# 3. 检查 OOM Killer（内存不足导致系统杀死进程）
echo "[3/10] 检查 OOM Killer 记录..."
if [ -f /var/log/kern.log ]; then
    OOM_COUNT=$(grep -c "Out of memory\|Killed process" /var/log/kern.log 2>/dev/null || echo "0")
    if [ "$OOM_COUNT" -gt 0 ]; then
        echo "  ⚠️  发现 $OOM_COUNT 条 OOM Killer 记录"
        echo "  最近的 OOM 事件:"
        grep "Out of memory\|Killed process" /var/log/kern.log 2>/dev/null | tail -5 | sed 's/^/    /'
    else
        echo "  ✅ 未发现 OOM Killer 记录"
    fi
elif [ -f /var/log/syslog ]; then
    OOM_COUNT=$(grep -c "Out of memory\|Killed process" /var/log/syslog 2>/dev/null || echo "0")
    if [ "$OOM_COUNT" -gt 0 ]; then
        echo "  ⚠️  发现 $OOM_COUNT 条 OOM Killer 记录"
        echo "  最近的 OOM 事件:"
        grep "Out of memory\|Killed process" /var/log/syslog 2>/dev/null | tail -5 | sed 's/^/    /'
    else
        echo "  ✅ 未发现 OOM Killer 记录"
    fi
else
    echo "  ⚠️  无法访问系统日志文件"
fi
echo ""

# 4. 检查系统崩溃日志
echo "[4/10] 检查系统崩溃日志..."
if [ -d /var/crash ]; then
    CRASH_COUNT=$(ls -1 /var/crash/*.crash 2>/dev/null | wc -l)
    if [ "$CRASH_COUNT" -gt 0 ]; then
        echo "  ⚠️  发现 $CRASH_COUNT 个崩溃文件"
        echo "  崩溃文件列表:"
        ls -lh /var/crash/*.crash 2>/dev/null | tail -5 | awk '{print "    " $9 " (" $5 ", " $6 " " $7 " " $8 ")"}'
    else
        echo "  ✅ 未发现崩溃文件"
    fi
else
    echo "  ✅ 未发现崩溃目录"
fi

# 检查 journalctl 中的崩溃记录
CRASH_LOGS=$(journalctl -p err -b -1 --no-pager 2>/dev/null | grep -i "crash\|panic\|segfault" | wc -l || echo "0")
if [ "$CRASH_LOGS" -gt 0 ]; then
    echo "  ⚠️  发现 $CRASH_LOGS 条崩溃相关日志"
    echo "  最近的崩溃日志:"
    journalctl -p err -b -1 --no-pager 2>/dev/null | grep -i "crash\|panic\|segfault" | tail -3 | sed 's/^/    /'
fi
echo ""

# 5. 检查系统错误日志
echo "[5/10] 检查系统错误日志..."
ERROR_COUNT=$(journalctl -p err --since "7 days ago" --no-pager 2>/dev/null | wc -l || echo "0")
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "  ⚠️  过去 7 天发现 $ERROR_COUNT 条错误日志"
    echo "  最近的错误:"
    journalctl -p err --since "24 hours ago" --no-pager 2>/dev/null | tail -10 | sed 's/^/    /'
else
    echo "  ✅ 过去 7 天未发现错误日志"
fi
echo ""

# 6. 检查异常进程（高 CPU/内存占用）
echo "[6/10] 检查异常进程..."
echo "  CPU 占用 Top 5:"
ps aux --sort=-%cpu | head -6 | tail -5 | awk '{printf "    %-20s PID:%-8s CPU:%-6s MEM:%-6s\n", $11, $2, $3"%", $4"%"}'
echo "  内存占用 Top 5:"
ps aux --sort=-%mem | head -6 | tail -5 | awk '{printf "    %-20s PID:%-8s CPU:%-6s MEM:%-6s\n", $11, $2, $3"%", $4"%"}'
echo ""

# 7. 检查可疑进程（可能的恶意软件）
echo "[7/10] 检查可疑进程..."
SUSPICIOUS_PATTERNS=("miner" "crypto" "bitcoin" "monero" "xmrig" "stratum" "minerd" "cpuminer")
SUSPICIOUS_FOUND=false
for pattern in "${SUSPICIOUS_PATTERNS[@]}"; do
    MATCHES=$(ps aux | grep -i "$pattern" | grep -v grep || true)
    if [ -n "$MATCHES" ]; then
        echo "  ⚠️  发现可疑进程 (包含 '$pattern'):"
        echo "$MATCHES" | awk '{printf "    PID:%-8s %s\n", $2, $11}'
        SUSPICIOUS_FOUND=true
    fi
done
if [ "$SUSPICIOUS_FOUND" = false ]; then
    echo "  ✅ 未发现明显的可疑进程"
fi
echo ""

# 8. 检查异常网络连接
echo "[8/10] 检查异常网络连接..."
echo "  活跃的网络连接数: $(ss -tun | wc -l)"
echo "  监听端口:"
ss -tlnp 2>/dev/null | grep LISTEN | awk '{print "    " $4}' | sort -u | head -10
echo "  异常的外部连接 (Top 10):"
ss -tunp 2>/dev/null | grep ESTAB | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -10 | awk '{printf "    %-15s %s 次连接\n", $2, $1}'
echo ""

# 9. 检查磁盘 I/O
echo "[9/10] 检查磁盘 I/O..."
if command -v iostat >/dev/null 2>&1; then
    echo "  磁盘 I/O 统计:"
    iostat -x 1 2 2>/dev/null | tail -n +4 | head -5 | awk '{if(NR>1) printf "    %-10s 读取:%-8s 写入:%-8s 利用率:%-6s\n", $1, $4"KB/s", $5"KB/s", $10"%"}'
else
    echo "  ⚠️  iostat 未安装，跳过磁盘 I/O 检查"
    echo "  安装命令: sudo apt-get install sysstat"
fi
echo ""

# 10. 检查系统服务状态
echo "[10/10] 检查系统服务状态..."
FAILED_SERVICES=$(systemctl --failed --no-legend 2>/dev/null | wc -l || echo "0")
if [ "$FAILED_SERVICES" -gt 0 ]; then
    echo "  ⚠️  发现 $FAILED_SERVICES 个失败的服务:"
    systemctl --failed --no-legend 2>/dev/null | awk '{print "    " $1}' | head -5
else
    echo "  ✅ 所有服务运行正常"
fi
echo ""

# 总结和建议
echo "=========================================="
echo "诊断总结"
echo "=========================================="
echo ""

# 生成建议
RECOMMENDATIONS=()

if [ "$OOM_COUNT" -gt 0 ]; then
    RECOMMENDATIONS+=("内存不足导致系统杀死进程，建议：1) 增加内存 2) 优化应用内存使用 3) 添加 swap 分区")
fi

if [ "$CRASH_COUNT" -gt 0 ] || [ "$CRASH_LOGS" -gt 0 ]; then
    RECOMMENDATIONS+=("发现系统崩溃记录，建议：1) 检查硬件（内存、硬盘） 2) 更新系统内核 3) 检查驱动兼容性")
fi

MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
if [ "$MEM_USAGE" -gt 90 ]; then
    RECOMMENDATIONS+=("内存使用率过高 (${MEM_USAGE}%)，可能导致系统不稳定，建议：1) 关闭不必要的服务 2) 优化应用内存使用 3) 增加内存")
fi

DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    RECOMMENDATIONS+=("磁盘使用率过高 (${DISK_USAGE}%)，可能导致系统问题，建议：1) 清理日志文件 2) 删除不必要的文件 3) 扩展磁盘空间")
fi

if [ "$SUSPICIOUS_FOUND" = true ]; then
    RECOMMENDATIONS+=("发现可疑进程，建议：1) 立即终止可疑进程 2) 检查系统是否被入侵 3) 运行安全扫描 4) 更改所有密码")
fi

if [ ${#RECOMMENDATIONS[@]} -eq 0 ]; then
    echo "✅ 未发现明显问题"
    echo ""
    echo "如果系统仍然频繁死机，建议："
    echo "  1. 检查硬件（内存、CPU、硬盘）是否有故障"
    echo "  2. 检查系统温度是否过高（过热保护）"
    echo "  3. 检查电源是否稳定"
    echo "  4. 查看完整的系统日志: journalctl -b -1 --no-pager"
    echo "  5. 运行硬件诊断工具: memtest86+ (内存), smartctl (硬盘)"
else
    echo "⚠️  发现以下问题："
    echo ""
    for i in "${!RECOMMENDATIONS[@]}"; do
        echo "  $((i+1)). ${RECOMMENDATIONS[$i]}"
    done
fi

echo ""
echo "=========================================="
echo "详细日志查看命令"
echo "=========================================="
echo "  查看系统日志: journalctl -b -1 --no-pager"
echo "  查看错误日志: journalctl -p err --since '7 days ago'"
echo "  查看崩溃日志: journalctl -k --since '7 days ago'"
echo "  查看 OOM 记录: grep -i 'out of memory' /var/log/kern.log"
echo "  查看系统负载历史: sar -u 1 10"
echo "  查看内存使用历史: sar -r 1 10"
echo ""

