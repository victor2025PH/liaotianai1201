#!/bin/bash
# ============================================================
# 安全威胁检查脚本（检查是否中毒）
# ============================================================

set -e

echo "=========================================="
echo "🔒 安全威胁检查"
echo "=========================================="
echo ""

# 1. 检查可疑进程
echo "[1/8] 检查可疑进程..."
SUSPICIOUS_KEYWORDS=("miner" "crypto" "bitcoin" "monero" "xmrig" "stratum" "minerd" "cpuminer" "backdoor" "trojan" "virus" "malware")
THREATS_FOUND=false

for keyword in "${SUSPICIOUS_KEYWORDS[@]}"; do
    MATCHES=$(ps aux | grep -i "$keyword" | grep -v grep || true)
    if [ -n "$MATCHES" ]; then
        echo "  ⚠️  发现可疑进程 (关键词: '$keyword'):"
        echo "$MATCHES" | while read line; do
            PID=$(echo "$line" | awk '{print $2}')
            CMD=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
            USER=$(echo "$line" | awk '{print $1}')
            echo "    PID: $PID, 用户: $USER, 命令: $CMD"
        done
        THREATS_FOUND=true
    fi
done

if [ "$THREATS_FOUND" = false ]; then
    echo "  ✅ 未发现可疑进程"
fi
echo ""

# 2. 检查异常网络连接
echo "[2/8] 检查异常网络连接..."
echo "  检查连接到可疑 IP 的进程..."
SUSPICIOUS_IPS=$(ss -tunp 2>/dev/null | grep ESTAB | awk '{print $5}' | cut -d: -f1 | sort -u)
if [ -n "$SUSPICIOUS_IPS" ]; then
    echo "  活跃的外部连接:"
    echo "$SUSPICIOUS_IPS" | while read ip; do
        if [ -n "$ip" ] && [ "$ip" != "127.0.0.1" ] && [ "$ip" != "::1" ]; then
            CONN_COUNT=$(ss -tunp 2>/dev/null | grep "$ip" | wc -l)
            PROCESSES=$(ss -tunp 2>/dev/null | grep "$ip" | grep -oP 'pid=\K\d+' | sort -u | head -3)
            if [ -n "$PROCESSES" ]; then
                echo "    IP: $ip (连接数: $CONN_COUNT)"
                for pid in $PROCESSES; do
                    if [ -n "$pid" ]; then
                        CMD=$(ps -p "$pid" -o cmd --no-headers 2>/dev/null || echo "未知")
                        echo "      进程 PID $pid: $CMD" | head -c 80
                        echo ""
                    fi
                done
            fi
        fi
    done | head -20
fi
echo ""

# 3. 检查异常定时任务
echo "[3/8] 检查异常定时任务..."
CRON_JOBS=$(crontab -l 2>/dev/null || echo "")
if [ -n "$CRON_JOBS" ]; then
    SUSPICIOUS_CRON=$(echo "$CRON_JOBS" | grep -iE "curl.*http|wget.*http|bash.*http|sh.*http|python.*http" || true)
    if [ -n "$SUSPICIOUS_CRON" ]; then
        echo "  ⚠️  发现可疑的定时任务（包含网络下载）:"
        echo "$SUSPICIOUS_CRON" | sed 's/^/    /'
    else
        echo "  ✅ 未发现可疑的定时任务"
    fi
else
    echo "  ✅ 当前用户无定时任务"
fi

# 检查系统级定时任务
if [ -f /etc/crontab ]; then
    SUSPICIOUS_SYSTEM_CRON=$(grep -iE "curl.*http|wget.*http|bash.*http|sh.*http|python.*http" /etc/crontab 2>/dev/null || true)
    if [ -n "$SUSPICIOUS_SYSTEM_CRON" ]; then
        echo "  ⚠️  发现可疑的系统定时任务:"
        echo "$SUSPICIOUS_SYSTEM_CRON" | sed 's/^/    /'
    fi
fi
echo ""

# 4. 检查异常文件权限
echo "[4/8] 检查异常文件权限..."
echo "  检查 SUID/SGID 文件（可能被利用）:"
SUID_FILES=$(find /usr /bin /sbin /opt -type f -perm -4000 2>/dev/null | head -10)
if [ -n "$SUID_FILES" ]; then
    echo "  发现 SUID 文件:"
    echo "$SUID_FILES" | sed 's/^/    /'
else
    echo "  ✅ 未发现异常的 SUID 文件"
fi
echo ""

# 5. 检查异常登录记录
echo "[5/8] 检查异常登录记录..."
echo "  最近的登录记录:"
last -n 20 2>/dev/null | head -10 | awk '{printf "    %-12s %-15s %s %s %s\n", $1, $3, $4, $5, $6}'
echo ""
echo "  失败的登录尝试:"
grep "Failed password" /var/log/auth.log 2>/dev/null | tail -10 | awk '{print "    " $1 " " $2 " " $3 " - " $9 " from " $11}' || echo "    无失败登录记录"
echo ""

# 6. 检查异常系统调用
echo "[6/8] 检查异常系统调用..."
if command -v auditctl >/dev/null 2>&1; then
    AUDIT_ENABLED=$(auditctl -s 2>/dev/null | grep "enabled" || echo "disabled")
    echo "  审计系统状态: $AUDIT_ENABLED"
    if echo "$AUDIT_ENABLED" | grep -q "enabled"; then
        echo "  最近的异常系统调用:"
        ausearch -m SYSCALL -ts recent 2>/dev/null | head -10 | sed 's/^/    /' || echo "    无异常记录"
    fi
else
    echo "  ⚠️  auditd 未安装，无法检查系统调用"
fi
echo ""

# 7. 检查异常文件修改
echo "[7/8] 检查异常文件修改..."
echo "  最近修改的系统文件 (过去 24 小时):"
find /etc /usr/bin /usr/sbin -type f -mtime -1 2>/dev/null | head -10 | while read file; do
    if [ -f "$file" ]; then
        MOD_TIME=$(stat -c %y "$file" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1)
        echo "    $file (修改时间: $MOD_TIME)"
    fi
done
echo ""

# 8. 检查异常进程树
echo "[8/8] 检查异常进程树..."
echo "  检查隐藏进程（PPID 异常）:"
ps -eo pid,ppid,user,cmd --sort=-pid | awk 'NR>1 {
    if ($2 == 1 && $3 != "root" && $3 != "systemd") {
        printf "    PID:%-8s PPID:%-8s 用户:%-10s %s\n", $1, $2, $3, $4
    }
}' | head -10
echo ""

# 总结
echo "=========================================="
echo "安全检查总结"
echo "=========================================="
echo ""

if [ "$THREATS_FOUND" = true ]; then
    echo "⚠️  发现潜在安全威胁！"
    echo ""
    echo "建议立即采取以下措施："
    echo "  1. 终止可疑进程: kill -9 <PID>"
    echo "  2. 检查并删除可疑文件"
    echo "  3. 更改所有密码（包括 SSH、数据库等）"
    echo "  4. 检查并清理定时任务"
    echo "  5. 运行完整的安全扫描: sudo rkhunter --check"
    echo "  6. 检查系统完整性: sudo debsums -c"
    echo "  7. 考虑重新安装系统或从备份恢复"
else
    echo "✅ 未发现明显的安全威胁"
    echo ""
    echo "建议定期执行以下安全检查："
    echo "  1. 更新系统: sudo apt update && sudo apt upgrade"
    echo "  2. 运行安全扫描: sudo rkhunter --check"
    echo "  3. 检查系统完整性: sudo debsums -c"
    echo "  4. 查看登录日志: last"
    echo "  5. 检查异常网络连接: netstat -tunp"
fi
echo ""

