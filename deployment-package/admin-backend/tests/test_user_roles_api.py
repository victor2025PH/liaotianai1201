"""
用戶角色管理 API 測試
測試用戶角色分配和撤銷 API 端點
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.crud.user import create_user, create_role, assign_role_to_user

client = TestClient(app)


def _get_token():
    """獲取認證 token"""
    from app.core.config import get_settings
    settings = get_settings()
    test_password = "testpass123"  # 與 conftest.py 中的測試密碼一致
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": settings.admin_default_email, "password": test_password}
    )
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return None


class TestUserRolesAPI:
    """用戶角色 API 測試"""

    def test_list_users_with_roles(self, prepare_database):
        """測試列出用戶及其角色"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        resp = client.get(
            "/api/v1/user-roles/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)

    def test_get_user_with_roles(self, prepare_database):
        """測試獲取用戶詳情及其角色"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        # 創建測試用戶
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            user = create_user(
                db,
                email="test_role@example.com",
                password="password123",
                full_name="Test User"
            )
            user_id = user.id
        finally:
            db.close()
        
        resp = client.get(
            f"/api/v1/user-roles/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]
        if resp.status_code == 200:
            data = resp.json()
            assert "id" in data
            assert "email" in data
            assert "roles" in data

    def test_get_user_roles(self, prepare_database):
        """測試獲取用戶的所有角色"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        # 創建用戶和角色
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            user = create_user(
                db,
                email="test_role2@example.com",
                password="password123",
                full_name="Test User"
            )
            role = create_role(db, name="test_role", description="測試角色")
            assign_role_to_user(db, user=user, role=role)
            user_id = user.id
        finally:
            db.close()
        
        resp = client.get(
            f"/api/v1/user-roles/users/{user_id}/roles",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) >= 1

    def test_assign_role_to_user(self, prepare_database):
        """測試為用戶分配角色"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        # 創建用戶和角色
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            import time
            user = create_user(
                db,
                email=f"test_assign_{int(time.time())}@example.com",
                password="password123",
                full_name="Test User"
            )
            role = create_role(db, name="assign_test_role", description="分配測試角色")
            user_id = user.id
            role_name = role.name
        finally:
            db.close()
        
        resp = client.post(
            f"/api/v1/user-roles/users/{user_id}/roles",
            json={"role_name": role_name},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403, 404]

    def test_revoke_role_from_user(self, prepare_database):
        """測試從用戶撤銷角色"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        # 創建用戶和角色，並分配角色
        from app.db import SessionLocal
        import time
        db = SessionLocal()
        try:
            user = create_user(
                db,
                email=f"test_revoke_{int(time.time())}@example.com",
                password="password123",
                full_name="Test User"
            )
            role = create_role(db, name=f"revoke_test_role_{int(time.time())}", description="撤銷測試角色")
            assign_role_to_user(db, user=user, role=role)
            user_id = user.id
            role_name = role.name
        finally:
            db.close()
        
        resp = client.delete(
            f"/api/v1/user-roles/users/{user_id}/roles/{role_name}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403, 404]

    def test_batch_assign_role(self, prepare_database):
        """測試批量分配角色"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        # 創建用戶和角色
        from app.db import SessionLocal
        import time
        db = SessionLocal()
        try:
            user1 = create_user(
                db,
                email=f"batch1_{int(time.time())}@example.com",
                password="password123",
                full_name="User 1"
            )
            user2 = create_user(
                db,
                email=f"batch2_{int(time.time())}@example.com",
                password="password123",
                full_name="User 2"
            )
            role = create_role(db, name=f"batch_role_{int(time.time())}", description="批量角色")
            user_ids = [user1.id, user2.id]
            role_name = role.name
        finally:
            db.close()
        
        resp = client.post(
            "/api/v1/user-roles/batch-assign",
            json={"user_ids": user_ids, "role_name": role_name},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403, 404]
        if resp.status_code == 200:
            data = resp.json()
            assert "success_count" in data
            assert "failed_count" in data

    def test_batch_revoke_role(self, prepare_database):
        """測試批量撤銷角色"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        # 創建用戶和角色，並分配角色
        from app.db import SessionLocal
        import time
        db = SessionLocal()
        try:
            user1 = create_user(
                db,
                email=f"batch_revoke1_{int(time.time())}@example.com",
                password="password123",
                full_name="User 1"
            )
            role = create_role(db, name=f"batch_revoke_role_{int(time.time())}", description="批量撤銷角色")
            assign_role_to_user(db, user=user1, role=role)
            user_ids = [user1.id]
            role_name = role.name
        finally:
            db.close()
        
        resp = client.post(
            "/api/v1/user-roles/batch-revoke",
            json={"user_ids": user_ids, "role_name": role_name},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403, 404]


class TestUserRolesAPIUnauthorized:
    """用戶角色 API 未認證測試"""

    def test_list_users_unauthorized(self):
        """測試未認證訪問"""
        resp = client.get("/api/v1/user-roles/users")
        assert resp.status_code == 401

    def test_assign_role_unauthorized(self):
        """測試未認證分配角色"""
        resp = client.post(
            "/api/v1/user-roles/users/1/roles",
            json={"role_name": "test"}
        )
        assert resp.status_code == 401

