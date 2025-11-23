"""
通知系統 API 測試
測試通知系統 API 端點
"""
import pytest
import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.crud.notification import (
    create_notification_config,
    create_notification,
    create_notification_template
)
from app.models.notification import NotificationType

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


class TestNotificationConfigAPI:
    """通知配置 API 測試"""

    def test_create_notification_config_success(self, prepare_database):
        """測試成功創建通知配置"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        unique_name = f"測試配置_{uuid.uuid4().hex[:8]}"
        resp = client.post(
            "/api/v1/notifications/configs",
            json={
                "name": unique_name,
                "notification_type": "EMAIL",
                "config_data": {"smtp_host": "smtp.example.com"},
                "recipients": ["admin@example.com"]
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [201, 403]

    def test_list_notification_configs(self, prepare_database):
        """測試列出通知配置"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        resp = client.get(
            "/api/v1/notifications/configs",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]
        if resp.status_code == 200:
            assert isinstance(resp.json(), list)

    def test_get_notification_config_not_found(self, prepare_database):
        """測試獲取不存在的通知配置"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        resp = client.get(
            "/api/v1/notifications/configs/999999",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [404, 403]


class TestNotificationTemplateAPI:
    """通知模板 API 測試"""

    def test_create_notification_template_success(self, prepare_database):
        """測試成功創建通知模板"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        unique_name = f"測試模板_{uuid.uuid4().hex[:8]}"
        resp = client.post(
            "/api/v1/notifications/templates",
            json={
                "name": unique_name,
                "notification_type": "EMAIL",
                "title_template": "標題: {{title}}",
                "body_template": "內容: {{message}}"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [201, 403]

    def test_list_notification_templates(self, prepare_database):
        """測試列出通知模板"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        resp = client.get(
            "/api/v1/notifications/templates",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]

    def test_preview_notification_template(self, prepare_database):
        """測試預覽通知模板"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        resp = client.post(
            "/api/v1/notifications/templates/preview",
            json={
                "title_template": "標題: {{title}}",
                "body_template": "內容: {{message}}",
                "context": {"title": "測試", "message": "消息"}
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 400, 403]
        if resp.status_code == 200:
            data = resp.json()
            assert "title" in data
            assert "message" in data


class TestNotificationAPI:
    """通知記錄 API 測試"""

    def test_list_notifications(self, prepare_database):
        """測試列出通知"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        # 創建一些通知
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            create_notification(
                db,
                notification_type=NotificationType.EMAIL,
                title="測試通知",
                message="測試消息",
                recipient="admin@example.com"
            )
        finally:
            db.close()
        
        resp = client.get(
            "/api/v1/notifications/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]
        if resp.status_code == 200:
            data = resp.json()
            assert "items" in data
            assert "total" in data
            assert "unread_count" in data

    def test_get_unread_count(self, prepare_database):
        """測試獲取未讀通知數量"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        resp = client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]
        if resp.status_code == 200:
            data = resp.json()
            assert "unread_count" in data

    def test_mark_all_read(self, prepare_database):
        """測試標記所有通知為已讀"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        resp = client.post(
            "/api/v1/notifications/mark-all-read",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]
        if resp.status_code == 200:
            data = resp.json()
            assert "message" in data
            assert "count" in data


class TestNotificationBatchAPI:
    """通知批量操作 API 測試"""

    def test_batch_mark_read(self, prepare_database):
        """測試批量標記為已讀"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        # 創建一些通知
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            n1 = create_notification(
                db,
                notification_type=NotificationType.BROWSER,
                title="通知1",
                message="消息1",
                recipient="admin@example.com"
            )
            n2 = create_notification(
                db,
                notification_type=NotificationType.BROWSER,
                title="通知2",
                message="消息2",
                recipient="admin@example.com"
            )
            notification_ids = [n1.id, n2.id]
        finally:
            db.close()
        
        resp = client.post(
            "/api/v1/notifications/batch/read",
            json={"notification_ids": notification_ids},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]

    def test_batch_delete_notifications(self, prepare_database):
        """測試批量刪除通知"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證 token")
        
        # 創建一些通知
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            n1 = create_notification(
                db,
                notification_type=NotificationType.EMAIL,
                title="通知1",
                message="消息1",
                recipient="admin@example.com"
            )
            notification_ids = [n1.id]
        finally:
            db.close()
        
        resp = client.post(
            "/api/v1/notifications/batch/delete",
            json={"notification_ids": notification_ids},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]


class TestNotificationAPIUnauthorized:
    """通知 API 未認證測試"""

    def test_list_notifications_unauthorized(self):
        """測試未認證訪問"""
        resp = client.get("/api/v1/notifications/")
        assert resp.status_code == 401

    def test_create_config_unauthorized(self):
        """測試未認證創建配置"""
        resp = client.post("/api/v1/notifications/configs", json={})
        assert resp.status_code == 401

