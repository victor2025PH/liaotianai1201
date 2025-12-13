#!/bin/bash
# ============================================================
# 修复数据库列缺失问题
# ============================================================

set -e

echo "=========================================="
echo "修复数据库列缺失问题"
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

# 检查并添加缺失的列
echo "检查并添加缺失的列..."
python3 << 'PYTHON_SCRIPT'
import sqlite3
import sys

db_path = "admin.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取表结构
    cursor.execute("PRAGMA table_info(ai_provider_configs)")
    columns = {row[1]: row for row in cursor.fetchall()}
    
    print("当前 ai_provider_configs 表的列:")
    for col_name in columns.keys():
        print(f"  - {col_name}")
    print("")
    
    # 检查并添加 key_name 列
    if 'key_name' not in columns:
        print("添加 key_name 列...")
        cursor.execute("ALTER TABLE ai_provider_configs ADD COLUMN key_name VARCHAR(100) DEFAULT 'default'")
        # 更新现有数据
        cursor.execute("UPDATE ai_provider_configs SET key_name = 'default' WHERE key_name IS NULL")
        print("✅ key_name 列已添加")
    else:
        print("✅ key_name 列已存在")
    
    # 检查并添加 is_active 列
    if 'is_active' not in columns:
        print("添加 is_active 列...")
        cursor.execute("ALTER TABLE ai_provider_configs ADD COLUMN is_active BOOLEAN DEFAULT 1")
        # 更新现有数据（默认激活第一个 Key）
        cursor.execute("UPDATE ai_provider_configs SET is_active = 1 WHERE is_active IS NULL")
        print("✅ is_active 列已添加")
    else:
        print("✅ is_active 列已存在")
    
    # 检查 ai_provider_settings 表
    cursor.execute("PRAGMA table_info(ai_provider_settings)")
    settings_columns = {row[1]: row for row in cursor.fetchall()}
    
    print("")
    print("当前 ai_provider_settings 表的列:")
    for col_name in settings_columns.keys():
        print(f"  - {col_name}")
    print("")
    
    # 检查并添加 active_keys 列
    if 'active_keys' not in settings_columns:
        print("添加 active_keys 列...")
        cursor.execute("ALTER TABLE ai_provider_settings ADD COLUMN active_keys TEXT DEFAULT '{}'")
        print("✅ active_keys 列已添加")
    else:
        print("✅ active_keys 列已存在")
    
    conn.commit()
    conn.close()
    
    print("")
    print("✅ 数据库列修复完成")
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

