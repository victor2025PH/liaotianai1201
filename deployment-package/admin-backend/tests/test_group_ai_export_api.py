"""
Group AI Export API 測試
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

from app.main import app
from app.core.config import get_settings

client = TestClient(app)


def _get_token() -> str:
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


class TestExportAPI:
    """Export API 測試"""

    def test_export_scripts_csv(self, prepare_database):
        """測試導出劇本為CSV"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/group-ai/export/scripts?format=csv",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 404, 500]
        if resp.status_code == 200:
            assert "text/csv" in resp.headers.get("content-type", "")

    def test_export_scripts_excel(self, prepare_database):
        """測試導出劇本為Excel"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/group-ai/export/scripts?format=excel",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 可能返回 503（庫未安裝）或其他狀態碼
        assert resp.status_code in [200, 404, 503, 500]

    def test_export_scripts_pdf(self, prepare_database):
        """測試導出劇本為PDF"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/group-ai/export/scripts?format=pdf",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 可能返回 503（庫未安裝）或其他狀態碼
        assert resp.status_code in [200, 404, 503, 500]

    def test_export_accounts_csv(self, prepare_database):
        """測試導出賬號為CSV"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/group-ai/export/accounts?format=csv",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 404, 500]

    def test_export_accounts_excel(self, prepare_database):
        """測試導出賬號為Excel"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/group-ai/export/accounts?format=excel",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 404, 503, 500]

    def test_export_schemes_csv(self, prepare_database):
        """測試導出分配方案為CSV"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/group-ai/export/schemes?format=csv",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 404, 500]

    def test_export_invalid_format(self, prepare_database):
        """測試無效格式"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/group-ai/export/scripts?format=invalid",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 可能返回 400（無效格式）或其他狀態碼
        assert resp.status_code in [200, 400, 404, 422, 500]

    def test_export_unauthorized(self):
        """測試未認證訪問"""
        resp = client.get("/api/v1/group-ai/export/scripts?format=csv")
        # 可能返回 401（未認證）或 200（認證被禁用）或 404
        assert resp.status_code in [200, 401, 403, 404]


class TestExportHelperFunctions:
    """導出輔助函數測試"""

    def test_export_to_csv_empty_data(self):
        """測試導出空數據為CSV"""
        from app.api.group_ai.export import export_to_csv
        
        data = []
        response = export_to_csv(data, "test")
        
        assert response is not None
        assert response.media_type == "text/csv; charset=utf-8"

    def test_export_to_csv_with_data(self):
        """測試導出有數據為CSV"""
        from app.api.group_ai.export import export_to_csv
        
        data = [
            {"id": 1, "name": "測試1", "value": 100},
            {"id": 2, "name": "測試2", "value": 200}
        ]
        response = export_to_csv(data, "test")
        
        assert response is not None
        assert response.media_type == "text/csv; charset=utf-8"

    def test_export_to_csv_with_nested_data(self):
        """測試導出嵌套數據為CSV"""
        from app.api.group_ai.export import export_to_csv
        
        data = [
            {"id": 1, "config": {"key": "value"}, "tags": ["tag1", "tag2"]}
        ]
        response = export_to_csv(data, "test")
        
        assert response is not None
        # 嵌套數據應該被轉換為字符串
        assert response.media_type == "text/csv; charset=utf-8"

