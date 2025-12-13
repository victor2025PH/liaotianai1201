#!/bin/bash
# ============================================================
# 检查可疑文件脚本
# ============================================================

set -e

echo "=========================================="
echo "🔍 检查可疑文件"
echo "=========================================="
echo ""

# 1. 检查 /data 目录下的可疑文件
echo "[1/5] 检查 /data 目录..."
if [ -d "/data" ]; then
    echo "  /data 目录存在，检查内容:"
    ls -lah /data/ 2>/dev/null | head -20
    echo ""
    
    # 检查可疑文件
    SUSPICIOUS_FILES=$(find /data -type f -name "*[A-Z0-9]*" 2>/dev/null | head -20)
    if [ -n "$SUSPICIOUS_FILES" ]; then
        echo "  ⚠️  发现可疑文件（随机字符串命名）:"
        echo "$SUSPICIOUS_FILES" | while read file; do
            if [ -f "$file" ]; then
                SIZE=$(stat -c %s "$file" 2>/dev/null || echo "0")
                PERMS=$(stat -c %a "$file" 2>/dev/null || echo "???")
                OWNER=$(stat -c %U "$file" 2>/dev/null || echo "???")
                MOD_TIME=$(stat -c %y "$file" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1 || echo "???")
                FILE_TYPE=$(file "$file" 2>/dev/null | cut -d: -f2 || echo "未知")
                echo "    文件: $file"
                echo "      大小: $SIZE 字节, 权限: $PERMS, 所有者: $OWNER"
                echo "      修改时间: $MOD_TIME"
                echo "      类型: $FILE_TYPE"
                
                # 检查是否为可执行文件
                if [ -x "$file" ]; then
                    echo "      ⚠️  这是一个可执行文件！"
                fi
                echo ""
            fi
        done
    fi
else
    echo "  ✅ /data 目录不存在"
fi
echo ""

# 2. 检查这些文件的进程
echo "[2/5] 检查可疑文件的运行进程..."
if [ -f "/data/MUTA71VL" ] || [ -f "/data/CX81yM9aE" ]; then
    for file in /data/MUTA71VL /data/CX81yM9aE; do
        if [ -f "$file" ]; then
            FILE_NAME=$(basename "$file")
            PROCESSES=$(ps aux | grep "$FILE_NAME" | grep -v grep || true)
            if [ -n "$PROCESSES" ]; then
                echo "  ⚠️  发现运行中的进程: $FILE_NAME"
                echo "$PROCESSES" | while read line; do
                    PID=$(echo "$line" | awk '{print $2}')
                    USER=$(echo "$line" | awk '{print $1}')
                    CMD=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
                    CPU=$(echo "$line" | awk '{print $3}')
                    MEM=$(echo "$line" | awk '{print $4}')
                    echo "    PID: $PID, 用户: $USER, CPU: ${CPU}%, 内存: ${MEM}%"
                    echo "    命令: $CMD"
                done
            fi
        fi
    done
else
    echo "  ✅ 未发现可疑文件进程"
fi
echo ""

# 3. 检查文件内容（前几行）
echo "[3/5] 检查可疑文件内容（前20行）..."
for file in /data/MUTA71VL /data/CX81yM9aE; do
    if [ -f "$file" ]; then
        echo "  文件: $file"
        echo "  内容预览:"
        head -20 "$file" 2>/dev/null | sed 's/^/    /' || echo "    无法读取文件内容"
        echo ""
        
        # 检查是否为脚本文件
        FIRST_LINE=$(head -1 "$file" 2>/dev/null || echo "")
        if echo "$FIRST_LINE" | grep -qE "^#!/bin/bash|^#!/bin/sh|^#!/usr/bin/python|^#!/usr/bin/env"; then
            echo "    ⚠️  这是一个脚本文件！"
        fi
        echo ""
    fi
done
echo ""

# 4. 检查文件来源（通过 inode 和进程）
echo "[4/5] 检查文件来源..."
for file in /data/MUTA71VL /data/CX81yM9aE; do
    if [ -f "$file" ]; then
        INODE=$(stat -c %i "$file" 2>/dev/null || echo "")
        if [ -n "$INODE" ]; then
            LSOF_OUTPUT=$(lsof "$file" 2>/dev/null || true)
            if [ -n "$LSOF_OUTPUT" ]; then
                echo "  文件: $file (inode: $INODE)"
                echo "  使用此文件的进程:"
                echo "$LSOF_OUTPUT" | tail -n +2 | awk '{printf "    PID:%-8s 用户:%-10s 命令: %s\n", $2, $3, $9}' | head -10
            fi
        fi
    fi
done
echo ""

# 5. 检查定时任务中是否引用了这些文件
echo "[5/5] 检查定时任务..."
CRON_JOBS=$(crontab -l 2>/dev/null || echo "")
if echo "$CRON_JOBS" | grep -qE "MUTA71VL|CX81yM9aE"; then
    echo "  ⚠️  发现定时任务引用了可疑文件:"
    echo "$CRON_JOBS" | grep -E "MUTA71VL|CX81yM9aE" | sed 's/^/    /'
else
    echo "  ✅ 定时任务中未发现可疑文件引用"
fi

# 检查系统级定时任务
if [ -f /etc/crontab ]; then
    if grep -qE "MUTA71VL|CX81yM9aE" /etc/crontab 2>/dev/null; then
        echo "  ⚠️  系统定时任务中发现了可疑文件:"
        grep -E "MUTA71VL|CX81yM9aE" /etc/crontab | sed 's/^/    /'
    fi
fi
echo ""

# 总结和建议
echo "=========================================="
echo "检查总结"
echo "=========================================="
echo ""

if [ -f "/data/MUTA71VL" ] || [ -f "/data/CX81yM9aE" ]; then
    echo "⚠️  发现可疑文件！"
    echo ""
    echo "建议立即采取以下措施："
    echo "  1. 终止相关进程（如果正在运行）:"
    echo "     sudo pkill -f MUTA71VL"
    echo "     sudo pkill -f CX81yM9aE"
    echo ""
    echo "  2. 备份文件（用于分析）:"
    echo "     sudo cp /data/MUTA71VL /tmp/MUTA71VL.backup"
    echo "     sudo cp /data/CX81yM9aE /tmp/CX81yM9aE.backup"
    echo ""
    echo "  3. 删除可疑文件:"
    echo "     sudo rm -f /data/MUTA71VL"
    echo "     sudo rm -f /data/CX81yM9aE"
    echo ""
    echo "  4. 检查并清理定时任务:"
    echo "     crontab -e"
    echo "     sudo nano /etc/crontab"
    echo ""
    echo "  5. 更改所有密码（SSH、数据库、应用等）"
    echo ""
    echo "  6. 检查系统完整性:"
    echo "     sudo debsums -c"
    echo ""
    echo "  7. 运行完整安全扫描:"
    echo "     sudo rkhunter --check"
else
    echo "✅ 未发现可疑文件"
fi
echo ""

