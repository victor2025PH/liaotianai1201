import os
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# 在導入 security 模組之前修補 passlib 的 bcrypt 初始化
# 避免 passlib 初始化時使用超過 72 字節的測試密碼
import passlib.handlers.bcrypt as bcrypt_handler

# 保存原始的 detect_wrap_bug 函數
_original_detect_wrap_bug = getattr(bcrypt_handler, 'detect_wrap_bug', None)

def _patched_detect_wrap_bug(ident):
    """修補的 detect_wrap_bug，跳過檢測以避免使用超過 72 字節的密碼"""
    # 直接返回 False，跳過檢測
    return False

# 在導入 security 之前替換 detect_wrap_bug 函數
if _original_detect_wrap_bug:
    bcrypt_handler.detect_wrap_bug = _patched_detect_wrap_bug

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db import Base, SessionLocal, engine
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    db_path = Path(get_settings().database_url.split("///")[-1])
    if db_path.exists():
        try:
            os.remove(db_path)
        except PermissionError:
            # 如果文件被占用，尝试使用临时数据库
            import tempfile
            db_path = Path(tempfile.gettempdir()) / "test_admin.db"
            # 更新设置使用临时数据库
            import app.core.config
            app.core.config.get_settings.cache_clear()
            os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    settings = get_settings()
    db = SessionLocal()
    try:
        admin_role = Role(name="admin", description="Administrator")
        permission_all = Permission(code="admin:all", description="Full access")
        admin_role.permissions.append(permission_all)

        # 確保測試密碼不超過 bcrypt 的 72 字節限制
        # 使用固定的短密碼，避免 passlib 初始化 bcrypt 時的內部測試密碼過長
        # 強制使用短密碼（不超過 72 字節），避免 bcrypt 庫初始化問題
        test_password = "testpass123"  # 固定使用短密碼，確保不超過 72 字節

        admin_user = User(
            email=settings.admin_default_email,
            full_name="Default Admin",
            hashed_password=get_password_hash(test_password),
            is_active=True,
            is_superuser=True,
        )
        admin_user.roles.append(admin_role)

        db.add(admin_role)
        db.add(permission_all)
        db.add(admin_user)
        db.commit()
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=engine)

