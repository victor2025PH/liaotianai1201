#!/bin/bash
# 修复站点管理迁移问题

set -e

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
ADMIN_BACKEND="$PROJECT_ROOT/admin-backend"
VENV_PATH="$ADMIN_BACKEND/.venv"

cd "$ADMIN_BACKEND" || { echo "❌ 无法进入后端目录: $ADMIN_BACKEND"; exit 1; }

# 激活虚拟环境
echo "🐍 激活虚拟环境..."
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "✅ 虚拟环境已激活: $VENV_PATH"
elif [ -d "$ADMIN_BACKEND/venv" ]; then
    source "$ADMIN_BACKEND/venv/bin/activate"
    echo "✅ 虚拟环境已激活: $ADMIN_BACKEND/venv"
else
    echo "❌ 未找到虚拟环境，请手动激活或创建。"
    exit 1
fi

# 检查数据库文件
DB_FILE="$ADMIN_BACKEND/admin.db"
if [ -f "$DB_FILE" ]; then
    echo "✅ 数据库文件存在: $DB_FILE"
else
    echo "⚠️  数据库文件不存在: $DB_FILE"
fi

# 检查当前 Alembic 版本
echo "📊 检查当前 Alembic 版本..."
CURRENT_VERSION=$(alembic current 2>/dev/null | grep -oE '[a-f0-9]+|xxxx_[a-z_]+|000_[a-z_]+' | head -1 || echo "")

if [ -z "$CURRENT_VERSION" ]; then
    echo "⚠️  无法获取当前版本，可能需要标记版本"
else
    echo "   当前版本: $CURRENT_VERSION"
fi

# 检查站点表是否已存在
echo "🔍 检查站点表是否已存在..."
python3 << 'PYTHON_SCRIPT'
import sqlite3
import sys
import os

db_file = os.path.join(os.path.dirname(__file__), "admin.db")
if not os.path.exists(db_file):
    print("❌ 数据库文件不存在")
    sys.exit(1)

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# 检查表是否存在
tables_to_check = ['sites', 'site_visits', 'ai_conversations', 'contact_forms', 'site_analytics']
existing_tables = []

for table in tables_to_check:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    if cursor.fetchone():
        existing_tables.append(table)
        print(f"✅ 表 '{table}' 已存在")
    else:
        print(f"❌ 表 '{table}' 不存在")

conn.close()

if len(existing_tables) == len(tables_to_check):
    print("\n✅ 所有站点表都已存在，可能需要标记迁移版本")
    sys.exit(2)  # 特殊退出码，表示表已存在
else:
    print(f"\n⚠️  部分表存在 ({len(existing_tables)}/{len(tables_to_check)})")
    sys.exit(0)
PYTHON_SCRIPT

EXIT_CODE=$?

if [ $EXIT_CODE -eq 2 ]; then
    echo ""
    echo "📝 所有站点表已存在，尝试标记迁移版本..."
    
    # 尝试标记为最新版本
    LATEST_REVISION="001_add_sites_tables"
    echo "   尝试标记为: $LATEST_REVISION"
    
    if alembic stamp "$LATEST_REVISION" 2>/dev/null; then
        echo "✅ 已标记迁移版本为: $LATEST_REVISION"
    else
        echo "⚠️  标记失败，可能需要手动处理"
        echo "   可以尝试: alembic stamp head"
    fi
elif [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "🔄 运行数据库迁移..."
    if alembic upgrade head; then
        echo "✅ 数据库迁移成功！"
    else
        echo "❌ 数据库迁移失败"
        echo ""
        echo "💡 如果表已存在错误，可以尝试："
        echo "   1. 检查迁移脚本是否有表存在检查"
        echo "   2. 使用 'alembic stamp head' 标记当前版本"
        exit 1
    fi
fi

# 初始化站点数据
echo ""
echo "📝 初始化站点数据..."
if python scripts/init_sites.py; then
    echo "✅ 站点数据初始化成功！"
else
    echo "⚠️  站点数据初始化失败，但迁移已完成。"
fi

echo ""
echo "=========================================="
echo "✅ 站点管理数据库迁移修复完成！"
echo "=========================================="

