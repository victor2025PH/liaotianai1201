"""檢查數據庫狀態"""
from sqlalchemy import create_engine, text, inspect
from app.core.config import get_settings
from app.db import engine

settings = get_settings()
print(f"配置的數據庫URL: {settings.database_url}")
print(f"實際使用的數據庫URL: {engine.url}")

# 使用實際的engine（已經處理了PostgreSQL回退到SQLite）
inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"\n現有表 ({len(tables)}):")
for table in sorted(tables):
    print(f"  - {table}")

print(f"\ngroup_ai_scripts存在: {'group_ai_scripts' in tables}")
print(f"group_ai_accounts存在: {'group_ai_accounts' in tables}")

# 檢查alembic版本
try:
    from alembic.config import Config
    from alembic import script
    from alembic.runtime.migration import MigrationContext
    
    alembic_cfg = Config('alembic.ini')
    script_dir = script.ScriptDirectory.from_config(alembic_cfg)
    head_rev = script_dir.get_current_head()
    
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        current_rev = context.get_current_revision()
        
    print(f"\nAlembic版本:")
    print(f"  當前版本: {current_rev}")
    print(f"  最新版本: {head_rev}")
    print(f"  需要升級: {current_rev != head_rev}")
except Exception as e:
    print(f"\n檢查Alembic版本失敗: {e}")

