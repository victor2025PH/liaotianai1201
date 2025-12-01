#!/bin/bash
# 診斷和修復數據庫表缺失問題

set -e

cd /home/ubuntu/liaotian/deployment-package/admin-backend

echo "=== 【步驟 1】檢查數據庫文件 ==="
find . -name "*.db" -type f 2>/dev/null | head -5 || echo "未找到 .db 文件"

echo ""
echo "=== 【步驟 2】檢查現有表 ==="
source /home/ubuntu/liaotian/admin-backend/.venv/bin/activate
export PYTHONPATH=/home/ubuntu/liaotian/deployment-package

python3 << 'PYEOF'
from app.db import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"數據庫中的表 ({len(tables)} 個):")
for table in tables:
    print(f"  - {table}")

if 'group_ai_accounts' not in tables:
    print("\n❌ group_ai_accounts 表不存在，需要初始化")
    NEED_INIT = True
else:
    print("\n✅ group_ai_accounts 表存在")
    NEED_INIT = False
PYEOF

echo ""
echo "=== 【步驟 3】初始化數據庫表 ==="
if [ -f "init_db_tables.py" ]; then
    echo "使用 init_db_tables.py 初始化..."
    python3 init_db_tables.py
else
    echo "init_db_tables.py 不存在，手動創建表..."
    python3 << 'PYEOF'
from app.db import engine, Base
from app.models import group_ai
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    logger.info("開始創建數據庫表...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ 數據庫表創建成功！")
    
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info(f"數據庫中的表: {', '.join(tables)}")
    
    # 檢查關鍵表
    required_tables = [
        'group_ai_scripts',
        'group_ai_accounts',
        'group_ai_script_versions',
        'group_ai_dialogue_history',
        'group_ai_redpacket_logs',
    ]
    
    missing_tables = [t for t in required_tables if t not in tables]
    if missing_tables:
        logger.error(f"❌ 缺少表: {', '.join(missing_tables)}")
    else:
        logger.info("✅ 所有必需的表都已創建！")
except Exception as e:
    logger.error(f"❌ 創建失敗: {e}", exc_info=True)
PYEOF
fi

echo ""
echo "=== 【步驟 4】驗證修復 ==="
python3 << 'PYEOF'
from app.db import SessionLocal
from app.models.group_ai import GroupAIAccount

db = SessionLocal()
try:
    count = db.query(GroupAIAccount).count()
    print(f"✅ 數據庫表正常，共有 {count} 個賬號")
    
    accounts = db.query(GroupAIAccount).all()
    if accounts:
        print("\n數據庫中的賬號:")
        for acc in accounts:
            print(f"  - {acc.account_id}: {acc.name or '無名稱'}")
    else:
        print("\n數據庫中沒有賬號（表已創建但為空）")
except Exception as e:
    print(f"❌ 查詢失敗: {e}")
finally:
    db.close()
PYEOF

echo ""
echo "=== 診斷和修復完成 ==="
