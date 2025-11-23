"""
數據源服務測試
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.services.data_sources import (
    get_accounts,
    get_activities,
    get_alerts,
    get_sessions,
    get_session_detail,
    get_logs,
    get_dashboard_stats
)


class TestDataSources:
    """數據源服務測試"""
    
    @pytest.mark.parametrize("endpoint_response,expected_fallback", [
        (None, True),  # API 失敗，使用 fallback
        ({"items": [], "total": 0}, False),  # API 成功但無數據
        ({"items": [{"phone": "+1234567890"}], "total": 1}, False),  # API 成功且有數據
    ])
    def test_get_accounts(self, endpoint_response, expected_fallback):
        """測試獲取賬號列表"""
        with patch('app.services.data_sources._safe_get') as mock_get, \
             patch('app.services.data_sources.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                session_service_url="http://example.com"
            )
            mock_get.return_value = endpoint_response
            
            result = get_accounts()
            
            assert "items" in result
            assert "total" in result
            if endpoint_response:
                assert result["total"] == endpoint_response["total"]
            else:
                # 使用 fallback 數據
                assert result["total"] == 2
    
    @pytest.mark.parametrize("endpoint_response,expected_fallback", [
        (None, True),
        ({"items": [], "total": 0}, False),
        ({"items": [{"id": "RP-001"}], "total": 1}, False),
    ])
    def test_get_activities(self, endpoint_response, expected_fallback):
        """測試獲取活動列表"""
        with patch('app.services.data_sources._safe_get') as mock_get, \
             patch('app.services.data_sources.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                redpacket_service_url="http://example.com"
            )
            mock_get.return_value = endpoint_response
            
            result = get_activities()
            
            assert "items" in result
            assert "total" in result
    
    @pytest.mark.parametrize("endpoint_response,expected_fallback", [
        (None, True),
        ({"items": [], "total": 0}, False),
        ({"items": [{"id": "AL-001"}], "total": 1}, False),
    ])
    def test_get_alerts(self, endpoint_response, expected_fallback):
        """測試獲取告警列表"""
        with patch('app.services.data_sources._safe_get') as mock_get, \
             patch('app.services.data_sources.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                monitoring_service_url="http://example.com"
            )
            mock_get.return_value = endpoint_response
            
            result = get_alerts()
            
            assert "items" in result
            assert "total" in result
    
    def test_get_dashboard_stats(self):
        """測試獲取 Dashboard 統計"""
        result = get_dashboard_stats()
        
        assert "stats" in result
        assert "recent_sessions" in result
        assert "recent_errors" in result
        assert result["stats"]["today_sessions"] == 0
    
    @pytest.mark.parametrize("page,page_size,expected_count", [
        (1, 10, 10),
        (2, 20, 20),
        (1, 5, 5),
    ])
    def test_get_sessions_with_pagination(self, page, page_size, expected_count):
        """測試獲取會話列表（分頁）"""
        with patch('app.services.data_sources._safe_get') as mock_get, \
             patch('app.services.data_sources.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                session_service_url="http://example.com"
            )
            mock_get.return_value = None  # 使用 fallback
            
            result = get_sessions(page=page, page_size=page_size)
            
            assert "items" in result
            assert "total" in result
            assert result["page"] == page
            assert result["page_size"] == page_size
            assert len(result["items"]) == expected_count
    
    def test_get_sessions_with_search(self):
        """測試獲取會話列表（搜索）"""
        with patch('app.services.data_sources._safe_get') as mock_get, \
             patch('app.services.data_sources.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                session_service_url="http://example.com"
            )
            mock_get.return_value = None  # 使用 fallback
            
            result = get_sessions(page=1, page_size=20, q="test")
            
            assert "items" in result
    
    def test_get_sessions_with_time_range(self):
        """測試獲取會話列表（時間範圍）"""
        with patch('app.services.data_sources._safe_get') as mock_get, \
             patch('app.services.data_sources.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                session_service_url="http://example.com"
            )
            mock_get.return_value = None  # 使用 fallback
            
            result = get_sessions(
                page=1,
                page_size=20,
                time_range="7d",
                start_date="2025-01-01",
                end_date="2025-01-07"
            )
            
            assert "items" in result
    
    def test_get_session_detail_success(self):
        """測試獲取會話詳情（成功）"""
        session_id = "test-session-001"
        mock_detail = {
            "id": session_id,
            "user": "test@example.com",
            "messages": 10,
            "status": "completed"
        }
        
        with patch('app.services.data_sources._safe_get') as mock_get, \
             patch('app.services.data_sources.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                session_service_url="http://example.com"
            )
            mock_get.return_value = mock_detail
            
            result = get_session_detail(session_id)
            
            assert result["id"] == session_id
            assert result["user"] == "test@example.com"
    
    def test_get_session_detail_fallback(self):
        """測試獲取會話詳情（fallback）"""
        session_id = "test-session-001"
        
        with patch('app.services.data_sources._safe_get') as mock_get, \
             patch('app.services.data_sources.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                session_service_url="http://example.com"
            )
            mock_get.return_value = None  # API 失敗，使用 fallback
            
            result = get_session_detail(session_id)
            
            assert result["id"] == session_id
            assert "user" in result
            assert "messages" in result
    
    @pytest.mark.parametrize("page,page_size,level", [
        (1, 20, None),
        (1, 10, "error"),
        (2, 15, "warning"),
    ])
    def test_get_logs(self, page, page_size, level):
        """測試獲取日誌列表"""
        # get_logs 現在返回空列表（已遷移到群組AI日誌API）
        result = get_logs(page=page, page_size=page_size, level=level)
        
        assert "items" in result
        assert "total" in result
        assert result["page"] == page
        assert result["page_size"] == page_size
        assert result["total"] == 0
        assert len(result["items"]) == 0

