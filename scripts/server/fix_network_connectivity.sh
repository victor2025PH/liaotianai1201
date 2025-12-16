#!/bin/bash
# ============================================================
# 网络连接修复脚本
# ============================================================
# 
# 功能：
# 1. 诊断网络配置问题
# 2. 检查网络接口、路由、DNS
# 3. 尝试修复常见网络问题
#
# 使用方法：sudo bash scripts/server/fix_network_connectivity.sh
# ============================================================

set -e

echo "============================================================"
echo "网络连接修复脚本"
echo "============================================================"
echo "开始时间: $(date)"
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  建议以 root 权限运行此脚本（使用 sudo）"
    echo "继续执行..."
    echo ""
fi

# ============================================================
# [1/6] 检查网络接口
# ============================================================
echo "[1/6] 检查网络接口"
echo "------------------------------------------------------------"

echo "□ 网络接口列表:"
if command -v ip > /dev/null 2>&1; then
    ip addr show
else
    ifconfig
fi
echo ""

# 获取主网络接口
MAIN_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -1)
if [ -z "$MAIN_INTERFACE" ]; then
    MAIN_INTERFACE=$(route -n | grep '^0.0.0.0' | awk '{print $8}' | head -1)
fi

if [ -n "$MAIN_INTERFACE" ]; then
    echo "□ 主网络接口: $MAIN_INTERFACE"
    ip addr show "$MAIN_INTERFACE" 2>/dev/null || ifconfig "$MAIN_INTERFACE" 2>/dev/null || echo "无法获取接口信息"
else
    echo "⚠️  未找到主网络接口"
fi
echo ""

# ============================================================
# [2/6] 检查路由表
# ============================================================
echo "[2/6] 检查路由表"
echo "------------------------------------------------------------"

echo "□ 默认路由:"
ip route | grep default || route -n | grep '^0.0.0.0' || echo "未找到默认路由"
echo ""

echo "□ 完整路由表:"
ip route show || route -n
echo ""

# 检查是否有默认网关
DEFAULT_GATEWAY=$(ip route | grep default | awk '{print $3}' | head -1)
if [ -z "$DEFAULT_GATEWAY" ]; then
    DEFAULT_GATEWAY=$(route -n | grep '^0.0.0.0' | awk '{print $2}' | head -1)
fi

if [ -n "$DEFAULT_GATEWAY" ]; then
    echo "□ 默认网关: $DEFAULT_GATEWAY"
    echo "  测试网关连接..."
    if ping -c 2 -W 2 "$DEFAULT_GATEWAY" > /dev/null 2>&1; then
        echo "  ✅ 网关可达"
    else
        echo "  ❌ 网关不可达"
    fi
else
    echo "⚠️  未找到默认网关"
fi
echo ""

# ============================================================
# [3/6] 检查 DNS 配置
# ============================================================
echo "[3/6] 检查 DNS 配置"
echo "------------------------------------------------------------"

echo "□ DNS 配置:"
if [ -f /etc/resolv.conf ]; then
    cat /etc/resolv.conf
else
    echo "⚠️  /etc/resolv.conf 不存在"
fi
echo ""

echo "□ 测试 DNS 解析:"
if nslookup google.com > /dev/null 2>&1 || host google.com > /dev/null 2>&1; then
    echo "✅ DNS 解析正常"
else
    echo "❌ DNS 解析失败"
    echo "  尝试使用 8.8.8.8 作为 DNS..."
    if [ -f /etc/resolv.conf ]; then
        # 备份原配置
        cp /etc/resolv.conf /etc/resolv.conf.bak.$(date +%Y%m%d_%H%M%S)
        # 添加 Google DNS
        echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf > /dev/null
        echo "nameserver 8.8.4.4" | sudo tee -a /etc/resolv.conf > /dev/null
        echo "✅ 已配置 DNS 为 8.8.8.8 和 8.8.4.4"
    fi
fi
echo ""

# ============================================================
# [4/6] 检查网络连接
# ============================================================
echo "[4/6] 检查网络连接"
echo "------------------------------------------------------------"

echo "□ 测试内网连接（网关）:"
if [ -n "$DEFAULT_GATEWAY" ]; then
    if ping -c 3 -W 2 "$DEFAULT_GATEWAY" > /dev/null 2>&1; then
        echo "✅ 网关连接正常"
    else
        echo "❌ 网关连接失败"
    fi
else
    echo "⚠️  无法测试（未找到网关）"
fi
echo ""

echo "□ 测试外网连接（8.8.8.8）:"
if ping -c 3 -W 5 8.8.8.8 > /dev/null 2>&1; then
    echo "✅ 外网连接正常"
else
    echo "❌ 外网连接失败（100% 丢包）"
    echo "  这可能是网络配置或云服务商网络问题"
fi
echo ""

echo "□ 测试 DNS 服务器连接:"
if ping -c 2 -W 3 8.8.8.8 > /dev/null 2>&1; then
    echo "✅ DNS 服务器可达"
else
    echo "❌ DNS 服务器不可达"
fi
echo ""

# ============================================================
# [5/6] 检查网络服务
# ============================================================
echo "[5/6] 检查网络服务"
echo "------------------------------------------------------------"

# 检查 NetworkManager
if systemctl is-active --quiet NetworkManager 2>/dev/null; then
    echo "✅ NetworkManager 运行中"
    systemctl status NetworkManager --no-pager | head -3
elif systemctl list-unit-files | grep -q NetworkManager; then
    echo "⚠️  NetworkManager 未运行"
    echo "  尝试启动 NetworkManager..."
    sudo systemctl start NetworkManager 2>/dev/null && echo "✅ NetworkManager 已启动" || echo "❌ NetworkManager 启动失败"
else
    echo "□ NetworkManager 未安装（可能使用 netplan 或 systemd-networkd）"
fi
echo ""

# 检查 systemd-networkd
if systemctl is-active --quiet systemd-networkd 2>/dev/null; then
    echo "✅ systemd-networkd 运行中"
    systemctl status systemd-networkd --no-pager | head -3
fi
echo ""

# ============================================================
# [6/6] 尝试修复网络问题
# ============================================================
echo "[6/6] 尝试修复网络问题"
echo "------------------------------------------------------------"

# 如果网络接口存在但没有 IP，尝试重启网络
if [ -n "$MAIN_INTERFACE" ]; then
    INTERFACE_IP=$(ip addr show "$MAIN_INTERFACE" 2>/dev/null | grep "inet " | awk '{print $2}' | head -1)
    if [ -z "$INTERFACE_IP" ]; then
        echo "⚠️  网络接口 $MAIN_INTERFACE 没有 IP 地址"
        echo "  尝试重启网络接口..."
        sudo ip link set "$MAIN_INTERFACE" down 2>/dev/null || true
        sleep 1
        sudo ip link set "$MAIN_INTERFACE" up 2>/dev/null || true
        echo "✅ 网络接口已重启"
    else
        echo "✅ 网络接口 $MAIN_INTERFACE 有 IP 地址: $INTERFACE_IP"
    fi
fi
echo ""

# 如果缺少默认路由，尝试添加
if [ -z "$DEFAULT_GATEWAY" ] && [ -n "$MAIN_INTERFACE" ]; then
    echo "⚠️  缺少默认路由"
    echo "  注意：无法自动添加默认路由，需要手动配置"
    echo "  请联系云服务商技术支持或检查网络配置"
fi
echo ""

# 重启网络服务（如果可能）
if systemctl is-active --quiet NetworkManager 2>/dev/null; then
    echo "□ 重启 NetworkManager..."
    sudo systemctl restart NetworkManager 2>/dev/null && echo "✅ NetworkManager 已重启" || echo "⚠️  NetworkManager 重启失败"
    sleep 3
fi
echo ""

# ============================================================
# 最终测试
# ============================================================
echo "============================================================"
echo "最终网络测试"
echo "============================================================"

echo "等待网络服务启动 (5秒)..."
sleep 5

echo ""
echo "□ 测试外网连接:"
if ping -c 3 -W 5 8.8.8.8 > /dev/null 2>&1; then
    echo "✅ 外网连接正常"
    NETWORK_OK=true
else
    echo "❌ 外网连接仍然失败"
    NETWORK_OK=false
fi
echo ""

echo "□ 测试 DNS 解析:"
if nslookup google.com > /dev/null 2>&1 || host google.com > /dev/null 2>&1; then
    echo "✅ DNS 解析正常"
else
    echo "❌ DNS 解析失败"
fi
echo ""

# ============================================================
# 诊断总结
# ============================================================
echo "============================================================"
echo "诊断总结"
echo "============================================================"

if [ "$NETWORK_OK" = true ]; then
    echo "✅ 网络连接已恢复"
    echo ""
    echo "现在可以尝试："
    echo "1. SSH 连接: ssh ubuntu@165.154.254.24"
    echo "2. 访问网站: https://aikz.usdt2026.cc"
else
    echo "❌ 网络连接问题仍然存在"
    echo ""
    echo "可能的原因："
    echo "1. 云服务商网络配置问题"
    echo "2. 服务器网络接口配置错误"
    echo "3. 路由表配置缺失"
    echo "4. 云服务商安全组/防火墙阻止了出站流量"
    echo ""
    echo "建议操作："
    echo "1. 检查 UCloud 控制台的网络配置"
    echo "2. 检查服务器是否在正确的 VPC/子网中"
    echo "3. 检查路由表配置"
    echo "4. 联系 UCloud 技术支持"
    echo ""
    echo "临时解决方案（如果只是 DNS 问题）："
    echo "  在 /etc/resolv.conf 中添加:"
    echo "    nameserver 8.8.8.8"
    echo "    nameserver 8.8.4.4"
fi

echo ""
echo "============================================================"
echo "修复完成"
echo "结束时间: $(date)"
echo "============================================================"

