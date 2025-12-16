#!/bin/bash
# ============================================================
# Activate All Accounts (Server Environment - Linux)
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Batch activate all accounts in the database
#
# One-click execution: bash scripts/server/activate_all_accounts.sh
# ============================================================

set -e

echo "============================================================"
echo "🔧 批量激活所有账号"
echo "============================================================"
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
DB_FILE="$BACKEND_DIR/data/app.db"

# 检查数据库文件是否存在
if [ ! -f "$DB_FILE" ]; then
  echo "❌ 数据库文件不存在: $DB_FILE"
  echo "请检查项目路径是否正确"
  exit 1
fi

echo "[1/3] 检查数据库..."
echo "----------------------------------------"
echo "数据库文件: $DB_FILE"

# 检查 SQLite3 是否可用
if ! command -v sqlite3 &> /dev/null; then
  echo "❌ sqlite3 命令不可用，请安装: sudo apt-get install sqlite3"
  exit 1
fi

# 统计账号数量
TOTAL_ACCOUNTS=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM group_ai_accounts;" 2>/dev/null || echo "0")
ACTIVE_ACCOUNTS=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM group_ai_accounts WHERE active = 1;" 2>/dev/null || echo "0")
INACTIVE_ACCOUNTS=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM group_ai_accounts WHERE active = 0;" 2>/dev/null || echo "0")

echo "总账号数: $TOTAL_ACCOUNTS"
echo "已激活: $ACTIVE_ACCOUNTS"
echo "未激活: $INACTIVE_ACCOUNTS"
echo ""

if [ "$INACTIVE_ACCOUNTS" = "0" ]; then
  echo "✅ 所有账号都已激活，无需操作"
  exit 0
fi

# 显示未激活的账号列表
echo "[2/3] 未激活的账号列表..."
echo "----------------------------------------"
sqlite3 "$DB_FILE" "SELECT account_id, phone_number, username, server_id FROM group_ai_accounts WHERE active = 0;" 2>/dev/null | while IFS='|' read -r account_id phone username server_id; do
  echo "  - $account_id (电话: ${phone:-N/A}, 用户名: ${username:-N/A}, 服务器: ${server_id:-N/A})"
done
echo ""

# 确认操作
echo "[3/3] 激活所有账号..."
echo "----------------------------------------"
echo "⚠️  即将激活 $INACTIVE_ACCOUNTS 个账号"
read -p "确认继续？(y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "操作已取消"
  exit 0
fi

# 备份数据库
BACKUP_FILE="${DB_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$DB_FILE" "$BACKUP_FILE"
echo "✅ 数据库已备份到: $BACKUP_FILE"

# 激活所有账号
sqlite3 "$DB_FILE" "UPDATE group_ai_accounts SET active = 1 WHERE active = 0;" 2>/dev/null

# 验证结果
UPDATED_COUNT=$(sqlite3 "$DB_FILE" "SELECT changes();" 2>/dev/null || echo "0")
NEW_ACTIVE_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM group_ai_accounts WHERE active = 1;" 2>/dev/null || echo "0")

echo ""
echo "✅ 激活完成！"
echo "   - 已激活账号数: $UPDATED_COUNT"
echo "   - 当前活跃账号总数: $NEW_ACTIVE_COUNT"
echo ""
echo "============================================================"
echo "✅ 批量激活完成"
echo "============================================================"
echo ""
echo "现在可以尝试使用"一键启动所有账号"功能了"

