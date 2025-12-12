#!/bin/bash
# 获取服务器IP地址的工具脚本

echo "=========================================="
echo "服务器IP地址信息"
echo "=========================================="
echo ""

echo "[1] 内网IP地址:"
hostname -I | awk '{print $1}'
echo ""

echo "[2] 所有网络接口:"
ip addr show | grep -E "inet " | grep -v "127.0.0.1" | awk '{print $2}' | cut -d'/' -f1
echo ""

echo "[3] 公网IP地址 (如果可访问):"
curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "无法获取公网IP"
echo ""

echo "[4] 主机名:"
hostname
echo ""

echo "=========================================="
echo "提示: 通常使用内网IP (hostname -I) 的第一个IP"
echo "=========================================="

