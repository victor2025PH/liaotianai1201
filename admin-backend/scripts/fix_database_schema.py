#!/usr/bin/env python3
"""
修復數據庫結構問題
解決類型不匹配問題
"""
import sys
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db import engine, SessionLocal
from sqlalchemy import text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_structure():
    """檢查表結構"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    logger.info(f"數據庫中的表: {', '.join(tables)}")
    
    # 檢查 users 表
    if 'users' in tables:
        columns = inspector.get_columns('users')
        logger.info("users 表的列:")
        for col in columns:
            logger.info(f"  {col['name']}: {col['type']}")
    
    return tables

def fix_users_table():
    """修復 users 表結構"""
    logger.info("檢查 users 表結構...")
    
    with engine.connect() as conn:
        # 檢查 users.id 的類型
        result = conn.execute(text("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'id'
        """))
        
        row = result.fetchone()
        if row:
            current_type = row[0]
            logger.info(f"users.id 當前類型: {current_type}")
            
            if current_type == 'text':
                logger.warning("users.id 是 text 類型，需要改為 integer")
                logger.info("嘗試修復...")
                
                try:
                    # 創建臨時表
                    conn.execute(text("""
                        CREATE TABLE users_new (
                            id SERIAL PRIMARY KEY,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            full_name VARCHAR(255),
                            hashed_password VARCHAR(255) NOT NULL,
                            is_active BOOLEAN DEFAULT TRUE,
                            is_superuser BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    
                    # 複製數據（如果有的話）
                    conn.execute(text("""
                        INSERT INTO users_new (email, full_name, hashed_password, is_active, is_superuser, created_at, updated_at)
                        SELECT email, full_name, hashed_password, is_active, is_superuser, created_at, updated_at
                        FROM users
                    """))
                    
                    # 刪除舊表
                    conn.execute(text("DROP TABLE users CASCADE"))
                    
                    # 重命名新表
                    conn.execute(text("ALTER TABLE users_new RENAME TO users"))
                    
                    # 創建索引
                    conn.execute(text("CREATE INDEX ix_users_id ON users (id)"))
                    conn.execute(text("CREATE UNIQUE INDEX ix_users_email ON users (email)"))
                    
                    conn.commit()
                    logger.info("✅ users 表結構已修復")
                    return True
                except Exception as e:
                    logger.error(f"修復失敗: {e}")
                    conn.rollback()
                    return False
            else:
                logger.info("users.id 類型正確")
                return True
        else:
            logger.info("users 表不存在，將在初始化時創建")
            return True

def main():
    """主函數"""
    logger.info("=" * 60)
    logger.info("🔧 修復數據庫結構")
    logger.info("=" * 60)
    logger.info("")
    
    try:
        # 檢查現有表
        tables = check_table_structure()
        logger.info("")
        
        # 修復 users 表
        if 'users' in tables:
            fix_users_table()
        else:
            logger.info("users 表不存在，將在初始化時創建")
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ 修復完成")
        logger.info("=" * 60)
        logger.info("")
        logger.info("現在可以運行: python init_db_tables.py")
        
        return 0
    except Exception as e:
        logger.error(f"❌ 錯誤: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())

