#!/usr/bin/env python
"""檢查數據持久化問題"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from app.db import SessionLocal, engine, Base
from app.models.group_ai import GroupAIScript, GroupAIAutomationTask
from sqlalchemy import inspect, text
import os

def main():
    print("=" * 60)
    print("數據持久化檢查")
    print("=" * 60)
    
    # 檢查數據庫文件
    db_path = Path("./admin.db").resolve()
    print(f"\n[1] 數據庫文件檢查")
    print(f"  路徑: {db_path}")
    print(f"  存在: {db_path.exists()}")
    if db_path.exists():
        print(f"  大小: {db_path.stat().st_size} 字節")
    
    # 檢查數據庫表
    print(f"\n[2] 數據庫表檢查")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"  表數量: {len(tables)}")
    for table in sorted(tables):
        print(f"    - {table}")
    
    # 檢查劇本表
    db = SessionLocal()
    try:
        print(f"\n[3] 劇本數據檢查")
        scripts = db.query(GroupAIScript).all()
        print(f"  劇本數量: {len(scripts)}")
        if scripts:
            for s in scripts[:5]:
                print(f"    - ID: {s.script_id}, 名稱: {s.name}, 狀態: {s.status}")
        else:
            print("  [WARNING] 沒有找到任何劇本")
        
        # 檢查任務表
        print(f"\n[4] 自動化任務數據檢查")
        tasks = db.query(GroupAIAutomationTask).all()
        print(f"  任務數量: {len(tasks)}")
        if tasks:
            for t in tasks[:5]:
                print(f"    - ID: {t.id}, 名稱: {t.name}, 類型: {t.task_type}, 啟用: {t.enabled}")
        else:
            print("  ⚠️  沒有找到任何任務")
        
        # 檢查數據庫連接配置
        print(f"\n[5] 數據庫連接配置")
        from app.core.config import get_settings
        settings = get_settings()
        print(f"  數據庫URL: {settings.database_url}")
        print(f"  當前工作目錄: {os.getcwd()}")
        
        # 檢查是否有其他數據庫文件
        print(f"\n[6] 查找所有可能的數據庫文件")
        current_dir = Path.cwd()
        db_files = list(current_dir.glob("*.db")) + list(current_dir.glob("**/*.db"))
        print(f"  找到 {len(db_files)} 個 .db 文件:")
        for db_file in db_files[:10]:
            size = db_file.stat().st_size
            print(f"    - {db_file.relative_to(current_dir)} ({size} 字節)")
        
    except Exception as e:
        print(f"  錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("建議:")
    print("1. 確保數據庫文件路徑是絕對路徑或穩定的相對路徑")
    print("2. 檢查服務啟動時的工作目錄")
    print("3. 確認 db.commit() 被正確調用")
    print("4. 檢查是否有多個數據庫文件（可能使用了不同的數據庫）")
    print("=" * 60)

if __name__ == "__main__":
    main()

