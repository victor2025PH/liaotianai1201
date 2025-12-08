#!/bin/bash
# ============================================================
# Set Admin Password
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Set ADMIN_DEFAULT_PASSWORD in .env file
#
# Usage: bash scripts/server/set-admin-password.sh <password>
# ============================================================

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
ENV_FILE="$BACKEND_DIR/.env"

if [ -z "$1" ]; then
    echo "用法: bash scripts/server/set-admin-password.sh <password>"
    echo "示例: bash scripts/server/set-admin-password.sh 'MyStrongPassword123!@#'"
    exit 1
fi

NEW_PASSWORD="$1"

# 检查密码长度
if [ ${#NEW_PASSWORD} -lt 12 ]; then
    echo "⚠️  警告: 密码长度少于 12 字符，建议使用更强的密码"
fi

echo "============================================================"
echo "🔐 设置管理员密码"
echo "============================================================"
echo ""

# 检查 .env 文件是否存在
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env 文件不存在，请先运行 fix-security-config.sh"
    exit 1
fi

# 使用 Python 更新密码
cd "$BACKEND_DIR"
python3 << PYEOF
import re
from pathlib import Path

env_file = Path("$ENV_FILE")
new_password = "$NEW_PASSWORD"

# 读取文件内容
with open(env_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 更新 ADMIN_DEFAULT_PASSWORD
content = re.sub(
    r'^ADMIN_DEFAULT_PASSWORD=.*',
    f'ADMIN_DEFAULT_PASSWORD={new_password}',
    content,
    flags=re.MULTILINE
)

# 写回文件
with open(env_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 已更新 ADMIN_DEFAULT_PASSWORD")
PYEOF

echo ""
echo "============================================================"
echo "🔄 重启服务"
echo "============================================================"
echo ""

pm2 restart backend
sleep 3
pm2 status backend

echo ""
echo "✅ 管理员密码已更新！"
echo ""
echo "⚠️  重要提示:"
echo "1. 请使用新密码登录: $NEW_PASSWORD"
echo "2. 登录后立即修改密码"
echo "3. 不要将密码泄露给他人"

