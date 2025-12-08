#!/usr/bin/env python
"""强制重置管理员密码"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from app.db import SessionLocal, engine, Base
from app.crud.user import get_user_by_email
from app.core.config import get_settings
from app.core.security import get_password_hash, verify_password

# 确保所有表已创建
from app.models import user, role, permission
from app.models import group_ai
Base.metadata.create_all(bind=engine)

settings = get_settings()
db = SessionLocal()

try:
    admin = get_user_by_email(db, email=settings.admin_default_email)
    if admin:
        print(f"找到用户: {admin.email}")
        print(f"  当前密码验证: {verify_password('changeme123', admin.hashed_password)}")
        print("  正在强制更新密码...")
        admin.hashed_password = get_password_hash('changeme123')
        admin.is_active = True
        admin.is_superuser = True
        db.commit()
        db.refresh(admin)
        print(f"  新密码验证: {verify_password('changeme123', admin.hashed_password)}")
        print("\n[SUCCESS] 密码已强制更新！")
    else:
        print("[ERROR] 用户不存在")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

