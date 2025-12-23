#!/bin/bash
# 调试迁移问题：检查迁移脚本是否真的执行了

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
echo "📊 检查 Alembic 版本..."
alembic current

echo ""
echo "🔍 检查数据库文件..."
DB_FILE="$ADMIN_BACKEND/admin.db"
if [ -f "$DB_FILE" ]; then
    echo "✅ 数据库文件存在: $DB_FILE"
    ls -lh "$DB_FILE"
else
    echo "❌ 数据库文件不存在: $DB_FILE"
    exit 1
fi

echo ""
echo "📋 检查所有表..."
python3 << 'PYTHON_SCRIPT'
import sqlite3
import sys
import os

db_file = os.path.join(os.path.dirname(__file__), "admin.db")
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

print(f"数据库中共有 {len(tables)} 个表:")
for table in tables:
    print(f"  - {table}")

# 检查站点相关表
site_tables = ['sites', 'site_visits', 'ai_conversations', 'contact_forms', 'site_analytics']
print("\n站点相关表检查:")
for table in site_tables:
    if table in tables:
        # 检查表结构
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print(f"  ✅ {table} - {len(columns)} 列")
    else:
        print(f"  ❌ {table} - 不存在")

conn.close()
PYTHON_SCRIPT

echo ""
echo "🔍 检查 Alembic 版本表..."
python3 << 'PYTHON_SCRIPT'
import sqlite3
import sys
import os

db_file = os.path.join(os.path.dirname(__file__), "admin.db")
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# 检查 alembic_version 表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
if cursor.fetchone():
    cursor.execute("SELECT version_num FROM alembic_version")
    version = cursor.fetchone()
    if version:
        print(f"  Alembic 版本: {version[0]}")
    else:
        print("  Alembic 版本: 未设置")
else:
    print("  ❌ alembic_version 表不存在")

conn.close()
PYTHON_SCRIPT

echo ""
echo "🧪 尝试手动运行迁移脚本的升级函数..."
python3 << 'PYTHON_SCRIPT'
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

try:
    from alembic import op
    from sqlalchemy import inspect
    
    # 尝试导入迁移脚本
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'alembic', 'versions'))
    
    # 读取迁移脚本
    migration_file = os.path.join(os.path.dirname(__file__), 'alembic', 'versions', '001_add_sites_tables.py')
    if os.path.exists(migration_file):
        print(f"  ✅ 找到迁移脚本: {migration_file}")
        
        # 读取文件内容
        with open(migration_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'inspector.has_table' in content:
                print("  ✅ 迁移脚本包含表存在检查")
            else:
                print("  ⚠️  迁移脚本不包含表存在检查")
    else:
        print(f"  ❌ 未找到迁移脚本: {migration_file}")
        
except Exception as e:
    print(f"  ⚠️  检查失败: {e}")
PYTHON_SCRIPT

echo ""
echo "💡 建议："
echo "   1. 如果表不存在，尝试运行: alembic downgrade xxxx_add_session_id && alembic upgrade head"
echo "   2. 或者直接使用 Python 创建表（如果迁移有问题）"

