import os
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# 在導入 security 模組之前修補 passlib 的 bcrypt 初始化
# 避免 passlib 初始化時使用超過 72 字節的測試密碼
# 同時修復 bcrypt 版本兼容性問題
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

# 修復 bcrypt 版本兼容性問題（bcrypt.__about__ 不存在）
try:
    import bcrypt as _bcrypt_module
    # 如果 bcrypt 沒有 __about__ 屬性，創建一個模擬的
    if not hasattr(_bcrypt_module, '__about__'):
        class _MockAbout:
            __version__ = getattr(_bcrypt_module, '__version__', '4.0.0')
        _bcrypt_module.__about__ = _MockAbout()
except ImportError:
    pass  # bcrypt 未安裝，跳過

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db import Base, SessionLocal, engine
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    settings = get_settings()
    database_url = settings.database_url
    
    # 检查是否是 PostgreSQL（需要 CASCADE 删除）
    is_postgresql = database_url.startswith("postgresql://") or database_url.startswith("postgres://")
    
    # 如果是 SQLite，尝试删除文件
    if not is_postgresql:
        db_path = Path(database_url.split("///")[-1])
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

    # 删除所有表（PostgreSQL 需要 CASCADE）
    if is_postgresql:
        # PostgreSQL 需要先删除外键约束，然后删除表
        from sqlalchemy import text
        with engine.connect() as conn:
            # 禁用外键检查（PostgreSQL 不支持，需要手动删除约束）
            # 使用 CASCADE 删除所有表
            conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
            conn.commit()
    else:
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

