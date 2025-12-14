#!/bin/bash
# ============================================================
# 检查 Nginx HTTPS 配置脚本
# ============================================================

set +e # 不在第一个错误时退出

echo "=========================================="
echo "🔍 检查 Nginx HTTPS 配置"
echo "=========================================="
echo ""

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo "此脚本需要 root 权限，请使用 sudo 运行"
    echo "使用方法: sudo bash $0"
    exit 1
fi

DOMAIN="aikz.usdt2026.cc"

echo "[1/4] 检查所有 server 块..."
echo "----------------------------------------"
echo "查找所有包含 $DOMAIN 的 server 块:"
nginx -T 2>&1 | grep -B 5 -A 20 "server_name.*$DOMAIN" | head -100
echo ""

echo "[2/4] 检查 HTTPS (443) 配置..."
echo "----------------------------------------"
HTTPS_CONFIG=$(nginx -T 2>&1 | grep -A 50 "listen.*443" | grep -A 50 "server_name.*$DOMAIN" | head -60)
if [ -n "$HTTPS_CONFIG" ]; then
    echo "✅ 找到 HTTPS 配置:"
    echo "$HTTPS_CONFIG"
else
    echo "❌ 未找到 HTTPS (443) 配置"
fi
echo ""

echo "[3/4] 检查 location 配置..."
echo "----------------------------------------"
echo "检查 /login location:"
nginx -T 2>&1 | grep -A 10 "location.*/login" | head -15
echo ""

echo "检查 /api location:"
nginx -T 2>&1 | grep -A 10 "location.*/api" | head -15
echo ""

echo "[4/4] 检查 SSL 证书..."
echo "----------------------------------------"
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo "✅ SSL 证书文件存在"
    ls -la /etc/letsencrypt/live/$DOMAIN/*.pem
else
    echo "❌ SSL 证书文件不存在"
fi
echo ""

echo "=========================================="
echo "检查完成"
echo "=========================================="
echo ""

