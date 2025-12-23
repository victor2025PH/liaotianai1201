#!/bin/bash
# 验证站点管理迁移是否成功

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
CURRENT_VERSION=$(alembic current 2>/dev/null | grep -oE '[a-f0-9]+|xxxx_[a-z_]+|000_[a-z_]+|001_[a-z_]+' | head -1 || echo "")
echo "   当前版本: ${CURRENT_VERSION:-未设置}"

echo ""
echo "🔍 检查站点表..."
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
tables = ['sites', 'site_visits', 'ai_conversations', 'contact_forms', 'site_analytics']
all_exist = True

for table in tables:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    if cursor.fetchone():
        print(f"✅ 表 '{table}' 存在")
    else:
        print(f"❌ 表 '{table}' 不存在")
        all_exist = False

if all_exist:
    print("\n✅ 所有站点表都已创建")
    
    # 检查站点数据
    cursor.execute("SELECT COUNT(*) FROM sites")
    count = cursor.fetchone()[0]
    print(f"\n📊 站点数据: {count} 条记录")
    
    if count == 0:
        print("⚠️  站点表为空，需要初始化")
        sys.exit(1)
    else:
        cursor.execute("SELECT id, name, site_type, status FROM sites")
        sites = cursor.fetchall()
        print("\n站点列表:")
        for site in sites:
            print(f"  - ID: {site[0]}, 名称: {site[1]}, 类型: {site[2]}, 状态: {site[3]}")
else:
    print("\n❌ 部分表缺失，迁移可能未完成")
    sys.exit(1)

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
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "✅ 站点管理迁移验证完成！"
echo "=========================================="
echo ""
echo "💡 下一步："
echo "   1. 重启后端服务以加载新的 API"
echo "   2. 测试站点管理 API: curl http://127.0.0.1:8000/api/v1/sites"
echo "   3. 部署前端管理后台"

