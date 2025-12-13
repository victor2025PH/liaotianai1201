#!/bin/bash
# ============================================================
# 修复多个 Key 同时激活的问题
# ============================================================

set -e

echo "=========================================="
echo "修复多个 Key 同时激活的问题"
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

# 修复多个 Key 同时激活的问题
echo "修复多个 Key 同时激活的问题..."
python3 << 'PYTHON_SCRIPT'
import sqlite3
import sys

db_path = "admin.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查每个提供商是否有多个激活的 Key
    providers = ["openai", "gemini", "grok"]
    
    for provider in providers:
        print(f"\n检查 {provider} 的激活 Key...")
        
        # 查找所有激活的 Key
        cursor.execute("""
            SELECT id, key_name, is_active 
            FROM ai_provider_configs 
            WHERE provider_name = ? AND is_active = 1
        """, (provider,))
        active_keys = cursor.fetchall()
        
        if len(active_keys) > 1:
            print(f"  ⚠️  发现 {len(active_keys)} 个激活的 Key:")
            for key_id, key_name, _ in active_keys:
                print(f"    - {key_name} (ID: {key_id})")
            
            # 只保留第一个有效的 Key 为激活状态
            # 优先选择有效的 Key
            cursor.execute("""
                SELECT id, key_name, is_valid 
                FROM ai_provider_configs 
                WHERE provider_name = ? AND is_active = 1
                ORDER BY is_valid DESC, created_at ASC
                LIMIT 1
            """, (provider,))
            keep_key = cursor.fetchone()
            
            if keep_key:
                keep_key_id = keep_key[0]
                keep_key_name = keep_key[1]
                print(f"  ✅ 保留激活状态: {keep_key_name} (ID: {keep_key_id})")
                
                # 取消激活其他 Key
                cursor.execute("""
                    UPDATE ai_provider_configs 
                    SET is_active = 0 
                    WHERE provider_name = ? AND id != ?
                """, (provider, keep_key_id))
                
                # 更新 active_keys 设置
                cursor.execute("SELECT active_keys FROM ai_provider_settings WHERE id = 'singleton'")
                result = cursor.fetchone()
                if result:
                    import json
                    active_keys_dict = json.loads(result[0]) if result[0] else {}
                    active_keys_dict[provider] = keep_key_id
                    cursor.execute("""
                        UPDATE ai_provider_settings 
                        SET active_keys = ?, updated_at = datetime('now')
                        WHERE id = 'singleton'
                    """, (json.dumps(active_keys_dict),))
                    print(f"  ✅ 已更新 active_keys 设置")
            else:
                print(f"  ⚠️  未找到要保留的 Key")
        elif len(active_keys) == 1:
            key_id, key_name, _ = active_keys[0]
            print(f"  ✅ 只有一个激活的 Key: {key_name} (ID: {key_id})")
            
            # 确保 active_keys 设置正确
            cursor.execute("SELECT active_keys FROM ai_provider_settings WHERE id = 'singleton'")
            result = cursor.fetchone()
            if result:
                import json
                active_keys_dict = json.loads(result[0]) if result[0] else {}
                if active_keys_dict.get(provider) != key_id:
                    active_keys_dict[provider] = key_id
                    cursor.execute("""
                        UPDATE ai_provider_settings 
                        SET active_keys = ?, updated_at = datetime('now')
                        WHERE id = 'singleton'
                    """, (json.dumps(active_keys_dict),))
                    print(f"  ✅ 已更新 active_keys 设置")
        else:
            print(f"  ⚠️  没有激活的 Key，尝试激活第一个有效的 Key...")
            cursor.execute("""
                SELECT id, key_name, is_valid 
                FROM ai_provider_configs 
                WHERE provider_name = ?
                ORDER BY is_valid DESC, created_at ASC
                LIMIT 1
            """, (provider,))
            first_key = cursor.fetchone()
            
            if first_key:
                first_key_id = first_key[0]
                first_key_name = first_key[1]
                cursor.execute("""
                    UPDATE ai_provider_configs 
                    SET is_active = 1 
                    WHERE id = ?
                """, (first_key_id,))
                
                # 更新 active_keys 设置
                cursor.execute("SELECT active_keys FROM ai_provider_settings WHERE id = 'singleton'")
                result = cursor.fetchone()
                if result:
                    import json
                    active_keys_dict = json.loads(result[0]) if result[0] else {}
                    active_keys_dict[provider] = first_key_id
                    cursor.execute("""
                        UPDATE ai_provider_settings 
                        SET active_keys = ?, updated_at = datetime('now')
                        WHERE id = 'singleton'
                    """, (json.dumps(active_keys_dict),))
                    print(f"  ✅ 已激活第一个 Key: {first_key_name} (ID: {first_key_id})")
    
    conn.commit()
    conn.close()
    
    print("\n✅ 修复完成")
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
  echo "✅ 修复成功"
  echo "=========================================="
  echo ""
  echo "现在可以重启后端服务:"
  echo "  sudo systemctl restart luckyred-api"
else
  echo ""
  echo "=========================================="
  echo "❌ 修复失败"
  echo "=========================================="
  exit 1
fi

