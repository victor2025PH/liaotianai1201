#!/bin/bash
# ============================================================
# 追踪可疑文件的来源
# ============================================================

set +e

echo "=========================================="
echo "🔍 追踪可疑文件来源"
echo "=========================================="
echo ""

SUSPICIOUS_FILES=("/data/4pVffo7" "/data/T1ID" "/data/ZaAxbGP")

echo "[1/8] 检查文件创建时间线..."
echo ""
for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📄 文件: $file"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # 文件时间戳
        echo "时间戳信息:"
        stat "$file" 2>/dev/null | grep -E "Modify|Change|Birth" | sed 's/^/  /'
        
        # 检查 inode 创建时间（如果支持）
        if stat -c "%w" "$file" 2>/dev/null | grep -qv "^$"; then
            echo "  创建时间: $(stat -c "%w" "$file" 2>/dev/null)"
        fi
        echo ""
    fi
done

echo "[2/8] 检查是否有进程正在创建这些文件..."
echo ""
# 使用 inotifywait 监控（如果可用）
if command -v inotifywait >/dev/null 2>&1; then
    echo "  使用 inotifywait 监控 /data/ 目录（10秒）..."
    timeout 10 inotifywait -m /data/ -e create,modify 2>&1 | head -20 &
    INOTIFY_PID=$!
    sleep 10
    kill $INOTIFY_PID 2>/dev/null || true
else
    echo "  ⚠️  inotifywait 未安装，跳过实时监控"
fi
echo ""

echo "[3/8] 检查系统日志中的文件创建记录..."
echo ""
for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        FILE_NAME=$(basename "$file")
        echo "  搜索 $FILE_NAME 相关日志:"
        
        # 检查 syslog
        sudo journalctl -x --since "24 hours ago" 2>/dev/null | grep -i "$FILE_NAME" | tail -10 | sed 's/^/    /' || echo "    未找到相关日志"
        
        # 检查 auth.log
        if [ -f /var/log/auth.log ]; then
            sudo grep -i "$FILE_NAME" /var/log/auth.log 2>/dev/null | tail -5 | sed 's/^/    /' || true
        fi
        
        # 检查 messages
        if [ -f /var/log/messages ]; then
            sudo grep -i "$FILE_NAME" /var/log/messages 2>/dev/null | tail -5 | sed 's/^/    /' || true
        fi
        echo ""
    fi
done

echo "[4/8] 检查定时任务（cron）..."
echo ""
echo "  用户定时任务:"
crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$" | sed 's/^/    /' || echo "    无用户定时任务"

echo ""
echo "  系统定时任务 (/etc/crontab):"
sudo cat /etc/crontab 2>/dev/null | grep -v "^#" | grep -v "^$" | sed 's/^/    /' || echo "    无系统定时任务"

echo ""
echo "  /etc/cron.d/ 目录:"
sudo ls -la /etc/cron.d/ 2>/dev/null | sed 's/^/    /' || echo "    无法访问"

echo ""
echo "  /etc/cron.daily/ 目录:"
sudo ls -la /etc/cron.daily/ 2>/dev/null | sed 's/^/    /' || echo "    无法访问"

echo ""
echo "  /etc/cron.hourly/ 目录:"
sudo ls -la /etc/cron.hourly/ 2>/dev/null | sed 's/^/    /' || echo "    无法访问"

echo ""
echo "  所有 cron 任务内容（搜索可疑关键词）:"
for cron_file in /etc/crontab /etc/cron.d/* /etc/cron.daily/* /etc/cron.hourly/* /etc/cron.weekly/* /etc/cron.monthly/*; do
    if [ -f "$cron_file" ] 2>/dev/null; then
        SUSPICIOUS=$(grep -E "80.64.16.241|unk.sh|/data/|curl.*http|wget.*http" "$cron_file" 2>/dev/null || true)
        if [ -n "$SUSPICIOUS" ]; then
            echo "    ❌ 发现可疑内容 in $cron_file:"
            echo "$SUSPICIOUS" | sed 's/^/      /'
        fi
    fi
done
echo ""

echo "[5/8] 检查 systemd 服务和定时器..."
echo ""
echo "  启用的定时器:"
systemctl list-unit-files | grep enabled | grep timer | sed 's/^/    /' || echo "    无启用的定时器"

echo ""
echo "  所有 systemd 服务（搜索可疑关键词）:"
for service_file in /etc/systemd/system/*.service /lib/systemd/system/*.service /usr/lib/systemd/system/*.service; do
    if [ -f "$service_file" ] 2>/dev/null; then
        SUSPICIOUS=$(grep -E "80.64.16.241|unk.sh|/data/|curl.*http|wget.*http" "$service_file" 2>/dev/null || true)
        if [ -n "$SUSPICIOUS" ]; then
            echo "    ❌ 发现可疑内容 in $service_file:"
            echo "$SUSPICIOUS" | sed 's/^/      /'
        fi
    fi
done
echo ""

echo "[6/8] 检查启动脚本..."
echo ""
echo "  /etc/rc.local:"
if [ -f /etc/rc.local ]; then
    cat /etc/rc.local | grep -v "^#" | grep -v "^$" | sed 's/^/    /' || echo "    空文件"
else
    echo "    文件不存在"
fi

echo ""
echo "  ~/.bashrc:"
if [ -f ~/.bashrc ]; then
    grep -E "80.64.16.241|unk.sh|/data/|curl.*http|wget.*http" ~/.bashrc 2>/dev/null | sed 's/^/    /' || echo "    未发现可疑内容"
fi

echo ""
echo "  ~/.bash_profile:"
if [ -f ~/.bash_profile ]; then
    grep -E "80.64.16.241|unk.sh|/data/|curl.*http|wget.*http" ~/.bash_profile 2>/dev/null | sed 's/^/    /' || echo "    未发现可疑内容"
fi

echo ""
echo "  ~/.profile:"
if [ -f ~/.profile ]; then
    grep -E "80.64.16.241|unk.sh|/data/|curl.*http|wget.*http" ~/.profile 2>/dev/null | sed 's/^/    /' || echo "    未发现可疑内容"
fi

echo ""
echo "  /etc/profile:"
if [ -f /etc/profile ]; then
    sudo grep -E "80.64.16.241|unk.sh|/data/|curl.*http|wget.*http" /etc/profile 2>/dev/null | sed 's/^/    /' || echo "    未发现可疑内容"
fi
echo ""

echo "[7/8] 检查网络连接和下载活动..."
echo ""
echo "  检查是否有进程正在下载文件:"
ps aux | grep -E "curl|wget|nc|netcat" | grep -v grep | sed 's/^/    /' || echo "    未发现下载进程"

echo ""
echo "  检查到可疑 IP 的连接:"
SUSPICIOUS_IP="80.64.16.241"
ss -tunp 2>/dev/null | grep "$SUSPICIOUS_IP" | sed 's/^/    /' || echo "    无到可疑 IP 的连接"

echo ""
echo "  检查所有网络连接:"
ss -tunp 2>/dev/null | head -20 | sed 's/^/    /'
echo ""

echo "[8/8] 检查文件系统监控（auditd）..."
echo ""
if command -v ausearch >/dev/null 2>&1; then
    echo "  使用 auditd 查询文件创建记录:"
    for file in "${SUSPICIOUS_FILES[@]}"; do
        if [ -f "$file" ]; then
            FILE_NAME=$(basename "$file")
            sudo ausearch -f "$file" 2>/dev/null | head -10 | sed 's/^/    /' || echo "    未找到 audit 记录"
        fi
    done
else
    echo "  ⚠️  auditd 未安装，无法使用审计日志"
fi
echo ""

echo "=========================================="
echo "📊 追踪总结"
echo "=========================================="
echo ""
echo "建议检查项:"
echo "  1. 检查所有定时任务（cron）"
echo "  2. 检查 systemd 服务和定时器"
echo "  3. 检查启动脚本（rc.local, .bashrc 等）"
echo "  4. 检查网络连接和下载活动"
echo "  5. 监控 /data/ 目录的文件创建"
echo ""
echo "如果文件被持续重新创建，可能的原因:"
echo "  - 定时任务（cron）在定期下载/创建文件"
echo "  - systemd 服务或定时器在运行恶意脚本"
echo "  - 启动脚本在系统启动时创建文件"
echo "  - 有隐藏进程在监控并重新创建文件"
echo ""
echo "下一步操作:"
echo "  1. 运行: bash scripts/server/analyze-suspicious-files.sh"
echo "  2. 运行: bash scripts/server/delete-new-malware-files.sh"
echo "  3. 删除所有可疑的定时任务和服务"
echo "  4. 监控系统，看文件是否重新出现"
echo ""

