#!/usr/bin/env python3
"""
數據庫初始化腳本
創建所有缺失的表
"""
import sys
import logging
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_database():
    """初始化數據庫，創建所有表"""
    logger.info("開始初始化數據庫...")
    
    try:
        # 導入數據庫引擎和 Base
        from app.db import engine, Base
        
        # 導入所有模型以確保它們被註冊到 Base.metadata
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
        
        logger.info(f"已註冊的表: {list(Base.metadata.tables.keys())}")
        
        # 創建所有表
        logger.info("正在創建數據庫表...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ 數據庫表創建成功！")
        
        # 驗證表是否存在
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"當前數據庫中的表: {existing_tables}")
        
        # 檢查關鍵表
        required_tables = [
            'group_ai_accounts',
            'group_ai_scripts',
            'group_ai_automation_tasks',
            'group_ai_dialogue_history',
            'group_ai_redpacket_logs',
            'group_ai_metrics',
        ]
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        if missing_tables:
            logger.warning(f"⚠️ 缺失的表: {missing_tables}")
        else:
            logger.info("✅ 所有關鍵表都已存在")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 數據庫初始化失敗: {e}", exc_info=True)
        return False


def create_default_admin():
    """創建默認管理員用戶"""
    logger.info("檢查是否需要創建默認管理員...")
    
    try:
        from app.db import SessionLocal
        from app.models.user import User
        from app.models.role import Role
        from app.core.security import get_password_hash
        from app.core.config import get_settings
        
        settings = get_settings()
        db = SessionLocal()
        
        try:
            # 檢查是否已有管理員
            admin = db.query(User).filter(User.email == settings.admin_default_email).first()
            if admin:
                logger.info(f"管理員用戶已存在: {settings.admin_default_email}")
                return True
            
            # 創建管理員角色
            admin_role = db.query(Role).filter(Role.name == "admin").first()
            if not admin_role:
                admin_role = Role(name="admin", description="系統管理員")
                db.add(admin_role)
                db.commit()
                logger.info("✅ 創建管理員角色")
            
            # 創建管理員用戶
            admin_user = User(
                email=settings.admin_default_email,
                hashed_password=get_password_hash(settings.admin_default_password),
                is_active=True
            )
            admin_user.roles.append(admin_role)
            db.add(admin_user)
            db.commit()
            
            logger.info(f"✅ 創建默認管理員: {settings.admin_default_email}")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ 創建管理員失敗: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("數據庫初始化腳本")
    print("=" * 60)
    
    success = init_database()
    if success:
        create_default_admin()
        print("\n✅ 數據庫初始化完成！現在可以啟動後端服務。")
    else:
        print("\n❌ 數據庫初始化失敗，請檢查錯誤日誌。")
        sys.exit(1)
