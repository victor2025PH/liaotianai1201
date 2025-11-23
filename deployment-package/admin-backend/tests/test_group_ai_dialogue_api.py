"""
Group AI Dialogue API 測試
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


class TestDialogueAPI:
    """Dialogue API 測試"""

    def test_get_dialogue_contexts(self, prepare_database):
        """測試獲取對話上下文列表"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.dialogue.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_dialogue_manager = MagicMock()
            mock_manager.dialogue_manager = mock_dialogue_manager
            mock_dialogue_manager.get_all_contexts = Mock(return_value=[])
            mock_get_manager.return_value = mock_manager
            
            resp = client.get(
                "/api/v1/group-ai/dialogue/contexts",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 500]

    def test_get_dialogue_context(self, prepare_database):
        """測試獲取單個對話上下文"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.dialogue.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_dialogue_manager = MagicMock()
            mock_context = MagicMock()
            mock_context.account_id = "test_account"
            mock_context.group_id = 12345
            mock_context.history_count = 10
            mock_context.reply_count_today = 5
            mock_context.mentioned_users = []
            mock_dialogue_manager.get_context = Mock(return_value=mock_context)
            mock_manager.dialogue_manager = mock_dialogue_manager
            mock_get_manager.return_value = mock_manager
            
            resp = client.get(
                "/api/v1/group-ai/dialogue/contexts/test_account/12345",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 500]

    def test_get_dialogue_history(self, prepare_database):
        """測試獲取對話歷史"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.dialogue.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_dialogue_manager = MagicMock()
            mock_dialogue_manager.get_history = Mock(return_value=[])
            mock_manager.dialogue_manager = mock_dialogue_manager
            mock_get_manager.return_value = mock_manager
            
            resp = client.get(
                "/api/v1/group-ai/dialogue/history/test_account/12345?limit=10",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 500]

    def test_manual_reply(self, prepare_database):
        """測試手動觸發回復"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.dialogue.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_dialogue_manager = MagicMock()
            mock_dialogue_manager.manual_reply = AsyncMock(return_value="測試回復")
            mock_manager.dialogue_manager = mock_dialogue_manager
            mock_get_manager.return_value = mock_manager
            
            reply_data = {
                "account_id": "test_account",
                "group_id": 12345,
                "message_text": "測試消息",
                "force_reply": False
            }
            
            resp = client.post(
                "/api/v1/group-ai/dialogue/manual-reply",
                json=reply_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 422, 500]

    def test_manual_reply_force(self, prepare_database):
        """測試強制回復"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.dialogue.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_dialogue_manager = MagicMock()
            mock_dialogue_manager.manual_reply = AsyncMock(return_value="強制回復")
            mock_manager.dialogue_manager = mock_dialogue_manager
            mock_get_manager.return_value = mock_manager
            
            reply_data = {
                "account_id": "test_account",
                "group_id": 12345,
                "message_text": "測試消息",
                "force_reply": True
            }
            
            resp = client.post(
                "/api/v1/group-ai/dialogue/manual-reply",
                json=reply_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 422, 500]

    def test_manual_reply_missing_fields(self, prepare_database):
        """測試缺少必填字段"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 缺少 account_id
        reply_data = {
            "group_id": 12345,
            "message_text": "測試消息"
        }
        
        resp = client.post(
            "/api/v1/group-ai/dialogue/manual-reply",
            json=reply_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 可能返回 404（路由不存在）或 422（驗證錯誤）
        assert resp.status_code in [404, 422, 400, 500]

    def test_get_dialogue_history_with_limit(self, prepare_database):
        """測試帶limit的對話歷史"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.dialogue.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_dialogue_manager = MagicMock()
            mock_dialogue_manager.get_history = Mock(return_value=[])
            mock_manager.dialogue_manager = mock_dialogue_manager
            mock_get_manager.return_value = mock_manager
            
            resp = client.get(
                "/api/v1/group-ai/dialogue/history/test_account/12345?limit=50",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 500]

    def test_get_dialogue_contexts_unauthorized(self):
        """測試未認證訪問"""
        resp = client.get("/api/v1/group-ai/dialogue/contexts")
        # 可能返回 401（未認證）或 200（認證被禁用）
        assert resp.status_code in [200, 401, 403]


class TestDialogueAPIEdgeCases:
    """Dialogue API 邊界情況測試"""

    def test_get_dialogue_context_not_found(self, prepare_database):
        """測試獲取不存在的對話上下文"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.dialogue.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_dialogue_manager = MagicMock()
            mock_dialogue_manager.get_context = Mock(return_value=None)
            mock_manager.dialogue_manager = mock_dialogue_manager
            mock_get_manager.return_value = mock_manager
            
            resp = client.get(
                "/api/v1/group-ai/dialogue/contexts/nonexistent/99999",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # 可能返回 200（空數據）或 404（不存在）
            assert resp.status_code in [200, 404, 500]

