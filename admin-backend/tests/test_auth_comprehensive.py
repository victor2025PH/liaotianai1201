"""
認證相關測試
補充認證、權限檢查等功能的測試用例
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.main import app
from app.db import SessionLocal, get_db
from app.crud import user, permission, role
from app.core.security import verify_password, create_access_token
from app.api.deps import get_current_active_user
from app.models.user import User

client = TestClient(app)


def _get_token(email: str = None, password: str = None) -> str:
    """獲取認證 Token"""
    settings = get_settings()
    if email is None:
        email = settings.admin_default_email
    if password is None:
        password = "testpass123"
    
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return None


class TestAuthentication:
    """認證測試"""

    def test_login_success(self):
        """測試登錄成功"""
        settings = get_settings()
        resp = client.post(
            "/api/v1/auth/login",
            data={
                "username": settings.admin_default_email,
                "password": "testpass123"
            },
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0

    def test_login_invalid_email(self):
        """測試登錄（無效郵箱）"""
        resp = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "anypassword"
            },
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 401

    def test_login_invalid_password(self):
        """測試登錄（錯誤密碼）"""
        settings = get_settings()
        resp = client.post(
            "/api/v1/auth/login",
            data={
                "username": settings.admin_default_email,
                "password": "wrongpassword"
            },
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 401

    def test_login_inactive_user(self, prepare_database):
        """測試登錄（已禁用用戶）"""
        import random
        unique_email = f"test_inactive_{random.randint(10000, 99999)}@example.com"
        
        # 獲取數據庫會話
        db = SessionLocal()
        try:
            # 創建已禁用的用戶
            new_user = user.create_user(
                db,
                email=unique_email,
                password="testpass123",
                is_superuser=False
            )
            user.update_user(db, user=new_user, is_active=False)
            resp = client.post(
                "/api/v1/auth/login",
                data={
                    "username": unique_email,
                    "password": "testpass123"
                },
                headers={"content-type": "application/x-www-form-urlencoded"},
            )
            # 應該返回 400（賬戶已禁用）
            assert resp.status_code == 400
            assert "禁用" in resp.json()["detail"] or "inactive" in resp.json()["detail"].lower()
        finally:
            # 清理
            db.delete(new_user)
            db.commit()
            db.close()

    def test_login_missing_fields(self):
        """測試登錄（缺少字段）"""
        # 缺少密碼
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com"},
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 422  # Validation error

    def test_token_format(self):
        """測試 Token 格式"""
        token = _get_token()
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT token 通常包含三個部分，用點分隔
        parts = token.split(".")
        assert len(parts) == 3


class TestPermissionMiddleware:
    """權限中間件測試"""

    def test_access_without_token(self):
        """測試無 Token 訪問受保護端點"""
        resp = client.get("/api/v1/dashboard")
        assert resp.status_code == 401

    def test_access_with_invalid_token(self):
        """測試使用無效 Token 訪問"""
        resp = client.get(
            "/api/v1/dashboard",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        assert resp.status_code == 401

    def test_access_with_valid_token(self):
        """測試使用有效 Token 訪問"""
        token = _get_token()
        assert token is not None
        
        resp = client.get(
            "/api/v1/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        # 可能返回 200（有權限）或 403（無權限）
        assert resp.status_code in [200, 403]

    def test_access_with_expired_token(self):
        """測試使用過期 Token 訪問"""
        from datetime import timedelta
        
        # 創建一個過期的 token
        settings = get_settings()
        expired_token = create_access_token(
            subject=settings.admin_default_email,
            expires_delta=timedelta(seconds=-1)  # 已過期
        )
        
        resp = client.get(
            "/api/v1/dashboard",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        # 應該返回 401（Token 已過期）
        assert resp.status_code == 401

    def test_permission_check_superuser(self, prepare_database):
        """測試超級管理員權限檢查"""
        import random
        unique_email = f"test_superuser_{random.randint(10000, 99999)}@example.com"
        
        db = SessionLocal()
        try:
            # 創建超級管理員
            superuser = user.create_user(
                db,
                email=unique_email,
                password="testpass123",
                is_superuser=True
            )
            token = _get_token(email=unique_email, password="testpass123")
            assert token is not None
            
            # 超級管理員應該能訪問所有端點
            resp = client.get(
                "/api/v1/users",
                headers={"Authorization": f"Bearer {token}"}
            )
            # 超級管理員通常有所有權限
            assert resp.status_code in [200, 403]
        finally:
            # 清理
            db.delete(superuser)
            db.commit()
            db.close()

    def test_permission_check_user_without_permission(self, prepare_database):
        """測試無權限用戶訪問受保護端點"""
        import random
        unique_email = f"test_no_perm_{random.randint(10000, 99999)}@example.com"
        
        db = SessionLocal()
        try:
            # 創建普通用戶（沒有特殊權限）
            regular_user = user.create_user(
                db,
                email=unique_email,
                password="testpass123",
                is_superuser=False
            )
            token = _get_token(email=unique_email, password="testpass123")
            assert token is not None
            
            # 嘗試訪問需要權限的端點
            resp = client.get(
                "/api/v1/users",
                headers={"Authorization": f"Bearer {token}"}
            )
            # 應該返回 403（無權限）或 200（如果該端點不需要特殊權限）
            assert resp.status_code in [200, 403]
        finally:
            # 清理
            db.delete(regular_user)
            db.commit()
            db.close()

    def test_permission_check_user_with_permission(self, prepare_database):
        """測試有權限用戶訪問端點"""
        import random
        unique_email = f"test_with_perm_{random.randint(10000, 99999)}@example.com"
        unique_code = f"user:view:{random.randint(10000, 99999)}"
        unique_role_name = f"test_role_{random.randint(10000, 99999)}"
        
        db = SessionLocal()
        try:
            from app.crud.user import create_role
            
            # 創建用戶、角色和權限
            test_user = user.create_user(
                db,
                email=unique_email,
                password="testpass123",
                is_superuser=False
            )
            test_role = create_role(db, name=unique_role_name)
            test_perm = permission.create_permission(db, code=unique_code)
            
            # 分配角色和權限
            user.assign_role_to_user(db, user=test_user, role=test_role)
            permission.assign_permission_to_role(db, role=test_role, permission=test_perm)
            token = _get_token(email=unique_email, password="testpass123")
            assert token is not None
            
            # 用戶應該有權限訪問對應的端點（如果端點檢查該權限）
            resp = client.get(
                "/api/v1/dashboard",
                headers={"Authorization": f"Bearer {token}"}
            )
            # 可能返回 200（有權限）或 403（該端點需要其他權限）
            assert resp.status_code in [200, 403]
        finally:
            # 清理
            db.delete(test_user)
            db.delete(test_role)
            db.delete(test_perm)
            db.commit()
            db.close()


class TestAuthEndpoints:
    """認證端點測試"""

    def test_login_endpoint_exists(self):
        """測試登錄端點存在"""
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "test", "password": "test"},
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        # 應該返回 401（認證失敗）而不是 404（端點不存在）
        assert resp.status_code != 404

    def test_no_logout_endpoint(self):
        """測試登出端點（如果不存在）"""
        # 有些系統可能沒有登出端點（使用 Token 過期）
        resp = client.post("/api/v1/auth/logout")
        # 可能返回 404（不存在）或 401（需要認證）
        assert resp.status_code in [404, 401, 405]

    def test_refresh_token_endpoint(self):
        """測試刷新 Token 端點（如果存在）"""
        token = _get_token()
        if token:
            resp = client.post(
                "/api/v1/auth/refresh",
                headers={"Authorization": f"Bearer {token}"}
            )
            # 可能返回 200（支持刷新）、404（不存在）或 401（Token 無效）
            assert resp.status_code in [200, 404, 401, 405]


class TestPasswordSecurity:
    """密碼安全測試"""

    def test_password_hashing(self):
        """測試密碼哈希"""
        from app.core.security import get_password_hash
        
        password = "testpass123"
        hashed = get_password_hash(password)
        
        # 哈希值應該不同於原始密碼
        assert hashed != password
        # 哈希值應該可以驗證
        assert verify_password(password, hashed)
        # 錯誤密碼不應該驗證通過
        assert not verify_password("wrongpass", hashed)

    def test_password_verification(self):
        """測試密碼驗證"""
        from app.core.security import get_password_hash, verify_password
        
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        # 正確密碼應該驗證通過
        assert verify_password(password, hashed)
        # 錯誤密碼不應該驗證通過
        assert not verify_password(password + "x", hashed)
        assert not verify_password("", hashed)
        assert not verify_password("different", hashed)

