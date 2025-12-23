#!/bin/bash
# 验证站点管理系统是否正常工作

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
echo "=========================================="
echo "🔍 验证站点管理系统"
echo "=========================================="

echo ""
echo "1️⃣ 检查数据库表..."
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
        print(f"  ✅ {table}")
    else:
        print(f"  ❌ {table} - 缺失")
        all_exist = False

if not all_exist:
    print("\n❌ 部分表缺失")
    sys.exit(1)

conn.close()
PYTHON_SCRIPT

EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    exit 1
fi

echo ""
echo "2️⃣ 检查站点数据..."
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
    print("  ❌ 站点数据为空")
    sys.exit(1)

print(f"  ✅ 站点数据: {count} 条记录")

cursor.execute("SELECT id, name, site_type, status FROM sites")
sites = cursor.fetchall()
print("\n  站点列表:")
for site in sites:
    print(f"    - ID: {site[0]}, 名称: {site[1]}, 类型: {site[2]}, 状态: {site[3]}")

conn.close()
PYTHON_SCRIPT

EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "  ⚠️  站点数据为空，运行: python scripts/init_sites.py"
    exit 1
fi

echo ""
echo "3️⃣ 检查后端服务..."
if curl -s http://127.0.0.1:8000/api/v1/sites > /dev/null 2>&1; then
    echo "  ✅ 后端 API 可访问"
    
    echo ""
    echo "4️⃣ 测试站点管理 API..."
    RESPONSE=$(curl -s http://127.0.0.1:8000/api/v1/sites)
    if echo "$RESPONSE" | grep -q "items"; then
        echo "  ✅ API 响应正常"
        echo ""
        echo "  API 响应示例:"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null | head -20 || echo "$RESPONSE" | head -10
    else
        echo "  ⚠️  API 响应异常: $RESPONSE"
    fi
else
    echo "  ⚠️  后端服务未运行或无法访问"
    echo "     请检查: pm2 list | grep admin-backend"
fi

echo ""
echo "5️⃣ 检查 Alembic 版本..."
CURRENT_VERSION=$(alembic current 2>/dev/null | grep -oE '[a-f0-9]+|xxxx_[a-z_]+|000_[a-z_]+|001_[a-z_]+' | head -1 || echo "")
if [ -n "$CURRENT_VERSION" ]; then
    echo "  ✅ Alembic 版本: $CURRENT_VERSION"
else
    echo "  ⚠️  无法获取 Alembic 版本"
fi

echo ""
echo "=========================================="
echo "✅ 验证完成！"
echo "=========================================="
echo ""
echo "💡 下一步："
echo "   1. 如果后端服务未运行，启动后端: pm2 restart admin-backend"
echo "   2. 部署前端管理后台: bash scripts/deploy_sites_admin.sh"
echo "   3. 在三个展示网站添加数据收集脚本"

