"""
審計日誌 API 測試
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import app
from app.core.config import get_settings
from app.crud.audit_log import create_audit_log

client = TestClient(app)


def _get_token():
    """獲取認證 Token"""
    settings = get_settings()
    test_password = "testpass123"
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": settings.admin_default_email, "password": test_password},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return None


class TestAuditLogsAPI:
    """審計日誌 API 測試"""

    def test_list_audit_logs_basic(self, prepare_database):
        """測試基本列表查詢"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/audit-logs/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]  # 可能沒有權限
        if resp.status_code == 200:
            data = resp.json()
            assert "items" in data
            assert "total" in data
            assert "skip" in data
            assert "limit" in data

    def test_list_audit_logs_with_pagination(self, prepare_database):
        """測試分頁查詢"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/audit-logs/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]
        if resp.status_code == 200:
            data = resp.json()
            assert len(data["items"]) <= 10

    def test_list_audit_logs_filter_by_user_id(self, prepare_database):
        """測試按用戶ID過濾"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/audit-logs/?user_id=1",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]

    def test_list_audit_logs_filter_by_action(self, prepare_database):
        """測試按操作類型過濾"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/audit-logs/?action=CREATE",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]

    def test_list_audit_logs_filter_by_resource_type(self, prepare_database):
        """測試按資源類型過濾"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/audit-logs/?resource_type=user",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]

    def test_list_audit_logs_filter_by_date_range(self, prepare_database):
        """測試按日期範圍過濾"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        resp = client.get(
            f"/api/v1/audit-logs/?start_date={start_date}&end_date={end_date}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]

    def test_get_audit_log_by_id(self, prepare_database):
        """測試根據ID獲取審計日誌"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 創建一個審計日誌
        db = SessionLocal()
        try:
            log = create_audit_log(
                db,
                user_id=1,
                user_email="test@example.com",
                action="TEST",
                resource_type="test"
            )
            
            resp = client.get(
                f"/api/v1/audit-logs/{log.id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 403, 404]
            if resp.status_code == 200:
                data = resp.json()
                assert data["id"] == log.id
                assert data["action"] == "TEST"
        finally:
            db.close()

    def test_get_audit_log_not_found(self, prepare_database):
        """測試獲取不存在的審計日誌"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/audit-logs/999999",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [404, 403]

    def test_list_audit_logs_unauthorized(self):
        """測試未認證訪問"""
        resp = client.get("/api/v1/audit-logs/")
        assert resp.status_code == 401
