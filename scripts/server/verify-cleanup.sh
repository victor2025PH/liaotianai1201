#!/bin/bash
# ============================================================
# 验证清理结果脚本
# ============================================================

set -e

echo "=========================================="
echo "✅ 验证清理结果"
echo "=========================================="
echo ""

ALL_CLEAN=true

# 1. 检查可疑文件
echo "[1/5] 检查可疑文件..."
SUSPICIOUS_FILES=("/data/MUTA71VL" "/data/CX81yM9aE" "/data/UY")
FILES_FOUND=0

for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        FILES_FOUND=$((FILES_FOUND+1))
        ALL_CLEAN=false
        echo "  ❌ 发现可疑文件: $file"
        ls -lh "$file" | awk '{print "    大小: " $5 ", 权限: " $1 ", 修改时间: " $6 " " $7 " " $8}'
    fi
done

if [ "$FILES_FOUND" -eq 0 ]; then
    echo "  ✅ 未发现可疑文件"
fi
echo ""

# 2. 检查可疑进程
echo "[2/5] 检查可疑进程..."
PROCESSES_FOUND=$(ps aux | grep -E "MUTA71VL|CX81yM9aE|80.64.16.241|unk.sh" | grep -v grep | wc -l || echo "0")
if [ "$PROCESSES_FOUND" -gt 0 ]; then
    ALL_CLEAN=false
    echo "  ❌ 发现可疑进程:"
    ps aux | grep -E "MUTA71VL|CX81yM9aE|80.64.16.241|unk.sh" | grep -v grep | awk '{printf "    PID:%-8s CPU:%-6s MEM:%-6s %s\n", $2, $3"%", $4"%", $11}'
else
    echo "  ✅ 未发现可疑进程"
fi
echo ""

# 3. 检查恶意定时任务
echo "[3/5] 检查恶意定时任务..."
if crontab -l >/dev/null 2>&1; then
    MALICIOUS_CRON=$(crontab -l | grep -E "80.64.16.241|unk.sh" || true)
    if [ -n "$MALICIOUS_CRON" ]; then
        ALL_CLEAN=false
        echo "  ❌ 发现恶意定时任务:"
        echo "$MALICIOUS_CRON" | sed 's/^/    /'
    else
        echo "  ✅ 用户定时任务正常"
    fi
else
    echo "  ✅ 用户无定时任务"
fi

# 检查系统定时任务
if [ -f /etc/crontab ]; then
    SYSTEM_MALICIOUS=$(grep -E "80.64.16.241|unk.sh" /etc/crontab 2>/dev/null || true)
    if [ -n "$SYSTEM_MALICIOUS" ]; then
        ALL_CLEAN=false
        echo "  ❌ 发现恶意系统定时任务:"
        echo "$SYSTEM_MALICIOUS" | sed 's/^/    /'
    fi
fi
echo ""

# 4. 检查网络连接
echo "[4/5] 检查网络连接..."
SUSPICIOUS_IP="80.64.16.241"
CONNECTIONS=$(ss -tunp 2>/dev/null | grep "$SUSPICIOUS_IP" || true)
if [ -n "$CONNECTIONS" ]; then
    ALL_CLEAN=false
    echo "  ❌ 发现到可疑 IP 的连接:"
    echo "$CONNECTIONS" | sed 's/^/    /'
else
    echo "  ✅ 无到可疑 IP 的连接"
fi
echo ""

# 5. 检查系统资源
echo "[5/5] 检查系统资源..."
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | head -1)
if [ -n "$CPU_USAGE" ] && [ "$CPU_USAGE" != "0" ]; then
    CPU_PERCENT=$(echo "$CPU_USAGE" | awk '{printf "%.1f", 100 - $1}')
    if (( $(echo "$CPU_PERCENT > 90" | bc -l 2>/dev/null || echo "0") )); then
        echo "  ⚠️  CPU 使用率过高: ${CPU_PERCENT}%"
    else
        echo "  ✅ CPU 使用率正常: ${CPU_PERCENT}%"
    fi
else
    echo "  ✅ CPU 使用率正常"
fi

MEM_INFO=$(free | grep Mem)
MEM_TOTAL=$(echo "$MEM_INFO" | awk '{print $2}')
MEM_USED=$(echo "$MEM_INFO" | awk '{print $3}')
if [ "$MEM_TOTAL" -gt 0 ]; then
    MEM_PERCENT=$(echo "scale=2; $MEM_USED * 100 / $MEM_TOTAL" | bc 2>/dev/null || echo "0")
    MEM_INT=$(echo "$MEM_PERCENT" | cut -d. -f1)
    if [ "$MEM_INT" -gt 90 ]; then
        echo "  ⚠️  内存使用率过高: ${MEM_PERCENT}%"
    else
        echo "  ✅ 内存使用率正常: ${MEM_PERCENT}%"
    fi
fi
echo ""

# 总结
echo "=========================================="
if [ "$ALL_CLEAN" = true ]; then
    echo "✅ 清理验证通过"
    echo "=========================================="
    echo ""
    echo "系统已清理干净，建议："
    echo "  1. 更改所有密码"
    echo "  2. 定期运行安全扫描"
    echo "  3. 监控系统资源使用"
    echo "  4. 定期检查系统日志"
else
    echo "⚠️  清理验证未完全通过"
    echo "=========================================="
    echo ""
    echo "发现的问题："
    if [ "$FILES_FOUND" -gt 0 ]; then
        echo "  - 仍有 $FILES_FOUND 个可疑文件存在"
        echo "    运行强制删除: bash scripts/server/force-remove-malware.sh"
    fi
    if [ "$PROCESSES_FOUND" -gt 0 ]; then
        echo "  - 仍有 $PROCESSES_FOUND 个可疑进程运行"
        echo "    终止进程: sudo pkill -9 -f MUTA71VL"
    fi
    echo ""
    echo "请根据上述问题采取相应措施"
fi
echo ""

