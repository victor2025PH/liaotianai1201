#!/bin/bash
# ============================================================
# 删除恶意定时任务脚本
# ============================================================

set -e

echo "=========================================="
echo "🗑️  删除恶意定时任务"
echo "=========================================="
echo ""

# 恶意定时任务模式
MALICIOUS_PATTERNS=("80.64.16.241" "unk.sh" "wget.*http.*sh" "curl.*http.*sh")

# 1. 清理用户定时任务
echo "[1/4] 清理用户定时任务..."
if crontab -l >/dev/null 2>&1; then
    CRON_CONTENT=$(crontab -l)
    BACKUP_FILE="/tmp/user_crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
    
    # 备份
    echo "$CRON_CONTENT" > "$BACKUP_FILE"
    echo "  已备份到: $BACKUP_FILE"
    
    # 检查是否有恶意任务
    MALICIOUS_FOUND=false
    for pattern in "${MALICIOUS_PATTERNS[@]}"; do
        if echo "$CRON_CONTENT" | grep -qE "$pattern"; then
            MALICIOUS_FOUND=true
            echo "  ⚠️  发现恶意定时任务:"
            echo "$CRON_CONTENT" | grep -E "$pattern" | sed 's/^/    /'
        fi
    done
    
    if [ "$MALICIOUS_FOUND" = true ]; then
        # 删除恶意任务
        NEW_CRON=$(echo "$CRON_CONTENT" | grep -vE "$(IFS='|'; echo "${MALICIOUS_PATTERNS[*]}")")
        echo "$NEW_CRON" | crontab -
        echo "  ✅ 已删除恶意定时任务"
    else
        echo "  ✅ 未发现恶意定时任务"
    fi
else
    echo "  ✅ 用户无定时任务"
fi
echo ""

# 2. 检查系统定时任务文件
echo "[2/4] 检查系统定时任务文件..."
if [ -f /etc/crontab ]; then
    SYSTEM_MALICIOUS=$(grep -E "$(IFS='|'; echo "${MALICIOUS_PATTERNS[*]}")" /etc/crontab 2>/dev/null || true)
    if [ -n "$SYSTEM_MALICIOUS" ]; then
        echo "  ⚠️  发现恶意系统定时任务:"
        echo "$SYSTEM_MALICIOUS" | sed 's/^/    /'
        echo "  请手动编辑 /etc/crontab 删除恶意任务"
        echo "  命令: sudo nano /etc/crontab"
    else
        echo "  ✅ /etc/crontab 正常"
    fi
fi
echo ""

# 3. 检查 /etc/cron.d/ 目录
echo "[3/4] 检查 /etc/cron.d/ 目录..."
if [ -d /etc/cron.d ]; then
    MALICIOUS_FILES_FOUND=false
    for cron_file in /etc/cron.d/*; do
        if [ -f "$cron_file" ] && [ "$(basename "$cron_file")" != ".placeholder" ]; then
            FILE_CONTENT=$(cat "$cron_file" 2>/dev/null || echo "")
            for pattern in "${MALICIOUS_PATTERNS[@]}"; do
                if echo "$FILE_CONTENT" | grep -qE "$pattern"; then
                    MALICIOUS_FILES_FOUND=true
                    echo "  ⚠️  发现恶意定时任务文件: $cron_file"
                    echo "$FILE_CONTENT" | grep -E "$pattern" | sed 's/^/    /'
                    echo "  建议删除: sudo rm -f $cron_file"
                fi
            done
        fi
    done
    
    if [ "$MALICIOUS_FILES_FOUND" = false ]; then
        echo "  ✅ /etc/cron.d/ 目录正常"
    fi
fi
echo ""

# 4. 检查定时任务目录
echo "[4/4] 检查定时任务目录..."
CRON_DIRS=("/etc/cron.hourly" "/etc/cron.daily" "/etc/cron.weekly" "/etc/cron.monthly")
MALICIOUS_SCRIPTS_FOUND=false

for dir in "${CRON_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        for script in "$dir"/*; do
            if [ -f "$script" ] && [ "$(basename "$script")" != ".placeholder" ]; then
                SCRIPT_CONTENT=$(cat "$script" 2>/dev/null || echo "")
                for pattern in "${MALICIOUS_PATTERNS[@]}"; do
                    if echo "$SCRIPT_CONTENT" | grep -qE "$pattern"; then
                        MALICIOUS_SCRIPTS_FOUND=true
                        echo "  ⚠️  发现恶意脚本: $script"
                        echo "$SCRIPT_CONTENT" | grep -E "$pattern" | sed 's/^/    /'
                        echo "  建议删除: sudo rm -f $script"
                    fi
                done
            fi
        done
    fi
done

if [ "$MALICIOUS_SCRIPTS_FOUND" = false ]; then
    echo "  ✅ 定时任务目录正常"
fi
echo ""

# 总结
echo "=========================================="
echo "清理完成"
echo "=========================================="
echo ""
echo "建议验证:"
echo "  1. 查看当前用户定时任务: crontab -l"
echo "  2. 查看系统定时任务: sudo cat /etc/crontab"
echo "  3. 查看定时任务目录: sudo ls -la /etc/cron.d/"
echo "  4. 监控系统，确保恶意任务不再执行"
echo ""

