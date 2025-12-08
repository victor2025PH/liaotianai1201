#!/bin/bash
# ============================================================
# Quick Fix Security Configuration
# ============================================================

set -e

cd /home/ubuntu/telegram-ai-system/admin-backend

# 如果 .env 不存在，从 env.example 创建
if [ ! -f .env ]; then
    cp env.example .env
    echo "✅ 已创建 .env 文件"
fi

# 生成新的 JWT_SECRET
NEW_JWT=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")

# 更新配置
sed -i "s|^JWT_SECRET=.*|JWT_SECRET=$NEW_JWT|" .env
sed -i 's|^CORS_ORIGINS=.*|CORS_ORIGINS=https://aikz.usdt2026.cc|' .env

echo "✅ JWT_SECRET 已更新"
echo "✅ CORS_ORIGINS 已更新"
echo ""
echo "⚠️  请手动设置 ADMIN_DEFAULT_PASSWORD:"
echo "   nano .env"
echo "   找到 ADMIN_DEFAULT_PASSWORD=changeme123"
echo "   修改为强密码（至少 12 字符）"

