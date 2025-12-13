#!/bin/bash
# ============================================================
# 最终文件检查和删除脚本
# ============================================================

set -e

echo "=========================================="
echo "🔍 最终文件检查和删除"
echo "=========================================="
echo ""

SUSPICIOUS_FILES=("/data/MUTA71VL" "/data/CX81yM9aE" "/data/UY")

# 1. 检查文件是否存在
echo "[1/4] 检查可疑文件..."
FILES_EXIST=0
for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        FILES_EXIST=$((FILES_EXIST+1))
        echo "  ⚠️  文件存在: $file"
        ls -lh "$file" | awk '{print "    大小: " $5 ", 权限: " $1 ", 修改时间: " $6 " " $7 " " $8}'
    else
        echo "  ✅ 文件不存在: $file"
    fi
done

if [ "$FILES_EXIST" -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ 所有可疑文件已删除！"
    echo "=========================================="
    echo ""
    echo "清理完成，建议："
    echo "  1. 运行验证脚本: bash scripts/server/verify-cleanup.sh"
    echo "  2. 更改所有密码"
    echo "  3. 运行安全扫描: sudo rkhunter --check"
    echo "  4. 监控系统资源使用情况"
    exit 0
fi

echo ""
echo "发现 $FILES_EXIST 个可疑文件，开始删除..."
echo ""

# 2. 终止所有相关进程（再次确认）
echo "[2/4] 终止所有相关进程..."
for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        FILE_NAME=$(basename "$file")
        
        # 终止使用该文件的进程
        PIDS=$(sudo lsof "$file" 2>/dev/null | awk 'NR>1 {print $2}' | sort -u || true)
        for pid in $PIDS; do
            if [ -n "$pid" ] && [ "$pid" != "$$" ]; then
                echo "  终止进程 PID: $pid (使用文件: $FILE_NAME)"
                sudo kill -9 "$pid" 2>/dev/null || true
            fi
        done
        
        # 终止命令中包含文件名的进程
        sudo pkill -9 -f "$FILE_NAME" 2>/dev/null || true
    fi
done

sleep 2
echo "  ✅ 进程终止完成"
echo ""

# 3. 强制删除文件
echo "[3/4] 强制删除文件..."
DELETED=0
FAILED=0

for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  删除: $file"
        
        # 获取 inode
        INODE=$(stat -c %i "$file" 2>/dev/null || echo "")
        
        # 方法 1: 标准删除
        if sudo rm -f "$file" 2>/dev/null; then
            DELETED=$((DELETED+1))
            echo "    ✅ 删除成功"
        else
            # 方法 2: 覆盖后删除
            echo "    ⚠️  标准删除失败，尝试覆盖删除..."
            if sudo dd if=/dev/zero of="$file" bs=1M count=10 2>/dev/null; then
                sync
                if sudo rm -f "$file" 2>/dev/null; then
                    DELETED=$((DELETED+1))
                    echo "    ✅ 覆盖删除成功"
                else
                    # 方法 3: 通过 inode 删除
                    if [ -n "$INODE" ]; then
                        echo "    ⚠️  覆盖删除失败，尝试通过 inode 删除..."
                        if find /data -inum "$INODE" -delete 2>/dev/null; then
                            DELETED=$((DELETED+1))
                            echo "    ✅ inode 删除成功"
                        else
                            FAILED=$((FAILED+1))
                            echo "    ❌ 所有删除方法均失败"
                        fi
                    else
                        FAILED=$((FAILED+1))
                        echo "    ❌ 无法获取 inode"
                    fi
                fi
            else
                FAILED=$((FAILED+1))
                echo "    ❌ 覆盖失败"
            fi
        fi
        
        # 同步文件系统
        sync
        sleep 0.5
    fi
done

echo ""
if [ "$DELETED" -gt 0 ]; then
    echo "  ✅ 成功删除 $DELETED 个文件"
fi
if [ "$FAILED" -gt 0 ]; then
    echo "  ⚠️  $FAILED 个文件删除失败"
fi
echo ""

# 4. 最终验证
echo "[4/4] 最终验证..."
sync
sync
sleep 2

# 强制刷新目录缓存
ls /data/ >/dev/null 2>&1 || true
sleep 1

REMAINING=0
for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        REMAINING=$((REMAINING+1))
        echo "  ❌ 文件仍存在: $file"
    else
        echo "  ✅ 文件已删除: $file"
    fi
done

echo ""
echo "=========================================="
if [ "$REMAINING" -eq 0 ]; then
    echo "✅ 所有可疑文件已成功删除！"
    echo "=========================================="
    echo ""
    echo "清理完成，建议："
    echo "  1. 运行验证脚本: bash scripts/server/verify-cleanup.sh"
    echo "  2. 更改所有密码"
    echo "  3. 运行安全扫描: sudo rkhunter --check"
    echo "  4. 监控系统资源使用情况"
else
    echo "⚠️  仍有 $REMAINING 个文件无法删除"
    echo "=========================================="
    echo ""
    echo "建议操作:"
    echo "  1. 重启系统后立即运行此脚本"
    echo "  2. 检查文件系统: sudo fsck /dev/vdb"
    echo "  3. 如果文件被持续重新创建，检查是否有隐藏进程"
    echo "  4. 考虑使用 Live CD 启动后删除文件"
fi
echo ""

