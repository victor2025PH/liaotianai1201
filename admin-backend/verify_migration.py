#!/usr/bin/env python3
"""验证数据库迁移是否成功"""
import sys
from sqlalchemy import text
from app.db import SessionLocal
from app.models.telegram_registration import UserRegistration, SessionFile, AntiDetectionLog

def verify_tables():
    """验证表是否创建"""
    db = SessionLocal()
    try:
        # 检查表是否存在
        result = db.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name IN ('user_registrations', 'session_files', 'anti_detection_logs')
        """))
        tables = [row[0] for row in result]
        
        print("=" * 50)
        print("数据库迁移验证")
        print("=" * 50)
        
        expected_tables = ['user_registrations', 'session_files', 'anti_detection_logs']
        all_exist = True
        
        for table in expected_tables:
            exists = table in tables
            status = "[OK]" if exists else "[FAIL]"
            print(f"{status} {table}: {'存在' if exists else '不存在'}")
            if not exists:
                all_exist = False
        
        print("=" * 50)
        
        if all_exist:
            print("[OK] 所有表已成功创建！")
            
            # 测试模型导入
            try:
                print("\n测试模型导入...")
                print(f"[OK] UserRegistration: {UserRegistration.__tablename__}")
                print(f"[OK] SessionFile: {SessionFile.__tablename__}")
                print(f"[OK] AntiDetectionLog: {AntiDetectionLog.__tablename__}")
                print("\n[OK] 所有模型导入成功！")
                return True
            except Exception as e:
                print(f"[FAIL] 模型导入失败: {e}")
                return False
        else:
            print("[FAIL] 部分表未创建，请检查迁移")
            return False
            
    except Exception as e:
        print(f"[FAIL] 验证失败: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = verify_tables()
    sys.exit(0 if success else 1)

