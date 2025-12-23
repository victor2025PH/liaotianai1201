#!/bin/bash
# 修复所有迁移问题（包括表已存在的情况）

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
if [ ! -f "$DB_FILE" ]; then
    echo "⚠️  数据库文件不存在: $DB_FILE，将创建新数据库"
fi

echo ""
echo "📊 检查当前 Alembic 版本..."
CURRENT_VERSION=$(alembic current 2>/dev/null | grep -oE '[a-f0-9]+|xxxx_[a-z_]+|000_[a-z_]+|001_[a-z_]+' | head -1 || echo "")

if [ -z "$CURRENT_VERSION" ]; then
    echo "⚠️  无法获取当前版本，数据库可能是新的或版本记录丢失"
    echo "   将尝试标记到最新版本"
    
    # 检查表是否存在，决定标记到哪个版本
    echo ""
    echo "🔍 检查数据库表..."
    python3 << 'PYTHON_SCRIPT'
import sqlite3
import sys
import os

db_file = os.path.join(os.path.dirname(__file__), "admin.db")
if not os.path.exists(db_file):
    print("数据库文件不存在，将创建新数据库")
    sys.exit(0)

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# 检查关键表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

conn.close()

# 判断应该标记到哪个版本
if 'sites' in tables and 'site_visits' in tables:
    print("检测到站点表，应该标记到 001_add_sites_tables")
    sys.exit(2)
elif 'group_ai_accounts' in tables:
    print("检测到 group_ai 表，应该标记到中间版本")
    sys.exit(1)
else:
    print("未检测到关键表，可能是新数据库")
    sys.exit(0)
PYTHON_SCRIPT

    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 2 ]; then
        # 站点表已存在，标记到站点迁移版本
        echo ""
        echo "📝 标记迁移版本为: 001_add_sites_tables"
        alembic stamp "001_add_sites_tables" 2>/dev/null || {
            echo "⚠️  标记失败，尝试标记到 head"
            alembic stamp head 2>/dev/null || echo "标记失败，请手动处理"
        }
    elif [ $EXIT_CODE -eq 1 ]; then
        # group_ai 表已存在，但站点表不存在
        echo ""
        echo "📝 检测到部分表已存在，尝试标记到中间版本..."
        # 尝试标记到 xxxx_add_session_id（AI usage 迁移）
        alembic stamp "xxxx_add_session_id" 2>/dev/null || {
            echo "⚠️  标记失败，将尝试运行迁移（可能会跳过已存在的表）"
        }
    fi
else
    echo "   当前版本: $CURRENT_VERSION"
fi

echo ""
echo "🔄 运行数据库迁移..."
if alembic upgrade head; then
    echo "✅ 数据库迁移成功！"
else
    echo "❌ 数据库迁移失败"
    echo ""
    echo "💡 如果遇到 'table already exists' 错误，可以尝试："
    echo "   1. 使用 'alembic stamp head' 标记当前版本"
    echo "   2. 或者手动修复迁移脚本，添加表存在检查"
    echo ""
    echo "   当前可以尝试："
    echo "   alembic stamp head"
    exit 1
fi

# 初始化站点数据（如果站点表存在）
echo ""
echo "📝 检查是否需要初始化站点数据..."
python3 << 'PYTHON_SCRIPT'
import sqlite3
import sys
import os

db_file = os.path.join(os.path.dirname(__file__), "admin.db")
if not os.path.exists(db_file):
    print("数据库文件不存在，跳过初始化")
    sys.exit(0)

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sites'")
if cursor.fetchone():
    cursor.execute("SELECT COUNT(*) FROM sites")
    count = cursor.fetchone()[0]
    if count == 0:
        print("站点表存在但为空，需要初始化")
        sys.exit(1)
    else:
        print(f"站点表已有 {count} 条记录，跳过初始化")
        sys.exit(0)
else:
    print("站点表不存在，跳过初始化")
    sys.exit(0)
PYTHON_SCRIPT

EXIT_CODE=$?

if [ $EXIT_CODE -eq 1 ]; then
    echo "📝 初始化站点数据..."
    if python scripts/init_sites.py; then
        echo "✅ 站点数据初始化成功！"
    else
        echo "⚠️  站点数据初始化失败，但迁移已完成。"
    fi
fi

echo ""
echo "=========================================="
echo "✅ 数据库迁移修复完成！"
echo "=========================================="

