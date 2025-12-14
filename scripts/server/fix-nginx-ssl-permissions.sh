#!/bin/bash
# ============================================================
# 修复 Nginx SSL 证书权限问题
# ============================================================

set +e # 不在第一个错误时退出

echo "=========================================="
echo "🔧 修复 Nginx SSL 证书权限"
echo "=========================================="
echo ""

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo "此脚本需要 root 权限，请使用 sudo 运行"
    echo "使用方法: sudo bash $0"
    exit 1
fi

# SSL 证书目录
SSL_DIR="/etc/letsencrypt"
LIVE_DIR="$SSL_DIR/live"
ARCHIVE_DIR="$SSL_DIR/archive"

echo "[1/4] 检查 SSL 证书目录..."
echo "----------------------------------------"
if [ ! -d "$LIVE_DIR" ]; then
    echo "❌ SSL 证书目录不存在: $LIVE_DIR"
    exit 1
fi
echo "✅ SSL 证书目录存在"
echo ""

echo "[2/4] 检查证书文件..."
echo "----------------------------------------"
DOMAIN="aikz.usdt2026.cc"
CERT_DIR="$LIVE_DIR/$DOMAIN"

if [ ! -d "$CERT_DIR" ]; then
    echo "⚠️  域名证书目录不存在: $CERT_DIR"
    echo "查找可用的证书目录:"
    ls -la "$LIVE_DIR" | head -10
    exit 1
fi

echo "证书目录: $CERT_DIR"
ls -la "$CERT_DIR"
echo ""

echo "[3/4] 修复权限..."
echo "----------------------------------------"
# 修复 letsencrypt 目录权限
chmod 755 "$SSL_DIR" 2>/dev/null || true
chmod 755 "$LIVE_DIR" 2>/dev/null || true
chmod 755 "$ARCHIVE_DIR" 2>/dev/null || true
chmod 755 "$CERT_DIR" 2>/dev/null || true

# 修复证书文件权限
if [ -f "$CERT_DIR/fullchain.pem" ]; then
    chmod 644 "$CERT_DIR/fullchain.pem" 2>/dev/null || true
    echo "✅ 已修复 fullchain.pem 权限"
else
    echo "❌ fullchain.pem 不存在"
fi

if [ -f "$CERT_DIR/privkey.pem" ]; then
    chmod 600 "$CERT_DIR/privkey.pem" 2>/dev/null || true
    echo "✅ 已修复 privkey.pem 权限"
else
    echo "❌ privkey.pem 不存在"
fi

if [ -f "$CERT_DIR/cert.pem" ]; then
    chmod 644 "$CERT_DIR/cert.pem" 2>/dev/null || true
    echo "✅ 已修复 cert.pem 权限"
fi

if [ -f "$CERT_DIR/chain.pem" ]; then
    chmod 644 "$CERT_DIR/chain.pem" 2>/dev/null || true
    echo "✅ 已修复 chain.pem 权限"
fi

# 确保 nginx 用户可以读取证书（通过组权限）
NGINX_USER=$(ps aux | grep -E "nginx: (master|worker)" | head -1 | awk '{print $1}' || echo "www-data")
if [ -n "$NGINX_USER" ] && [ "$NGINX_USER" != "root" ]; then
    echo "检测到 Nginx 用户: $NGINX_USER"
    # 将证书目录添加到 nginx 用户组（如果存在）
    if getent group "$NGINX_USER" > /dev/null 2>&1; then
        chgrp -R "$NGINX_USER" "$CERT_DIR" 2>/dev/null || true
        chmod g+r "$CERT_DIR"/*.pem 2>/dev/null || true
        echo "✅ 已设置组权限"
    fi
fi
echo ""

echo "[4/4] 验证 Nginx 配置..."
echo "----------------------------------------"
if nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
    echo ""
    echo "重新加载 Nginx..."
    systemctl reload nginx 2>/dev/null || systemctl restart nginx
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已重新加载"
    else
        echo "❌ Nginx 重新加载失败"
        systemctl status nginx --no-pager -l | head -10
    fi
else
    echo "❌ Nginx 配置仍有错误:"
    nginx -t 2>&1 | tail -10
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""

