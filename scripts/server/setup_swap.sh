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
SWAP_SIZE="4G"
SWAPPINESS=10

# 检查是否已存在 Swap
if [ -f "$SWAP_FILE" ] || swapon --show | grep -q "$SWAP_FILE"; then
    echo "✅ Swap 文件已存在，跳过创建"
    swapon --show | grep "$SWAP_FILE" || echo "⚠️  Swap 文件存在但未激活"
    exit 0
fi

echo "📦 创建 ${SWAP_SIZE} Swap 文件..."

# 检查可用磁盘空间（需要至少 5GB）
AVAILABLE_SPACE=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 5 ]; then
    echo "⚠️  可用磁盘空间不足 5GB，无法创建 Swap"
    echo "   当前可用: ${AVAILABLE_SPACE}GB"
    exit 1
fi

# 创建 Swap 文件
sudo fallocate -l $SWAP_SIZE $SWAP_FILE || {
    echo "⚠️  fallocate 失败，尝试使用 dd..."
    sudo dd if=/dev/zero of=$SWAP_FILE bs=1M count=4096 status=progress
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
