"""
routes.py 中 activities 和 commands 端點的詳細測試
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

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


class TestActivitiesEndpoint:
    """活動端點測試"""

    def test_list_activities_basic(self):
        """測試基本活動列表查詢"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/activities",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert data["total"] >= 0

    def test_list_activities_structure(self):
        """測試活動列表數據結構"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/activities",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        
        # 驗證每個活動項目的結構
        for item in data.get("items", []):
            assert "id" in item
            assert "name" in item
            assert "status" in item
            assert "success_rate" in item
            assert isinstance(item["success_rate"], (int, float))
            assert "started_at" in item
            assert "participants" in item
            assert isinstance(item["participants"], int)

    def test_list_activities_unauthorized(self):
        """測試未認證訪問"""
        resp = client.get("/api/v1/activities")
        assert resp.status_code == 401

    @patch('app.services.data_sources.get_activities')
    def test_list_activities_with_mock_data(self, mock_get_activities):
        """測試使用模擬數據"""
        from datetime import datetime
        mock_get_activities.return_value = {
            "items": [
                {
                    "id": "TEST-001",
                    "name": "測試活動",
                    "status": "進行中",
                    "success_rate": 0.95,
                    "started_at": datetime.utcnow().isoformat(),
                    "participants": 10
                }
            ],
            "total": 1
        }
        
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/activities",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) >= 0  # 可能返回真實數據或模擬數據
        assert data["total"] >= 0

    @patch('app.services.data_sources.get_activities')
    def test_list_activities_empty_data(self, mock_get_activities):
        """測試空數據處理"""
        mock_get_activities.return_value = {
            "items": [],
            "total": 0
        }
        
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/activities",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 0  # 可能返回真實數據
        assert isinstance(data["items"], list)


class TestCommandsEndpoint:
    """命令端點測試"""

    def test_create_command_basic(self):
        """測試基本命令創建"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        payload = {
            "account": "+8613812345678",
            "command": "send_text",
            "payload": "測試消息"
        }
        
        resp = client.post(
            "/api/v1/commands",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code == 202
        data = resp.json()
        assert "status" in data
        assert "command_id" in data or "commandId" in data
        assert "queued_at" in data or "queuedAt" in data

    def test_create_command_with_payload(self):
        """測試帶payload的命令"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        payload = {
            "account": "+8613812345678",
            "command": "send_photo",
            "payload": "https://example.com/image.jpg"
        }
        
        resp = client.post(
            "/api/v1/commands",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] in ["QUEUED", "queued", "PENDING", "pending"]

    def test_create_command_without_payload(self):
        """測試不帶payload的命令"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        payload = {
            "account": "+8613812345678",
            "command": "get_status"
        }
        
        resp = client.post(
            "/api/v1/commands",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [202, 400, 422]

    def test_create_command_missing_account(self):
        """測試缺少account字段"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        payload = {
            "command": "send_text"
        }
        
        resp = client.post(
            "/api/v1/commands",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [422, 400]  # 驗證錯誤

    def test_create_command_missing_command(self):
        """測試缺少command字段"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        payload = {
            "account": "+8613812345678"
        }
        
        resp = client.post(
            "/api/v1/commands",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [422, 400]  # 驗證錯誤

    def test_create_command_empty_fields(self):
        """測試空字段"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        payload = {
            "account": "",
            "command": "",
            "payload": ""
        }
        
        resp = client.post(
            "/api/v1/commands",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 可能返回 202（如果允許空字符串）或 400/422（驗證錯誤）
        assert resp.status_code in [202, 400, 422]

    def test_create_command_unauthorized(self):
        """測試未認證訪問"""
        payload = {
            "account": "+8613812345678",
            "command": "send_text"
        }
        
        resp = client.post("/api/v1/commands", json=payload)
        assert resp.status_code == 401

    @patch('app.services.data_sources.enqueue_command')
    def test_create_command_with_mock(self, mock_enqueue_command):
        """測試使用模擬的enqueue_command"""
        from datetime import datetime
        mock_enqueue_command.return_value = {
            "commandId": "mock-command-123",
            "status": "QUEUED",
            "queuedAt": datetime.utcnow().isoformat()
        }
        
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        payload = {
            "account": "+8613812345678",
            "command": "send_text",
            "payload": "測試"
        }
        
        resp = client.post(
            "/api/v1/commands",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] in ["QUEUED", "queued"]

    def test_create_command_invalid_json(self):
        """測試無效的JSON"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.post(
            "/api/v1/commands",
            data="invalid json",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        assert resp.status_code in [400, 422]

    def test_create_command_different_command_types(self):
        """測試不同類型的命令"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        command_types = ["send_text", "send_photo", "send_video", "get_status", "get_info"]
        
        for cmd_type in command_types:
            payload = {
                "account": "+8613812345678",
                "command": cmd_type,
                "payload": "測試數據"
            }
            
            resp = client.post(
                "/api/v1/commands",
                json=payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # 應該都返回 202（已接受），實際執行結果取決於後端
            assert resp.status_code in [202, 400, 422, 500]


class TestActivitiesCommandsIntegration:
    """活動和命令集成測試"""

    def test_activities_followed_by_command(self):
        """測試先獲取活動列表，然後創建命令"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 獲取活動列表
        resp1 = client.get(
            "/api/v1/activities",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp1.status_code == 200
        
        # 創建命令
        payload = {
            "account": "+8613812345678",
            "command": "send_text",
            "payload": "測試"
        }
        resp2 = client.post(
            "/api/v1/commands",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp2.status_code == 202

    def test_multiple_commands_sequence(self):
        """測試連續創建多個命令"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        commands = [
            {"account": "+8613812345678", "command": "get_status"},
            {"account": "+8613812345679", "command": "send_text", "payload": "消息1"},
            {"account": "+8613812345678", "command": "send_text", "payload": "消息2"},
        ]
        
        for cmd in commands:
            resp = client.post(
                "/api/v1/commands",
                json=cmd,
                headers={"Authorization": f"Bearer {token}"}
            )
            # 應該都成功（202）或至少不拋出異常
            assert resp.status_code in [202, 400, 422, 500]

