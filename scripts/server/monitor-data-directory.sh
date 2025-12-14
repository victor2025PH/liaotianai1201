#!/bin/bash
# ============================================================
# 监控 /data/ 目录，检测文件何时被创建
# ============================================================

set +e

echo "=========================================="
echo "👁️  监控 /data/ 目录"
echo "=========================================="
echo ""
echo "此脚本将监控 /data/ 目录，检测新文件的创建"
echo "按 Ctrl+C 停止监控"
echo ""

# 创建监控日志文件
MONITOR_LOG="/tmp/data_monitor_$(date +%Y%m%d_%H%M%S).log"
echo "监控日志: $MONITOR_LOG"
echo ""

# 记录初始文件列表
echo "[初始状态] $(date '+%Y-%m-%d %H:%M:%S')" >> "$MONITOR_LOG"
ls -la /data/ >> "$MONITOR_LOG" 2>&1
echo "" >> "$MONITOR_LOG"

echo "开始监控 /data/ 目录..."
echo ""

# 如果 inotifywait 可用，使用它
if command -v inotifywait >/dev/null 2>&1; then
    echo "使用 inotifywait 实时监控..."
    echo ""
    
    inotifywait -m /data/ -e create,modify,moved_to --format '%T %e %w%f' --timefmt '%Y-%m-%d %H:%M:%S' 2>&1 | while read line; do
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        echo "[$TIMESTAMP] $line" | tee -a "$MONITOR_LOG"
        
        # 检查新创建的文件
        if echo "$line" | grep -q "CREATE\|MOVED_TO"; then
            FILE_PATH=$(echo "$line" | awk '{print $NF}')
            if [ -f "$FILE_PATH" ]; then
                echo ""
                echo "  ⚠️  检测到新文件: $FILE_PATH"
                echo "  文件信息:"
                ls -lh "$FILE_PATH" | awk '{print "    大小: " $5 ", 权限: " $1 ", 所有者: " $3 ":" $4}'
                
                # 检查是否有进程在使用
                LSOF_OUTPUT=$(sudo lsof "$FILE_PATH" 2>/dev/null || true)
                if [ -n "$LSOF_OUTPUT" ]; then
                    echo "  使用该文件的进程:"
                    echo "$LSOF_OUTPUT" | sed 's/^/    /'
                fi
                
                # 检查文件类型
                FILE_TYPE=$(file "$FILE_PATH" 2>/dev/null || echo "无法确定")
                echo "  文件类型: $FILE_TYPE"
                echo ""
            fi
        fi
    done
else
    echo "⚠️  inotifywait 未安装，使用轮询方式监控..."
    echo "安装 inotifywait: sudo apt install inotify-tools"
    echo ""
    
    # 轮询方式
    while true; do
        sleep 5
        
        CURRENT_FILES=$(ls -1 /data/ 2>/dev/null | grep -v "^lost+found$" || true)
        PREVIOUS_FILES=$(cat /tmp/data_files_previous.txt 2>/dev/null || true)
        
        if [ "$CURRENT_FILES" != "$PREVIOUS_FILES" ]; then
            TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
            echo "[$TIMESTAMP] 文件列表发生变化" | tee -a "$MONITOR_LOG"
            
            # 找出新文件
            NEW_FILES=$(comm -13 <(echo "$PREVIOUS_FILES" | sort) <(echo "$CURRENT_FILES" | sort) 2>/dev/null || true)
            if [ -n "$NEW_FILES" ]; then
                echo "$NEW_FILES" | while read new_file; do
                    if [ -n "$new_file" ]; then
                        FILE_PATH="/data/$new_file"
                        echo "  ⚠️  检测到新文件: $FILE_PATH" | tee -a "$MONITOR_LOG"
                        
                        if [ -f "$FILE_PATH" ]; then
                            ls -lh "$FILE_PATH" | tee -a "$MONITOR_LOG"
                            
                            # 检查进程
                            LSOF_OUTPUT=$(sudo lsof "$FILE_PATH" 2>/dev/null || true)
                            if [ -n "$LSOF_OUTPUT" ]; then
                                echo "  使用该文件的进程:" | tee -a "$MONITOR_LOG"
                                echo "$LSOF_OUTPUT" | tee -a "$MONITOR_LOG"
                            fi
                        fi
                    fi
                done
            fi
            
            # 保存当前文件列表
            echo "$CURRENT_FILES" > /tmp/data_files_previous.txt
        fi
        
        # 记录当前文件列表到日志
        echo "[$TIMESTAMP] 当前文件列表:" >> "$MONITOR_LOG"
        ls -la /data/ >> "$MONITOR_LOG" 2>&1
    done
fi

