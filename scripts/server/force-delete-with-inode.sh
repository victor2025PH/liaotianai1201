#!/bin/bash
# ============================================================
# 使用 inode 强制删除文件（绕过文件名）
# ============================================================

set -e

echo "=========================================="
echo "🔥 使用 inode 强制删除文件"
echo "=========================================="
echo ""

SUSPICIOUS_FILES=("/data/MUTA71VL" "/data/CX81yM9aE" "/data/UY")

for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "处理文件: $file"
        
        # 获取文件 inode
        INODE=$(stat -c %i "$file" 2>/dev/null || echo "")
        if [ -z "$INODE" ]; then
            echo "  ❌ 无法获取文件 inode"
            continue
        fi
        
        echo "  inode: $INODE"
        
        # 查找所有硬链接
        ALL_LINKS=$(find /data -inum "$INODE" 2>/dev/null)
        echo "  找到的硬链接:"
        echo "$ALL_LINKS" | while read link; do
            echo "    $link"
        done
        
        # 终止所有使用该文件的进程
        echo "  终止使用该文件的进程..."
        for link in $ALL_LINKS; do
            PIDS=$(sudo lsof "$link" 2>/dev/null | awk 'NR>1 {print $2}' | sort -u || true)
            for pid in $PIDS; do
                if [ -n "$pid" ] && [ "$pid" != "$$" ]; then
                    echo "    终止进程 PID: $pid"
                    sudo kill -9 "$pid" 2>/dev/null || true
                fi
            done
        done
        
        sleep 2
        
        # 移除文件属性（如果有）
        echo "  移除文件特殊属性..."
        for link in $ALL_LINKS; do
            sudo chattr -a -i -u "$link" 2>/dev/null || true
        done
        
        # 使用 find -delete 通过 inode 删除
        echo "  通过 inode 删除文件..."
        find /data -inum "$INODE" -delete 2>/dev/null || {
            # 如果 find -delete 失败，尝试逐个删除硬链接
            echo "  find -delete 失败，尝试逐个删除硬链接..."
            for link in $ALL_LINKS; do
                if [ -f "$link" ]; then
                    echo "    删除: $link"
                    sudo rm -f "$link" 2>/dev/null || true
                fi
            done
        }
        
        # 同步文件系统
        sync
        sleep 1
        
        # 验证删除
        REMAINING=$(find /data -inum "$INODE" 2>/dev/null | wc -l)
        if [ "$REMAINING" -eq 0 ]; then
            echo "  ✅ 文件已删除（通过 inode）"
        else
            echo "  ⚠️  文件仍存在，剩余硬链接数: $REMAINING"
            echo "  剩余硬链接:"
            find /data -inum "$INODE" 2>/dev/null | while read link; do
                echo "    $link"
            done
        fi
        echo ""
    fi
done

# 最终验证
echo "=========================================="
echo "最终验证"
echo "=========================================="
sync
sleep 2

for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ⚠️  文件仍存在: $file"
    else
        echo "  ✅ 文件已删除: $file"
    fi
done
echo ""

