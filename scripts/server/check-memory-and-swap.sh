#!/bin/bash
# ============================================================
# 检查内存和 Swap 状态
# ============================================================

echo "========================================="
echo "检查内存和 Swap 状态"
echo "========================================="
echo ""

# 检查内存
echo "[1/3] 内存使用情况："
free -h
echo ""

# 检查 Swap
echo "[2/3] Swap 状态："
swapon --show
echo ""

# 检查 Swap 文件
echo "[3/3] Swap 文件："
if [ -f /swapfile ]; then
    ls -lh /swapfile
    echo ""
    echo "检查 Swap 是否在 /etc/fstab 中："
    grep swapfile /etc/fstab || echo "⚠️  Swap 未在 /etc/fstab 中（重启后会丢失）"
else
    echo "⚠️  /swapfile 不存在"
fi
echo ""

# 检查进程内存使用（Top 10）
echo "Top 10 内存使用进程："
ps aux --sort=-%mem | head -11
echo ""

# 建议
echo "========================================="
echo "建议"
echo "========================================="

SWAP_SIZE=$(free -h | grep Swap | awk '{print $2}')
if [ "$SWAP_SIZE" = "0B" ] || [ "$SWAP_SIZE" = "0" ]; then
    echo "⚠️  警告：Swap 未启用或大小为 0"
    echo ""
    echo "执行以下命令启用 Swap："
    echo "  sudo swapon /swapfile"
    echo ""
    echo "如果 Swap 文件不存在，创建 8GB Swap："
    echo "  sudo fallocate -l 8G /swapfile"
    echo "  sudo chmod 600 /swapfile"
    echo "  sudo mkswap /swapfile"
    echo "  sudo swapon /swapfile"
    echo "  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab"
else
    echo "✅ Swap 已启用: $SWAP_SIZE"
fi
