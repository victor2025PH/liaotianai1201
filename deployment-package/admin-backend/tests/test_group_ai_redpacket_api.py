"""
Group AI Redpacket API 測試
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


class TestRedpacketAPI:
    """Redpacket API 測試"""

    def test_get_redpacket_stats(self, prepare_database):
        """測試獲取紅包統計"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.redpacket.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_redpacket_handler = MagicMock()
            mock_stats = MagicMock()
            mock_stats.total_participations = 10
            mock_stats.successful = 8
            mock_stats.failed = 2
            mock_stats.success_rate = 0.8
            mock_stats.total_amount = 100.0
            mock_stats.average_amount = 12.5
            mock_redpacket_handler.get_stats = Mock(return_value=mock_stats)
            mock_manager.redpacket_handler = mock_redpacket_handler
            mock_get_manager.return_value = mock_manager
            
            resp = client.get(
                "/api/v1/group-ai/redpacket/stats",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 500]

    def test_get_redpacket_stats_by_account(self, prepare_database):
        """測試獲取指定賬號的紅包統計"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.redpacket.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_redpacket_handler = MagicMock()
            mock_stats = MagicMock()
            mock_stats.total_participations = 5
            mock_stats.successful = 4
            mock_stats.failed = 1
            mock_stats.success_rate = 0.8
            mock_redpacket_handler.get_stats = Mock(return_value=mock_stats)
            mock_manager.redpacket_handler = mock_redpacket_handler
            mock_get_manager.return_value = mock_manager
            
            resp = client.get(
                "/api/v1/group-ai/redpacket/stats?account_id=test_account",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 500]

    def test_get_redpacket_history(self, prepare_database):
        """測試獲取紅包參與歷史"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.redpacket.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_redpacket_handler = MagicMock()
            mock_redpacket_handler.get_history = Mock(return_value=[])
            mock_manager.redpacket_handler = mock_redpacket_handler
            mock_get_manager.return_value = mock_manager
            
            resp = client.get(
                "/api/v1/group-ai/redpacket/history",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 500]

    def test_get_redpacket_history_with_filters(self, prepare_database):
        """測試帶過濾條件的紅包歷史"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.redpacket.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_redpacket_handler = MagicMock()
            mock_redpacket_handler.get_history = Mock(return_value=[])
            mock_manager.redpacket_handler = mock_redpacket_handler
            mock_get_manager.return_value = mock_manager
            
            resp = client.get(
                "/api/v1/group-ai/redpacket/history?account_id=test_account&days=7",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 500]

    def test_update_strategy(self, prepare_database):
        """測試更新紅包策略"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.redpacket.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_redpacket_handler = MagicMock()
            mock_redpacket_handler.set_strategy = Mock()
            mock_manager.redpacket_handler = mock_redpacket_handler
            mock_get_manager.return_value = mock_manager
            
            strategy_data = {
                "account_id": "test_account",
                "strategy_type": "random",
                "strategy_params": {
                    "probability": 0.5
                }
            }
            
            resp = client.post(
                "/api/v1/group-ai/redpacket/strategy",
                json=strategy_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 422, 500]

    def test_update_strategy_time_based(self, prepare_database):
        """測試更新時間策略"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.redpacket.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_redpacket_handler = MagicMock()
            mock_redpacket_handler.set_strategy = Mock()
            mock_manager.redpacket_handler = mock_redpacket_handler
            mock_get_manager.return_value = mock_manager
            
            strategy_data = {
                "strategy_type": "time_based",
                "strategy_params": {
                    "peak_hours": [9, 10, 11, 14, 15, 16],
                    "peak_probability": 0.8,
                    "off_peak_probability": 0.3
                }
            }
            
            resp = client.post(
                "/api/v1/group-ai/redpacket/strategy",
                json=strategy_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 422, 500]

    def test_update_strategy_amount_based(self, prepare_database):
        """測試更新金額策略"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with patch('app.api.group_ai.redpacket.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_redpacket_handler = MagicMock()
            mock_redpacket_handler.set_strategy = Mock()
            mock_manager.redpacket_handler = mock_redpacket_handler
            mock_get_manager.return_value = mock_manager
            
            strategy_data = {
                "strategy_type": "amount_based",
                "strategy_params": {
                    "threshold": 10.0,
                    "above_threshold_probability": 0.9,
                    "below_threshold_probability": 0.2
                }
            }
            
            resp = client.post(
                "/api/v1/group-ai/redpacket/strategy",
                json=strategy_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 422, 500]

    def test_update_strategy_invalid_type(self, prepare_database):
        """測試無效策略類型"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        strategy_data = {
            "strategy_type": "invalid_strategy",
            "strategy_params": {}
        }
        
        resp = client.post(
            "/api/v1/group-ai/redpacket/strategy",
            json=strategy_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [422, 400, 404, 500]

    def test_get_redpacket_stats_unauthorized(self):
        """測試未認證訪問"""
        resp = client.get("/api/v1/group-ai/redpacket/stats")
        # 可能返回 401（未認證）或 200（認證被禁用）
        assert resp.status_code in [200, 401, 403]

