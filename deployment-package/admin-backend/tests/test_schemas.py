"""
Schemas 數據驗證測試
測試 Pydantic 模型的驗證和序列化
"""
import pytest
from pydantic import ValidationError
from datetime import datetime

from app.schemas.auth import Token, TokenPayload
from app.schemas.user import (
    UserRead,
    UserCreate,
    UserUpdate,
    UserPasswordReset,
    RoleRead
)
from app.models.user import User
from app.models.role import Role


class TestAuthSchemas:
    """認證相關 Schema 測試"""

    def test_token_basic(self):
        """測試基本 Token schema"""
        token = Token(access_token="test_token_123")
        assert token.access_token == "test_token_123"
        assert token.token_type == "bearer"

    def test_token_with_type(self):
        """測試帶類型 Token schema"""
        token = Token(access_token="test_token_123", token_type="Bearer")
        assert token.access_token == "test_token_123"
        assert token.token_type == "Bearer"

    def test_token_payload_basic(self):
        """測試基本 TokenPayload schema"""
        payload = TokenPayload(sub="test@example.com")
        assert payload.sub == "test@example.com"

    def test_token_payload_empty(self):
        """測試空 TokenPayload schema"""
        payload = TokenPayload()
        assert payload.sub is None


class TestUserSchemas:
    """用戶相關 Schema 測試"""

    def test_user_create_valid(self):
        """測試有效用戶創建"""
        user_data = UserCreate(
            email="test@example.com",
            password="password123",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        assert user_data.email == "test@example.com"
        assert user_data.password == "password123"
        assert user_data.full_name == "Test User"
        assert user_data.is_active is True
        assert user_data.is_superuser is False

    def test_user_create_minimal(self):
        """測試最小用戶創建（只提供必填字段）"""
        user_data = UserCreate(
            email="test@example.com",
            password="password123"
        )
        assert user_data.email == "test@example.com"
        assert user_data.full_name is None
        assert user_data.is_active is True  # 默認值
        assert user_data.is_superuser is False  # 默認值

    def test_user_create_invalid_email(self):
        """測試無效郵箱"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid_email",
                password="password123"
            )

    def test_user_create_missing_fields(self):
        """測試缺少必填字段"""
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com")
            # 缺少 password

    def test_user_update_all_fields(self):
        """測試更新所有字段"""
        update_data = UserUpdate(
            email="new@example.com",
            full_name="New Name",
            is_active=False,
            is_superuser=True
        )
        assert update_data.email == "new@example.com"
        assert update_data.full_name == "New Name"
        assert update_data.is_active is False
        assert update_data.is_superuser is True

    def test_user_update_partial(self):
        """測試部分更新"""
        update_data = UserUpdate(email="new@example.com")
        assert update_data.email == "new@example.com"
        assert update_data.full_name is None
        assert update_data.is_active is None
        assert update_data.is_superuser is None

    def test_user_update_empty(self):
        """測試空更新"""
        update_data = UserUpdate()
        assert update_data.email is None
        assert update_data.full_name is None
        assert update_data.is_active is None
        assert update_data.is_superuser is None

    def test_user_password_reset(self):
        """測試密碼重置"""
        reset_data = UserPasswordReset(new_password="newpassword123")
        assert reset_data.new_password == "newpassword123"

    def test_user_password_reset_empty(self):
        """測試空密碼重置"""
        # Pydantic 可能允許空字符串（取決於配置），測試它至少可以創建對象
        reset_data = UserPasswordReset(new_password="")
        assert reset_data.new_password == ""


class TestRoleSchemas:
    """角色相關 Schema 測試"""

    def test_role_read(self):
        """測試角色讀取"""
        role_data = RoleRead(id=1, name="admin")
        assert role_data.id == 1
        assert role_data.name == "admin"


class TestUserReadSchema:
    """用戶讀取 Schema 測試"""

    def test_user_read_from_orm(self, prepare_database):
        """測試從 ORM 對象創建 UserRead"""
        from app.db import SessionLocal
        from app.crud.user import create_user, create_role, assign_role_to_user
        
        db = SessionLocal()
        try:
            # 創建用戶和角色
            user = create_user(
                db,
                email="test_read@example.com",
                password="password123",
                full_name="Test User"
            )
            
            role = create_role(db, name="test_role")
            assign_role_to_user(db, user=user, role=role)
            
            db.refresh(user)
            
            # 從 ORM 對象創建 schema
            user_read = UserRead.from_orm(user)
            assert user_read.id == user.id
            assert user_read.email == user.email
            assert user_read.full_name == user.full_name
            assert user_read.is_active == user.is_active
            assert user_read.is_superuser == user.is_superuser
            assert len(user_read.roles) == 1
            assert user_read.roles[0].id == role.id
            assert user_read.roles[0].name == role.name
        finally:
            db.close()

    def test_user_read_from_dict(self):
        """測試從字典創建 UserRead"""
        user_dict = {
            "id": 1,
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True,
            "is_superuser": False,
            "roles": [],
            "created_at": datetime.now()
        }
        
        user_read = UserRead(**user_dict)
        assert user_read.id == 1
        assert user_read.email == "test@example.com"
        assert user_read.full_name == "Test User"

    def test_user_read_with_roles(self):
        """測試帶角色的用戶讀取"""
        user_dict = {
            "id": 1,
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True,
            "is_superuser": False,
            "roles": [
                {"id": 1, "name": "admin"},
                {"id": 2, "name": "user"}
            ],
            "created_at": datetime.now()
        }
        
        user_read = UserRead(**user_dict)
        assert len(user_read.roles) == 2
        assert user_read.roles[0].name == "admin"
        assert user_read.roles[1].name == "user"

    def test_user_read_invalid_email(self):
        """測試無效郵箱"""
        with pytest.raises(ValidationError):
            UserRead(
                id=1,
                email="invalid_email",
                is_active=True,
                is_superuser=False,
                roles=[],
                created_at=datetime.now()
            )

    def test_user_read_serialization(self):
        """測試序列化"""
        user_read = UserRead(
            id=1,
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            roles=[],
            created_at=datetime.now()
        )
        
        # 轉換為字典
        user_dict = user_read.dict()
        assert "id" in user_dict
        assert "email" in user_dict
        assert "roles" in user_dict
        
        # 轉換為 JSON
        user_json = user_read.json()
        assert "test@example.com" in user_json


class TestSchemaValidation:
    """Schema 驗證測試"""

    def test_email_validation(self):
        """測試郵箱驗證"""
        # 有效郵箱
        valid_emails = [
            "test@example.com",
            "user.name@example.co.uk",
            "user+tag@example.com",
            "123@example.com"
        ]
        
        for email in valid_emails:
            user_data = UserCreate(email=email, password="password123")
            assert user_data.email == email
        
        # 無效郵箱
        invalid_emails = [
            "invalid_email",
            "@example.com",
            "test@",
            "test @example.com",
            "test@example",
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                UserCreate(email=email, password="password123")

    def test_optional_fields(self):
        """測試可選字段"""
        # full_name 是可選的
        user_data1 = UserCreate(email="test@example.com", password="pass")
        assert user_data1.full_name is None
        
        # 可以設置為 None
        user_data2 = UserCreate(
            email="test@example.com",
            password="pass",
            full_name=None
        )
        assert user_data2.full_name is None
        
        # 可以設置值
        user_data3 = UserCreate(
            email="test@example.com",
            password="pass",
            full_name="Test"
        )
        assert user_data3.full_name == "Test"

    def test_default_values(self):
        """測試默認值"""
        user_data = UserCreate(email="test@example.com", password="pass")
        assert user_data.is_active is True
        assert user_data.is_superuser is False

    def test_type_conversion(self):
        """測試類型轉換"""
        # is_active 應該是 bool
        user_data = UserCreate(
            email="test@example.com",
            password="pass",
            is_active=1  # 應該轉換為 True
        )
        assert user_data.is_active is True
        
        user_data2 = UserCreate(
            email="test@example.com",
            password="pass",
            is_active=0  # 應該轉換為 False
        )
        assert user_data2.is_active is False

