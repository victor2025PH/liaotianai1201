#!/usr/bin/env python3
"""
本地開發啟動腳本
強制使用 SQLite 數據庫
"""
import os
import sys
import subprocess
from pathlib import Path

# 設置工作目錄
os.chdir(Path(__file__).parent)

# 強制使用 SQLite（覆蓋任何環境變量）
os.environ["DATABASE_URL"] = "sqlite:///./admin.db"

# 刪除舊數據庫（如果存在問題）
db_path = Path("admin.db")
if db_path.exists():
    print(f"發現現有數據庫: {db_path}")
    response = input("是否刪除並重建？(y/n): ")
    if response.lower() == 'y':
        os.remove(db_path)
        print("✅ 已刪除舊數據庫")

# 初始化數據庫
print("\n正在初始化數據庫...")

# 導入並初始化
sys.path.insert(0, str(Path(__file__).parent))

from app.db import engine, Base

# 導入所有模型
from app.models.role import Role
from app.models.user import User
from app.models.permission import Permission
from app.models.user_role import user_role_table
from app.models.role_permission import role_permission_table
from app.models.audit_log import AuditLog
from app.models.notification import NotificationConfig, Notification, NotificationTemplate
from app.models.telegram_registration import UserRegistration, SessionFile, AntiDetectionLog
from app.models.group_ai import (
    GroupAIAccount, GroupAIScript, GroupAIScriptVersion,
    AllocationHistory, GroupAIDialogueHistory, GroupAIRedpacketLog,
    GroupAIMetric, GroupAIAlertRule, GroupAIRoleAssignmentScheme,
    GroupAIRoleAssignmentHistory, GroupAIAutomationTask, GroupAIAutomationTaskLog
)

# 創建表
print("創建數據庫表...")
Base.metadata.create_all(bind=engine)
print("✅ 數據庫表創建成功！")

# 創建管理員
from app.db import SessionLocal
from app.core.security import get_password_hash

db = SessionLocal()
try:
    # 檢查是否已有管理員
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        # 創建角色
        admin_role = Role(name="admin", description="系統管理員")
        db.add(admin_role)
        db.flush()
        
        # 創建用戶
        admin_user = User(
            email="admin@example.com",
            full_name="Administrator",
            hashed_password=get_password_hash("admin123456"),
            is_active=True,
            is_superuser=True
        )
        admin_user.roles.append(admin_role)
        db.add(admin_user)
        db.commit()
        print("✅ 創建管理員: admin@example.com / admin123456")
    else:
        print("管理員已存在")
finally:
    db.close()

print("\n✅ 數據庫初始化完成！")
print("\n正在啟動服務...")

# 啟動 uvicorn
subprocess.run([
    sys.executable, "-m", "uvicorn", 
    "app.main:app", 
    "--host", "0.0.0.0", 
    "--port", "8000", 
    "--reload"
])
