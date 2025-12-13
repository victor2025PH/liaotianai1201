#!/bin/bash
# ============================================================
# 诊断文件持续存在的原因
# ============================================================

set -e

echo "=========================================="
echo "🔍 诊断文件持续存在的原因"
echo "=========================================="
echo ""

SUSPICIOUS_FILES=("/data/MUTA71VL" "/data/CX81yM9aE" "/data/UY")

for file in "${SUSPICIOUS_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "=========================================="
        echo "检查文件: $file"
        echo "=========================================="
        
        # 1. 文件基本信息
        echo "[1/8] 文件基本信息:"
        ls -li "$file" 2>/dev/null || echo "  无法获取文件信息"
        echo ""
        
        # 2. 文件属性
        echo "[2/8] 文件属性:"
        lsattr "$file" 2>/dev/null || echo "  无法获取文件属性"
        echo ""
        
        # 3. 文件 inode 和硬链接
        echo "[3/8] 文件 inode 和硬链接:"
        if [ -f "$file" ]; then
            INODE=$(stat -c %i "$file" 2>/dev/null || echo "")
            if [ -n "$INODE" ]; then
                echo "  inode: $INODE"
                echo "  查找所有硬链接:"
                find /data -inum "$INODE" 2>/dev/null | while read f; do
                    echo "    $f"
                done
            fi
        fi
        echo ""
        
        # 4. 占用文件的进程
        echo "[4/8] 占用文件的进程:"
        sudo lsof "$file" 2>/dev/null || echo "  无进程占用"
        echo ""
        
        # 5. 文件系统信息
        echo "[5/8] 文件系统信息:"
        mount | grep " /data " || echo "  无法获取挂载信息"
        df -h /data 2>/dev/null || echo "  无法获取磁盘信息"
        echo ""
        
        # 6. 文件权限和所有者
        echo "[6/8] 文件权限和所有者:"
        stat "$file" 2>/dev/null | grep -E "Access:|Uid:|Gid:" || echo "  无法获取权限信息"
        echo ""
        
        # 7. 检查是否有进程在监控/重新创建文件
        echo "[7/8] 检查相关进程:"
        FILE_NAME=$(basename "$file")
        echo "  查找命令中包含文件名的进程:"
        ps aux | grep -i "$FILE_NAME" | grep -v grep || echo "    未发现相关进程"
        echo "  查找使用该文件的进程:"
        sudo fuser "$file" 2>/dev/null || echo "    无进程使用该文件"
        echo ""
        
        # 8. 检查文件是否被锁定
        echo "[8/8] 检查文件锁定状态:"
        if flock -n "$file" true 2>/dev/null; then
            echo "  文件未被锁定"
        else
            echo "  ⚠️  文件可能被锁定"
        fi
        
        # 尝试删除测试
        echo ""
        echo "尝试删除测试:"
        if sudo rm -f "$file" 2>/dev/null; then
            echo "  ✅ 删除成功"
            sleep 1
            if [ -f "$file" ]; then
                echo "  ⚠️  文件被重新创建！"
                echo "  重新创建时间:"
                stat -c "    %y" "$file" 2>/dev/null || echo "    无法获取"
            else
                echo "  ✅ 文件已删除"
            fi
        else
            echo "  ❌ 删除失败"
        fi
        echo ""
    fi
done

echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""

