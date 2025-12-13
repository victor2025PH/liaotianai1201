#!/bin/bash
# ============================================================
# 修复数据库唯一约束问题
# ============================================================

set -e

echo "=========================================="
echo "修复数据库唯一约束问题"
echo "=========================================="

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
DB_PATH="$PROJECT_DIR/admin-backend/admin.db"

if [ ! -f "$DB_PATH" ]; then
  echo "❌ 数据库文件不存在: $DB_PATH"
  exit 1
fi

echo "数据库文件: $DB_PATH"
echo ""

cd "$PROJECT_DIR/admin-backend" || exit 1

# 修复唯一约束
echo "修复唯一约束..."
python3 << 'PYTHON_SCRIPT'
import sqlite3
import sys

db_path = "admin.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查现有的索引
    print("检查现有的索引和约束...")
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='ai_provider_configs'")
    indexes = cursor.fetchall()
    
    print("现有的索引:")
    for idx_name, idx_sql in indexes:
        print(f"  - {idx_name}: {idx_sql}")
    
    # 检查是否有 provider_name 的唯一索引
    provider_name_unique = False
    for idx_name, idx_sql in indexes:
        if idx_sql and 'provider_name' in idx_sql and 'UNIQUE' in idx_sql.upper():
            print(f"\n⚠️  发现 provider_name 的唯一索引: {idx_name}")
            print(f"   删除旧的唯一索引...")
            cursor.execute(f"DROP INDEX IF EXISTS {idx_name}")
            provider_name_unique = True
    
    # 检查是否有 (provider_name, key_name) 的组合唯一约束
    has_composite_unique = False
    for idx_name, idx_sql in indexes:
        if idx_sql and 'provider_name' in idx_sql and 'key_name' in idx_sql and 'UNIQUE' in idx_sql.upper():
            print(f"✅ 已存在组合唯一约束: {idx_name}")
            has_composite_unique = True
            break
    
    # 如果没有组合唯一约束，创建一个
    if not has_composite_unique:
        print("\n创建 (provider_name, key_name) 组合唯一约束...")
        try:
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS _provider_key_name_uc 
                ON ai_provider_configs(provider_name, key_name)
            """)
            print("✅ 组合唯一约束已创建")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e).lower():
                print("✅ 组合唯一约束已存在")
            else:
                raise
    
    # 验证数据完整性
    print("\n验证数据完整性...")
    cursor.execute("SELECT provider_name, key_name, COUNT(*) as cnt FROM ai_provider_configs GROUP BY provider_name, key_name HAVING cnt > 1")
    duplicates = cursor.fetchall()
    if duplicates:
        print("⚠️  发现重复的 (provider_name, key_name) 组合:")
        for provider, key_name, cnt in duplicates:
            print(f"  - {provider}/{key_name}: {cnt} 条记录")
        print("  建议：删除重复记录或重命名 key_name")
    else:
        print("✅ 没有重复的 (provider_name, key_name) 组合")
    
    conn.commit()
    conn.close()
    
    print("\n✅ 数据库唯一约束修复完成")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ 修复失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
  echo ""
  echo "=========================================="
  echo "✅ 数据库修复成功"
  echo "=========================================="
  echo ""
  echo "现在可以重启后端服务:"
  echo "  sudo systemctl restart luckyred-api"
else
  echo ""
  echo "=========================================="
  echo "❌ 数据库修复失败"
  echo "=========================================="
  exit 1
fi

