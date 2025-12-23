#!/bin/bash
# 完全重新生成 Nginx 配置（修复所有问题）

set -e

echo "🔧 完全重新生成 Nginx 配置..."

# 1. 备份现有配置
CONFIG_FILE="/etc/nginx/sites-available/aiadmin.usdt2026.cc"
if [ -f "$CONFIG_FILE" ]; then
    BACKUP_FILE="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    sudo cp "$CONFIG_FILE" "$BACKUP_FILE"
    echo "✅ 已备份配置文件到: $BACKUP_FILE"
fi

# 2. 删除旧配置
echo "🗑️  删除旧配置..."
sudo rm -f "$CONFIG_FILE"
sudo rm -f "/etc/nginx/sites-enabled/aiadmin.usdt2026.cc"

# 3. 重新运行配置脚本
echo "🔄 重新运行配置脚本..."
cd /home/ubuntu/telegram-ai-system
bash scripts/configure_admin_nginx.sh

echo ""
echo "=========================================="
echo "✅ 配置已完全重新生成！"
echo "=========================================="

