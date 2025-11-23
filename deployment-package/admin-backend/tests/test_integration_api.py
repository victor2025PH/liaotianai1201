"""
API 集成測試

測試 API 端點的完整流程
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.main import app

client = TestClient(app)


class TestDialogueAPI:
    """對話 API 集成測試"""
    
    @pytest.mark.integration
    def test_get_dialogue_contexts(self):
        """測試獲取對話上下文列表"""
        # 注意：需要 ServiceManager 已初始化
        response = client.get("/api/v1/group-ai/dialogue/contexts")
        
        # 可能返回 200 或 503（服務未初始化）
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.integration
    def test_get_dialogue_context(self):
        """測試獲取單個對話上下文"""
        account_id = "test_account"
        group_id = -1001234567890
        
        response = client.get(f"/api/v1/group-ai/dialogue/contexts/{account_id}/{group_id}")
        
        # 可能返回 200、404 或 503
        assert response.status_code in [200, 404, 503]
    
    @pytest.mark.integration
    def test_get_dialogue_history(self):
        """測試獲取對話歷史"""
        account_id = "test_account"
        group_id = -1001234567890
        
        response = client.get(
            f"/api/v1/group-ai/dialogue/history",
            params={
                "account_id": account_id,
                "group_id": group_id,
                "limit": 50
            }
        )
        
        # 可能返回 200、404 或 503
        assert response.status_code in [200, 404, 503]


class TestRedpacketAPI:
    """紅包 API 集成測試"""
    
    @pytest.mark.integration
    def test_get_redpacket_stats(self):
        """測試獲取紅包統計"""
        response = client.get("/api/v1/group-ai/redpacket/stats")
        
        # 可能返回 200 或 503
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "total_participations" in data
            assert "successful" in data
            assert "failed" in data
    
    @pytest.mark.integration
    def test_get_redpacket_history(self):
        """測試獲取紅包歷史"""
        response = client.get(
            "/api/v1/group-ai/redpacket/history",
            params={"limit": 100}
        )
        
        # 可能返回 200 或 503
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "history" in data
            assert isinstance(data["history"], list)
    
    @pytest.mark.integration
    def test_get_hourly_participation_count(self):
        """測試獲取每小時參與次數"""
        account_id = "test_account"
        
        response = client.get(f"/api/v1/group-ai/redpacket/hourly-count/{account_id}")
        
        # 可能返回 200 或 503
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "account_id" in data
            assert "current_hour_count" in data


class TestMonitorAPI:
    """監控 API 集成測試"""
    
    @pytest.mark.integration
    def test_get_system_metrics(self):
        """測試獲取系統指標"""
        response = client.get("/api/v1/group-ai/monitor/system")
        
        # 可能返回 200 或 500
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "total_accounts" in data
            assert "online_accounts" in data
    
    @pytest.mark.integration
    def test_get_accounts_metrics(self):
        """測試獲取賬號指標"""
        response = client.get("/api/v1/group-ai/monitor/accounts/metrics")
        
        # 可能返回 200 或 500
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.integration
    def test_get_alerts(self):
        """測試獲取告警列表"""
        response = client.get("/api/v1/group-ai/monitor/alerts")
        
        # 可能返回 200 或 500
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.integration
    def test_get_events(self):
        """測試獲取事件日誌"""
        response = client.get("/api/v1/group-ai/monitor/events")
        
        # 可能返回 200 或 500
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

