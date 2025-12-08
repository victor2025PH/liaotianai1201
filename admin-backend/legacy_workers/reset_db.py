#!/usr/bin/env python3
"""
數據庫重置腳本
刪除並重新創建所有表
"""
import sys
import os
import logging
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reset_database():
    """重置數據庫，刪除並重新創建所有表"""
    logger.info("=" * 60)
    logger.info("數據庫重置腳本")
    logger.info("=" * 60)
    
    try:
        # 獲取數據庫路徑
        project_root = Path(__file__).parent
        db_path = project_root / "admin.db"
        
        # 刪除現有數據庫
        if db_path.exists():
            logger.info(f"刪除現有數據庫: {db_path}")
            os.remove(db_path)
            logger.info("✅ 數據庫已刪除")
        else:
            logger.info("數據庫文件不存在，將創建新數據庫")
        
        # 導入數據庫引擎和 Base
        from app.db import engine, Base
        
        # 導入所有模型
        logger.info("導入所有模型...")
        
        # 基礎模型
        from app.models.role import Role
        from app.models.user import User
        from app.models.permission import Permission
        from app.models.user_role import user_role_table
        from app.models.role_permission import role_permission_table
        from app.models.audit_log import AuditLog
        from app.models.notification import (
            NotificationConfig,
            Notification,
            NotificationTemplate,
        )
        from app.models.telegram_registration import (
            UserRegistration,
            SessionFile,
            AntiDetectionLog,
        )
        
        # Group AI 模型
        from app.models.group_ai import (
            GroupAIAccount,
            GroupAIScript,
            GroupAIScriptVersion,
            AllocationHistory,
            GroupAIDialogueHistory,
            GroupAIRedpacketLog,
            GroupAIMetric,
            GroupAIAlertRule,
            GroupAIRoleAssignmentScheme,
            GroupAIRoleAssignmentHistory,
            GroupAIAutomationTask,
            GroupAIAutomationTaskLog,
        )
        
        logger.info(f"已註冊的表: {len(Base.metadata.tables)} 個")
        
        # 創建所有表
        logger.info("正在創建數據庫表...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 數據庫表創建成功！")
        
        # 驗證表是否存在
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"當前數據庫中的表: {len(existing_tables)} 個")
        
        # 創建默認管理員
        create_default_admin()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 數據庫重置失敗: {e}", exc_info=True)
        return False


def create_default_admin():
    """創建默認管理員用戶"""
    logger.info("創建默認管理員...")
    
    try:
        from app.db import SessionLocal
        from app.models.user import User
        from app.models.role import Role
        from app.core.security import get_password_hash
        from app.core.config import get_settings
        
        settings = get_settings()
        db = SessionLocal()
        
        try:
            # 創建管理員角色
            admin_role = Role(name="admin", description="系統管理員")
            db.add(admin_role)
            db.flush()
            
            # 創建管理員用戶
            admin_user = User(
                email=settings.admin_default_email,
                full_name="Administrator",
                hashed_password=get_password_hash(settings.admin_default_password),
                is_active=True,
                is_superuser=True
            )
            admin_user.roles.append(admin_role)
            db.add(admin_user)
            db.commit()
            
            logger.info(f"✅ 創建默認管理員: {settings.admin_default_email}")
            logger.info(f"   密碼: {settings.admin_default_password}")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ 創建管理員失敗: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    print()
    print("⚠️  警告：此操作將刪除所有現有數據！")
    print()
    
    confirm = input("確認重置數據庫？(輸入 'yes' 確認): ")
    if confirm.lower() == 'yes':
        success = reset_database()
        if success:
            print("\n✅ 數據庫重置完成！現在可以啟動後端服務。")
        else:
            print("\n❌ 數據庫重置失敗，請檢查錯誤日誌。")
            sys.exit(1)
    else:
        print("已取消操作。")
