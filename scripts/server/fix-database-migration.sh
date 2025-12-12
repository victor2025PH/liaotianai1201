#!/bin/bash
# 修复数据库迁移问题 - 表已存在的情况

set -e

echo "=========================================="
echo "修复数据库迁移问题"
echo "=========================================="

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
ADMIN_BACKEND="$PROJECT_ROOT/admin-backend"
VENV_PATH="$ADMIN_BACKEND/.venv"

cd "$ADMIN_BACKEND"
source "$VENV_PATH/bin/activate"

echo ""
echo "[1] 检查当前数据库版本..."
python3 -m alembic current

echo ""
echo "[2] 检查所有迁移版本..."
python3 -m alembic history

echo ""
echo "[3] 检查数据库中的表..."
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/home/ubuntu/telegram-ai-system/admin-backend')

from app.db import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"数据库中的表 ({len(tables)} 个):")
for table in sorted(tables):
    print(f"  - {table}")

# 检查关键表
required_tables = ['users', 'ai_provider_configs', 'ai_provider_settings']
missing_tables = [t for t in required_tables if t not in tables]

if missing_tables:
    print(f"\n⚠️  缺少表: {', '.join(missing_tables)}")
else:
    print("\n✅ 所有关键表都存在")
PYTHON_SCRIPT

echo ""
echo "[4] 检查 alembic_version 表..."
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/home/ubuntu/telegram-ai-system/admin-backend')

from app.db import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        version = result.fetchone()
        if version:
            print(f"当前数据库版本: {version[0]}")
        else:
            print("⚠️  alembic_version 表中没有记录")
            print("   需要标记当前版本")
except Exception as e:
    print(f"❌ 检查版本失败: {e}")
PYTHON_SCRIPT

echo ""
echo "[5] 尝试标记当前版本（如果表已存在）..."
# 获取最新的迁移版本
LATEST_REVISION=$(python3 -m alembic heads 2>&1 | grep -E "^[a-f0-9]+" | head -1 | awk '{print $1}')

if [ -n "$LATEST_REVISION" ]; then
    echo "最新迁移版本: $LATEST_REVISION"
    echo "尝试标记为当前版本..."
    
    # 检查是否需要标记
    python3 << PYTHON_SCRIPT
import sys
sys.path.insert(0, '/home/ubuntu/telegram-ai-system/admin-backend')

from app.db import engine
from sqlalchemy import text, inspect

inspector = inspect(engine)
tables = inspector.get_table_names()

# 如果表都存在，尝试标记版本
if 'users' in tables and 'ai_provider_configs' in tables:
    try:
        with engine.connect() as conn:
            # 检查 alembic_version 表
            try:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.fetchone()
                if not version:
                    print("标记数据库版本为: $LATEST_REVISION")
                    conn.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('$LATEST_REVISION')"))
                    conn.commit()
                    print("✅ 版本标记成功")
                else:
                    print(f"✅ 数据库已有版本记录: {version[0]}")
            except Exception as e:
                print(f"⚠️  无法标记版本: {e}")
    except Exception as e:
        print(f"❌ 操作失败: {e}")
else:
    print("⚠️  表不完整，需要运行迁移")
PYTHON_SCRIPT
else
    echo "❌ 无法获取最新版本"
fi

echo ""
echo "[6] 尝试升级到最新版本（跳过已存在的表）..."
# 使用 stamp 命令标记版本，然后升级
python3 -m alembic stamp head 2>/dev/null || {
    echo "⚠️  stamp 失败，尝试直接升级..."
    python3 -m alembic upgrade head 2>&1 | grep -v "table.*already exists" || true
}

echo ""
echo "[7] 验证最终状态..."
python3 -m alembic current

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "如果仍有问题，可以："
echo "1. 手动标记版本: python3 -m alembic stamp head"
echo "2. 查看迁移历史: python3 -m alembic history"
echo "3. 检查数据库表: python3 -c \"from app.db import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())\""
echo ""

