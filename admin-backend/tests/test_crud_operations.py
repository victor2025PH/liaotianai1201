"""
數據庫 CRUD 操作測試
測試 app/crud 模組中的所有 CRUD 函數
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime

from app.db import SessionLocal
from app.crud import user, permission
from app.crud.user import create_role
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.core.security import verify_password


@pytest.fixture
def db_session():
    """創建數據庫會話"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


class TestUserCRUD:
    """用戶 CRUD 操作測試"""

    def test_get_user_by_email_exists(self, db_session: Session):
        """測試根據郵箱獲取用戶（存在）"""
        # 使用 conftest.py 中創建的測試用戶
        settings = pytest.importorskip("app.core.config").get_settings()
        user_obj = user.get_user_by_email(db_session, email=settings.admin_default_email)
        assert user_obj is not None
        assert user_obj.email == settings.admin_default_email

    def test_get_user_by_email_not_exists(self, db_session: Session):
        """測試根據郵箱獲取用戶（不存在）"""
        user_obj = user.get_user_by_email(db_session, email="nonexistent@example.com")
        assert user_obj is None

    def test_create_user_success(self, db_session: Session):
        """測試創建用戶（成功）"""
        import random
        unique_email = f"test_user_{random.randint(10000, 99999)}@example.com"
        
        new_user = user.create_user(
            db_session,
            email=unique_email,
            password="testpass123",
            full_name="Test User",
            is_superuser=False
        )
        
        assert new_user is not None
        assert new_user.email == unique_email
        assert new_user.full_name == "Test User"
        assert new_user.is_superuser is False
        assert new_user.is_active is True
        assert verify_password("testpass123", new_user.hashed_password)
        
        # 清理
        db_session.delete(new_user)
        db_session.commit()

    def test_create_user_duplicate_email(self, db_session: Session):
        """測試創建用戶（重複郵箱）"""
        settings = pytest.importorskip("app.core.config").get_settings()
        existing_email = settings.admin_default_email
        
        # 嘗試創建相同郵箱的用戶（應該會失敗或返回現有用戶）
        with pytest.raises(Exception):
            user.create_user(
                db_session,
                email=existing_email,
                password="newpass123"
            )

    def test_get_user_by_id_exists(self, db_session: Session):
        """測試根據ID獲取用戶（存在）"""
        settings = pytest.importorskip("app.core.config").get_settings()
        user_obj = user.get_user_by_email(db_session, email=settings.admin_default_email)
        assert user_obj is not None
        
        user_by_id = user.get_user_by_id(db_session, user_id=user_obj.id)
        assert user_by_id is not None
        assert user_by_id.id == user_obj.id
        assert user_by_id.email == user_obj.email

    def test_get_user_by_id_not_exists(self, db_session: Session):
        """測試根據ID獲取用戶（不存在）"""
        user_obj = user.get_user_by_id(db_session, user_id=99999)
        assert user_obj is None

    def test_update_user_success(self, db_session: Session):
        """測試更新用戶（成功）"""
        import random
        unique_email = f"test_update_{random.randint(10000, 99999)}@example.com"
        
        # 創建用戶
        new_user = user.create_user(
            db_session,
            email=unique_email,
            password="testpass123",
            full_name="Original Name"
        )
        
        # 更新用戶
        updated_user = user.update_user(
            db_session,
            user=new_user,
            full_name="Updated Name",
            is_active=False
        )
        
        assert updated_user.full_name == "Updated Name"
        assert updated_user.is_active is False
        assert updated_user.email == unique_email  # 郵箱未變
        
        # 清理
        db_session.delete(updated_user)
        db_session.commit()

    def test_update_user_password(self, db_session: Session):
        """測試更新用戶密碼"""
        import random
        unique_email = f"test_password_{random.randint(10000, 99999)}@example.com"
        
        # 創建用戶
        new_user = user.create_user(
            db_session,
            email=unique_email,
            password="oldpass123"
        )
        
        # 更新密碼
        updated_user = user.update_user_password(
            db_session,
            user=new_user,
            new_password="newpass456"
        )
        
        assert verify_password("newpass456", updated_user.hashed_password)
        assert not verify_password("oldpass123", updated_user.hashed_password)
        
        # 清理
        db_session.delete(updated_user)
        db_session.commit()

    def test_delete_user_success(self, db_session: Session):
        """測試刪除用戶（成功）"""
        import random
        unique_email = f"test_delete_{random.randint(10000, 99999)}@example.com"
        
        # 創建用戶
        new_user = user.create_user(
            db_session,
            email=unique_email,
            password="testpass123"
        )
        user_id = new_user.id
        
        # 刪除用戶
        result = user.delete_user(db_session, user_id=user_id)
        assert result is True
        
        # 驗證用戶已刪除
        deleted_user = user.get_user_by_id(db_session, user_id=user_id)
        assert deleted_user is None

    def test_delete_user_not_exists(self, db_session: Session):
        """測試刪除用戶（不存在）"""
        result = user.delete_user(db_session, user_id=99999)
        assert result is False


class TestRoleCRUD:
    """角色 CRUD 操作測試"""

    def test_create_role_success(self, db_session: Session):
        """測試創建角色（成功）"""
        import random
        unique_name = f"test_role_{random.randint(10000, 99999)}"
        
        new_role = create_role(
            db_session,
            name=unique_name,
            description="Test Role"
        )
        
        assert new_role is not None
        assert new_role.name == unique_name
        assert new_role.description == "Test Role"
        
        # 清理
        db_session.delete(new_role)
        db_session.commit()

    def test_create_role_duplicate(self, db_session: Session):
        """測試創建角色（重複名稱）"""
        import random
        unique_name = f"test_role_dup_{random.randint(10000, 99999)}"
        
        # 第一次創建
        role1 = create_role(db_session, name=unique_name)
        
        # 第二次創建相同名稱的角色（應該返回現有角色）
        role2 = create_role(db_session, name=unique_name)
        
        assert role1.id == role2.id
        assert role1.name == role2.name
        
        # 清理
        db_session.delete(role1)
        db_session.commit()

    def test_get_role_by_name_exists(self, db_session: Session):
        """測試根據名稱獲取角色（存在）"""
        import random
        unique_name = f"test_get_role_{random.randint(10000, 99999)}"
        
        # 創建角色
        new_role = create_role(db_session, name=unique_name)
        
        # 查詢角色
        from app.crud.role import get_role_by_name
        found_role = get_role_by_name(db_session, name=unique_name)
        assert found_role is not None
        assert found_role.id == new_role.id
        assert found_role.name == unique_name
        
        # 清理
        db_session.delete(new_role)
        db_session.commit()

    def test_get_role_by_name_not_exists(self, db_session: Session):
        """測試根據名稱獲取角色（不存在）"""
        from app.crud.role import get_role_by_name
        role_obj = get_role_by_name(db_session, name="nonexistent_role")
        assert role_obj is None

    def test_assign_role_to_user(self, db_session: Session):
        """測試為用戶分配角色"""
        import random
        unique_email = f"test_role_assign_{random.randint(10000, 99999)}@example.com"
        unique_role_name = f"test_role_{random.randint(10000, 99999)}"
        
        # 創建用戶和角色
        new_user = user.create_user(db_session, email=unique_email, password="testpass123")
        new_role = create_role(db_session, name=unique_role_name)
        
        # 分配角色
        user.assign_role_to_user(db_session, user=new_user, role=new_role)
        
        # 刷新用戶以獲取關聯的角色
        db_session.refresh(new_user)
        
        assert new_role in new_user.roles
        
        # 清理
        db_session.delete(new_user)
        db_session.delete(new_role)
        db_session.commit()


class TestPermissionCRUD:
    """權限 CRUD 操作測試"""

    def test_create_permission_success(self, db_session: Session):
        """測試創建權限（成功）"""
        import random
        unique_code = f"test:permission:{random.randint(10000, 99999)}"
        
        new_permission = permission.create_permission(
            db_session,
            code=unique_code,
            description="Test Permission"
        )
        
        assert new_permission is not None
        assert new_permission.code == unique_code
        assert new_permission.description == "Test Permission"
        
        # 清理
        db_session.delete(new_permission)
        db_session.commit()

    def test_create_permission_duplicate(self, db_session: Session):
        """測試創建權限（重複代碼）"""
        import random
        unique_code = f"test:dup:{random.randint(10000, 99999)}"
        
        # 第一次創建
        perm1 = permission.create_permission(db_session, code=unique_code)
        
        # 第二次創建相同代碼的權限（應該返回現有權限）
        perm2 = permission.create_permission(db_session, code=unique_code)
        
        assert perm1.id == perm2.id
        assert perm1.code == perm2.code
        
        # 清理
        db_session.delete(perm1)
        db_session.commit()

    def test_get_permission_by_code(self, db_session: Session):
        """測試根據代碼獲取權限"""
        import random
        unique_code = f"test:get:{random.randint(10000, 99999)}"
        
        # 創建權限
        new_perm = permission.create_permission(db_session, code=unique_code)
        
        # 查詢權限
        found_perm = permission.get_permission_by_code(db_session, code=unique_code)
        assert found_perm is not None
        assert found_perm.id == new_perm.id
        assert found_perm.code == unique_code
        
        # 清理
        db_session.delete(new_perm)
        db_session.commit()

    def test_get_permission_by_id(self, db_session: Session):
        """測試根據ID獲取權限"""
        import random
        unique_code = f"test:by_id:{random.randint(10000, 99999)}"
        
        # 創建權限
        new_perm = permission.create_permission(db_session, code=unique_code)
        perm_id = new_perm.id
        
        # 根據ID查詢
        found_perm = permission.get_permission_by_id(db_session, permission_id=perm_id)
        assert found_perm is not None
        assert found_perm.id == perm_id
        
        # 清理
        db_session.delete(new_perm)
        db_session.commit()

    def test_list_permissions(self, db_session: Session):
        """測試列出權限"""
        perms = permission.list_permissions(db_session, skip=0, limit=10)
        assert isinstance(perms, list)
        # 至少應該有一些權限（系統默認創建的）

    def test_update_permission(self, db_session: Session):
        """測試更新權限"""
        import random
        unique_code = f"test:update:{random.randint(10000, 99999)}"
        
        # 創建權限
        new_perm = permission.create_permission(
            db_session,
            code=unique_code,
            description="Original Description"
        )
        
        # 更新權限
        updated_perm = permission.update_permission(
            db_session,
            permission=new_perm,
            description="Updated Description"
        )
        
        assert updated_perm.description == "Updated Description"
        assert updated_perm.code == unique_code
        
        # 清理
        db_session.delete(updated_perm)
        db_session.commit()

    def test_delete_permission(self, db_session: Session):
        """測試刪除權限"""
        import random
        unique_code = f"test:delete:{random.randint(10000, 99999)}"
        
        # 創建權限
        new_perm = permission.create_permission(db_session, code=unique_code)
        perm_id = new_perm.id
        
        # 刪除權限
        permission.delete_permission(db_session, permission=new_perm)
        
        # 驗證權限已刪除
        deleted_perm = permission.get_permission_by_id(db_session, permission_id=perm_id)
        assert deleted_perm is None

    def test_assign_permission_to_role(self, db_session: Session):
        """測試為角色分配權限"""
        import random
        unique_code = f"test:assign:{random.randint(10000, 99999)}"
        unique_role_name = f"test_role_{random.randint(10000, 99999)}"
        
        # 創建權限和角色
        new_perm = permission.create_permission(db_session, code=unique_code)
        new_role = create_role(db_session, name=unique_role_name)
        
        # 分配權限
        permission.assign_permission_to_role(db_session, role=new_role, permission=new_perm)
        
        # 刷新角色以獲取關聯的權限
        db_session.refresh(new_role)
        
        assert new_perm in new_role.permissions
        
        # 清理
        db_session.delete(new_role)
        db_session.delete(new_perm)
        db_session.commit()

    def test_revoke_permission_from_role(self, db_session: Session):
        """測試從角色撤銷權限"""
        import random
        unique_code = f"test:revoke:{random.randint(10000, 99999)}"
        unique_role_name = f"test_role_{random.randint(10000, 99999)}"
        
        # 創建權限和角色
        new_perm = permission.create_permission(db_session, code=unique_code)
        new_role = create_role(db_session, name=unique_role_name)
        
        # 分配權限
        permission.assign_permission_to_role(db_session, role=new_role, permission=new_perm)
        db_session.refresh(new_role)
        assert new_perm in new_role.permissions
        
        # 撤銷權限
        permission.revoke_permission_from_role(db_session, role=new_role, permission=new_perm)
        db_session.refresh(new_role)
        assert new_perm not in new_role.permissions
        
        # 清理
        db_session.delete(new_role)
        db_session.delete(new_perm)
        db_session.commit()

    def test_get_role_permissions(self, db_session: Session):
        """測試獲取角色的權限"""
        import random
        unique_code1 = f"test:perm1:{random.randint(10000, 99999)}"
        unique_code2 = f"test:perm2:{random.randint(10000, 99999)}"
        unique_role_name = f"test_role_{random.randint(10000, 99999)}"
        
        # 創建權限和角色
        perm1 = permission.create_permission(db_session, code=unique_code1)
        perm2 = permission.create_permission(db_session, code=unique_code2)
        new_role = create_role(db_session, name=unique_role_name)
        
        # 分配權限
        permission.assign_permission_to_role(db_session, role=new_role, permission=perm1)
        permission.assign_permission_to_role(db_session, role=new_role, permission=perm2)
        
        # 獲取角色權限
        from app.crud.permission import get_role_permissions
        role_perms = get_role_permissions(db_session, role=new_role)
        assert len(role_perms) >= 2
        assert perm1 in role_perms
        assert perm2 in role_perms
        
        # 清理
        db_session.delete(new_role)
        db_session.delete(perm1)
        db_session.delete(perm2)
        db_session.commit()

    def test_get_user_permissions(self, db_session: Session):
        """測試獲取用戶權限"""
        import random
        unique_email = f"test_user_perm_{random.randint(10000, 99999)}@example.com"
        unique_code = f"test:user_perm:{random.randint(10000, 99999)}"
        unique_role_name = f"test_role_{random.randint(10000, 99999)}"
        
        # 創建用戶、角色和權限
        new_user = user.create_user(db_session, email=unique_email, password="testpass123")
        new_role = create_role(db_session, name=unique_role_name)
        new_perm = permission.create_permission(db_session, code=unique_code)
        
        # 分配角色和權限
        user.assign_role_to_user(db_session, user=new_user, role=new_role)
        permission.assign_permission_to_role(db_session, role=new_role, permission=new_perm)
        
        # 獲取用戶權限
        user_perms = permission.get_user_permissions(db_session, user=new_user)
        assert new_perm in user_perms
        
        # 清理
        db_session.delete(new_user)
        db_session.delete(new_role)
        db_session.delete(new_perm)
        db_session.commit()

    def test_user_has_permission(self, db_session: Session):
        """測試檢查用戶是否有權限"""
        import random
        unique_email = f"test_has_perm_{random.randint(10000, 99999)}@example.com"
        unique_code = f"test:has_perm:{random.randint(10000, 99999)}"
        unique_role_name = f"test_role_{random.randint(10000, 99999)}"
        
        # 創建用戶、角色和權限
        new_user = user.create_user(db_session, email=unique_email, password="testpass123")
        new_role = create_role(db_session, name=unique_role_name)
        new_perm = permission.create_permission(db_session, code=unique_code)
        
        # 初始應該沒有權限
        assert not permission.user_has_permission(db_session, user=new_user, permission_code=unique_code)
        
        # 分配角色和權限
        user.assign_role_to_user(db_session, user=new_user, role=new_role)
        permission.assign_permission_to_role(db_session, role=new_role, permission=new_perm)
        
        # 現在應該有權限
        assert permission.user_has_permission(db_session, user=new_user, permission_code=unique_code)
        
        # 清理
        db_session.delete(new_user)
        db_session.delete(new_role)
        db_session.delete(new_perm)
        db_session.commit()

    def test_user_has_permission_superuser(self, db_session: Session):
        """測試超級管理員擁有所有權限"""
        import random
        unique_email = f"test_superuser_{random.randint(10000, 99999)}@example.com"
        unique_code = f"test:superuser_perm:{random.randint(10000, 99999)}"
        
        # 創建超級管理員用戶（不分配任何角色）
        superuser = user.create_user(
            db_session,
            email=unique_email,
            password="testpass123",
            is_superuser=True
        )
        
        # 創建一個權限（但不分配給用戶）
        new_perm = permission.create_permission(db_session, code=unique_code)
        
        # 超級管理員應該擁有所有權限
        assert permission.user_has_permission(db_session, user=superuser, permission_code=unique_code)
        
        # 清理
        db_session.delete(superuser)
        db_session.delete(new_perm)
        db_session.commit()

    def test_user_has_any_permission(self, db_session: Session):
        """測試檢查用戶是否有任意一個權限"""
        import random
        unique_email = f"test_any_perm_{random.randint(10000, 99999)}@example.com"
        unique_code1 = f"test:any1:{random.randint(10000, 99999)}"
        unique_code2 = f"test:any2:{random.randint(10000, 99999)}"
        unique_role_name = f"test_role_{random.randint(10000, 99999)}"
        
        # 創建用戶、角色和權限
        new_user = user.create_user(db_session, email=unique_email, password="testpass123")
        new_role = create_role(db_session, name=unique_role_name)
        perm1 = permission.create_permission(db_session, code=unique_code1)
        perm2 = permission.create_permission(db_session, code=unique_code2)
        
        # 只分配第一個權限
        user.assign_role_to_user(db_session, user=new_user, role=new_role)
        permission.assign_permission_to_role(db_session, role=new_role, permission=perm1)
        
        # 應該有第一個權限，沒有第二個
        assert permission.user_has_any_permission(
            db_session,
            user=new_user,
            permission_codes=[unique_code1, unique_code2]
        )
        assert not permission.user_has_any_permission(
            db_session,
            user=new_user,
            permission_codes=[unique_code2]
        )
        
        # 清理
        db_session.delete(new_user)
        db_session.delete(new_role)
        db_session.delete(perm1)
        db_session.delete(perm2)
        db_session.commit()

    def test_user_has_all_permissions(self, db_session: Session):
        """測試檢查用戶是否有所有權限"""
        import random
        unique_email = f"test_all_perm_{random.randint(10000, 99999)}@example.com"
        unique_code1 = f"test:all1:{random.randint(10000, 99999)}"
        unique_code2 = f"test:all2:{random.randint(10000, 99999)}"
        unique_role_name = f"test_role_{random.randint(10000, 99999)}"
        
        # 創建用戶、角色和權限
        new_user = user.create_user(db_session, email=unique_email, password="testpass123")
        new_role = create_role(db_session, name=unique_role_name)
        perm1 = permission.create_permission(db_session, code=unique_code1)
        perm2 = permission.create_permission(db_session, code=unique_code2)
        
        # 分配兩個權限
        user.assign_role_to_user(db_session, user=new_user, role=new_role)
        permission.assign_permission_to_role(db_session, role=new_role, permission=perm1)
        permission.assign_permission_to_role(db_session, role=new_role, permission=perm2)
        
        # 應該有所有權限
        assert permission.user_has_all_permissions(
            db_session,
            user=new_user,
            permission_codes=[unique_code1, unique_code2]
        )
        
        # 但缺少一個就不行
        assert not permission.user_has_all_permissions(
            db_session,
            user=new_user,
            permission_codes=[unique_code1, unique_code2, "nonexistent:permission"]
        )
        
        # 清理
        db_session.delete(new_user)
        db_session.delete(new_role)
        db_session.delete(perm1)
        db_session.delete(perm2)
        db_session.commit()

