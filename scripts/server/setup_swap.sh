#!/bin/bash
# ============================================================
# 服务器资源防护脚本 - 配置 Swap 虚拟内存
# 防止构建时内存溢出导致 SSH 断开
# ============================================================

set -e

echo "=========================================="
echo "🔧 配置 Swap 虚拟内存"
echo "=========================================="
echo ""

SWAP_FILE="/swapfile"
SWAP_SIZE="8G"  # 增加到 8GB，与物理内存 1:1 比例
SWAPPINESS=10

# 检查是否已存在 Swap
CURRENT_SWAP_SIZE=$(swapon --show=SIZE --noheadings 2>/dev/null | head -1 || echo "")
if [ -f "$SWAP_FILE" ] || [ -n "$CURRENT_SWAP_SIZE" ]; then
    if [ -n "$CURRENT_SWAP_SIZE" ]; then
        echo "✅ Swap 已存在，当前大小: $CURRENT_SWAP_SIZE"
        # 检查是否需要扩展
        CURRENT_SIZE_GB=$(echo "$CURRENT_SWAP_SIZE" | sed 's/[^0-9]//g')
        if [ "$CURRENT_SIZE_GB" -lt 8 ]; then
            echo "⚠️  当前 Swap 大小 ($CURRENT_SWAP_SIZE) 小于 8GB，建议扩展"
            echo "   如需扩展，请先执行: sudo swapoff $SWAP_FILE && sudo rm $SWAP_FILE"
        fi
    else
        echo "✅ Swap 文件已存在，但未激活"
        sudo swapon $SWAP_FILE 2>/dev/null || echo "⚠️  激活失败，可能需要重新创建"
    fi
    exit 0
fi

echo "📦 创建 ${SWAP_SIZE} Swap 文件..."

# 检查可用磁盘空间（需要至少 9GB）
AVAILABLE_SPACE=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 9 ]; then
    echo "⚠️  可用磁盘空间不足 9GB，无法创建 8GB Swap"
    echo "   当前可用: ${AVAILABLE_SPACE}GB"
    exit 1
fi

# 创建 Swap 文件（8GB = 8192MB）
echo "⏳ 正在创建 8GB Swap 文件（这可能需要几分钟）..."
sudo fallocate -l $SWAP_SIZE $SWAP_FILE || {
    echo "⚠️  fallocate 失败，尝试使用 dd（这可能需要更长时间）..."
    sudo dd if=/dev/zero of=$SWAP_FILE bs=1M count=8192 status=progress
}

# 设置权限
sudo chmod 600 $SWAP_FILE

# 格式化为 Swap
echo "🔨 格式化 Swap 文件..."
sudo mkswap $SWAP_FILE

# 启用 Swap
echo "🚀 启用 Swap..."
sudo swapon $SWAP_FILE

# 验证 Swap 已启用
if swapon --show | grep -q "$SWAP_FILE"; then
    echo "✅ Swap 已成功启用"
    swapon --show
else
    echo "❌ Swap 启用失败"
    exit 1
fi

# 永久化配置（写入 /etc/fstab）
if ! grep -q "$SWAP_FILE" /etc/fstab; then
    echo "💾 写入 /etc/fstab 以永久启用..."
    echo "$SWAP_FILE none swap sw 0 0" | sudo tee -a /etc/fstab
    echo "✅ 已写入 /etc/fstab"
else
    echo "✅ /etc/fstab 中已存在 Swap 配置"
fi

# 优化 vm.swappiness（降低 Swap 使用频率，优先使用物理内存）
CURRENT_SWAPPINESS=$(cat /proc/sys/vm/swappiness 2>/dev/null || echo "60")
if [ "$CURRENT_SWAPPINESS" != "$SWAPPINESS" ]; then
    echo "⚙️  优化 vm.swappiness: $CURRENT_SWAPPINESS -> $SWAPPINESS"
    echo "vm.swappiness=$SWAPPINESS" | sudo tee -a /etc/sysctl.conf
    sudo sysctl -w vm.swappiness=$SWAPPINESS
    echo "✅ vm.swappiness 已优化"
else
    echo "✅ vm.swappiness 已是优化值: $SWAPPINESS"
fi

echo ""
echo "=========================================="
echo "✅ Swap 配置完成！"
echo "=========================================="
echo ""
echo "Swap 状态:"
free -h
echo ""
echo "验证命令:"
echo "  swapon --show"
echo "  free -h"
