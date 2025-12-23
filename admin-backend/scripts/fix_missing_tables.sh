#!/bin/bash
# 修复表缺失问题：降级版本后重新运行迁移

set -e

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
ADMIN_BACKEND="$PROJECT_ROOT/admin-backend"
VENV_PATH="$ADMIN_BACKEND/.venv"

cd "$ADMIN_BACKEND" || { echo "❌ 无法进入后端目录: $ADMIN_BACKEND"; exit 1; }

# 激活虚拟环境
echo "🐍 激活虚拟环境..."
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
elif [ -d "$ADMIN_BACKEND/venv" ]; then
    source "$ADMIN_BACKEND/venv/bin/activate"
else
    echo "❌ 未找到虚拟环境"
    exit 1
fi

echo ""
echo "📊 检查当前 Alembic 版本..."
CURRENT_VERSION=$(alembic current 2>/dev/null | grep -oE '[a-f0-9]+|xxxx_[a-z_]+|000_[a-z_]+|001_[a-z_]+' | head -1 || echo "")
echo "   当前版本: ${CURRENT_VERSION:-未设置}"

echo ""
echo "🔍 检查站点表是否存在..."
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

tables = ['sites', 'site_visits', 'ai_conversations', 'contact_forms', 'site_analytics']
missing_tables = []

for table in tables:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    if not cursor.fetchone():
        missing_tables.append(table)
        print(f"❌ 表 '{table}' 不存在")

conn.close()

if missing_tables:
    print(f"\n⚠️  缺失 {len(missing_tables)} 个表，需要运行迁移")
    sys.exit(1)
else:
    print("\n✅ 所有站点表都存在")
    sys.exit(0)
PYTHON_SCRIPT

EXIT_CODE=$?

if [ $EXIT_CODE -eq 1 ]; then
    echo ""
    echo "🔧 检测到表缺失，需要重新运行迁移"
    echo ""
    echo "📝 步骤 1: 降级到迁移前的版本..."
    
    # 降级到 xxxx_add_session_id（站点迁移的 down_revision）
    if alembic downgrade xxxx_add_session_id 2>/dev/null; then
        echo "✅ 已降级到 xxxx_add_session_id"
    else
        echo "⚠️  降级失败，尝试降级到 000_initial_base"
        alembic downgrade 000_initial_base 2>/dev/null || {
            echo "⚠️  降级失败，可能需要手动处理"
        }
    fi
    
    echo ""
    echo "📝 步骤 2: 重新运行迁移（会跳过已存在的表）..."
    if alembic upgrade head; then
        echo "✅ 迁移运行成功！"
    else
        echo "❌ 迁移运行失败"
        exit 1
    fi
    
    echo ""
    echo "📝 步骤 3: 验证表是否创建..."
    python3 << 'PYTHON_SCRIPT'
import sqlite3
import sys
import os

db_file = os.path.join(os.path.dirname(__file__), "admin.db")
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

tables = ['sites', 'site_visits', 'ai_conversations', 'contact_forms', 'site_analytics']
all_exist = True

for table in tables:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    if cursor.fetchone():
        print(f"✅ 表 '{table}' 存在")
    else:
        print(f"❌ 表 '{table}' 不存在")
        all_exist = False

conn.close()

if all_exist:
    print("\n✅ 所有站点表都已创建")
    sys.exit(0)
else:
    print("\n❌ 部分表仍未创建，请检查迁移脚本")
    sys.exit(1)
PYTHON_SCRIPT
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo "📝 步骤 4: 初始化站点数据..."
        if python scripts/init_sites.py; then
            echo "✅ 站点数据初始化成功！"
        else
            echo "⚠️  站点数据初始化失败，但表已创建"
        fi
    fi
else
    echo ""
    echo "✅ 所有表都已存在，无需修复"
    echo ""
    echo "📝 检查站点数据..."
    python3 << 'PYTHON_SCRIPT'
import sqlite3
import sys
import os

db_file = os.path.join(os.path.dirname(__file__), "admin.db")
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM sites")
count = cursor.fetchone()[0]

if count == 0:
    print("⚠️  站点表为空，需要初始化")
    sys.exit(1)
else:
    cursor.execute("SELECT id, name, site_type, status FROM sites")
    sites = cursor.fetchall()
    print(f"✅ 站点数据: {count} 条记录")
    print("\n站点列表:")
    for site in sites:
        print(f"  - ID: {site[0]}, 名称: {site[1]}, 类型: {site[2]}, 状态: {site[3]}")
    sys.exit(0)

conn.close()
PYTHON_SCRIPT
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 1 ]; then
        echo ""
        echo "📝 初始化站点数据..."
        if python scripts/init_sites.py; then
            echo "✅ 站点数据初始化成功！"
        else
            echo "❌ 站点数据初始化失败"
        fi
    fi
fi

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="

