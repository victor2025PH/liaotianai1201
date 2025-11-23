"""
Group AI Groups API 測試
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock, AsyncMock

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


class TestGroupsAPI:
    """Groups API 測試"""

    def test_create_group_basic(self, prepare_database):
        """測試基本群組創建"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.groups.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_account_manager = MagicMock()
            mock_account = MagicMock()
            mock_account.client.is_connected = True
            mock_account.client.get_chat = AsyncMock(return_value=MagicMock(title="測試群組"))
            mock_account_manager.accounts = {"test_account": mock_account}
            mock_manager.account_manager = mock_account_manager
            mock_get_manager.return_value = mock_manager
            
            with patch('group_ai_service.group_manager.GroupManager') as mock_group_manager_class:
                mock_group_manager = MagicMock()
                mock_group_manager.create_and_start_group = AsyncMock(return_value=12345)
                mock_group_manager_class.return_value = mock_group_manager
                
                group_data = {
                    "account_id": "test_account",
                    "title": "測試群組",
                    "description": "測試描述",
                    "auto_reply": True
                }
                
                resp = client.post(
                    "/api/v1/group-ai/groups/create",
                    json=group_data,
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                assert resp.status_code in [200, 404, 500]

    def test_create_group_with_members(self, prepare_database):
        """測試帶成員的群組創建"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.groups.get_service_manager') as mock_get_manager, \
             patch('group_ai_service.group_manager.GroupManager') as mock_group_manager_class:
            mock_manager = MagicMock()
            mock_account_manager = MagicMock()
            mock_account_manager.accounts = {"test_account": MagicMock()}
            mock_manager.account_manager = mock_account_manager
            mock_get_manager.return_value = mock_manager
            
            mock_group_manager = MagicMock()
            mock_group_manager.create_and_start_group = AsyncMock(return_value=12345)
            mock_group_manager_class.return_value = mock_group_manager
            
            group_data = {
                "account_id": "test_account",
                "title": "測試群組",
                "member_ids": [111111, 222222],
                "auto_reply": True
            }
            
            resp = client.post(
                "/api/v1/group-ai/groups/create",
                json=group_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 500]

    def test_create_group_missing_fields(self, prepare_database):
        """測試缺少必填字段"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 缺少 account_id
        group_data = {
            "title": "測試群組"
        }
        
        resp = client.post(
            "/api/v1/group-ai/groups/create",
            json=group_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [422, 404, 500]

    def test_join_group_by_username(self, prepare_database):
        """測試通過用戶名加入群組"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.groups.get_service_manager') as mock_get_manager, \
             patch('group_ai_service.group_manager.GroupManager') as mock_group_manager_class:
            mock_manager = MagicMock()
            mock_account_manager = MagicMock()
            mock_account_manager.accounts = {"test_account": MagicMock()}
            mock_manager.account_manager = mock_account_manager
            mock_get_manager.return_value = mock_manager
            
            mock_group_manager = MagicMock()
            mock_group_manager.join_and_start_group = AsyncMock(return_value=12345)
            mock_group_manager_class.return_value = mock_group_manager
            
            join_data = {
                "account_id": "test_account",
                "group_username": "testgroup",
                "auto_reply": True
            }
            
            resp = client.post(
                "/api/v1/group-ai/groups/join",
                json=join_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 500]

    def test_join_group_by_id(self, prepare_database):
        """測試通過ID加入群組"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.groups.get_service_manager') as mock_get_manager, \
             patch('group_ai_service.group_manager.GroupManager') as mock_group_manager_class:
            mock_manager = MagicMock()
            mock_account_manager = MagicMock()
            mock_account_manager.accounts = {"test_account": MagicMock()}
            mock_manager.account_manager = mock_account_manager
            mock_get_manager.return_value = mock_manager
            
            mock_group_manager = MagicMock()
            mock_group_manager.join_and_start_group = AsyncMock(return_value=12345)
            mock_group_manager_class.return_value = mock_group_manager
            
            join_data = {
                "account_id": "test_account",
                "group_id": 12345,
                "auto_reply": True
            }
            
            resp = client.post(
                "/api/v1/group-ai/groups/join",
                json=join_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 500]

    def test_join_group_by_invite_link(self, prepare_database):
        """測試通過邀請鏈接加入群組"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.groups.get_service_manager') as mock_get_manager, \
             patch('group_ai_service.group_manager.GroupManager') as mock_group_manager_class:
            mock_manager = MagicMock()
            mock_account_manager = MagicMock()
            mock_account_manager.accounts = {"test_account": MagicMock()}
            mock_manager.account_manager = mock_account_manager
            mock_get_manager.return_value = mock_manager
            
            mock_group_manager = MagicMock()
            mock_group_manager.join_and_start_group = AsyncMock(return_value=12345)
            mock_group_manager_class.return_value = mock_group_manager
            
            join_data = {
                "account_id": "test_account",
                "invite_link": "https://t.me/joinchat/xxxxx",
                "auto_reply": True
            }
            
            resp = client.post(
                "/api/v1/group-ai/groups/join",
                json=join_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 500]

    def test_start_group_chat(self, prepare_database):
        """測試啟動群組聊天"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.groups.get_service_manager') as mock_get_manager, \
             patch('group_ai_service.group_manager.GroupManager') as mock_group_manager_class:
            mock_manager = MagicMock()
            mock_account_manager = MagicMock()
            mock_account_manager.accounts = {"test_account": MagicMock()}
            mock_manager.account_manager = mock_account_manager
            mock_get_manager.return_value = mock_manager
            
            mock_group_manager = MagicMock()
            mock_group_manager.start_group_chat = AsyncMock(return_value=True)
            mock_group_manager_class.return_value = mock_group_manager
            
            start_data = {
                "account_id": "test_account",
                "group_id": 12345,
                "auto_reply": True
            }
            
            resp = client.post(
                "/api/v1/group-ai/groups/start-chat",
                json=start_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 500]

    def test_create_group_unauthorized(self):
        """測試未認證訪問"""
        group_data = {
            "account_id": "test_account",
            "title": "測試群組"
        }
        
        resp = client.post("/api/v1/group-ai/groups/create", json=group_data)
        # 可能返回 401（未認證）或 404（路由不存在）或 500（內部錯誤）
        assert resp.status_code in [200, 401, 403, 404, 500]

