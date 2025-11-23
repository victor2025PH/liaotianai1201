"""
性能監控中間件測試
"""
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request, Response
from fastapi.testclient import TestClient

from app.middleware.performance import (
    PerformanceMonitoringMiddleware,
    get_performance_stats,
    reset_performance_stats
)
from app.main import app


class TestPerformanceMonitoringMiddleware:
    """性能監控中間件測試"""

    @pytest.fixture(autouse=True)
    def reset_stats(self):
        """每個測試前重置統計"""
        reset_performance_stats()
        yield
        reset_performance_stats()

    @pytest.mark.asyncio
    async def test_middleware_skip_health_check(self):
        """測試跳過健康檢查端點"""
        mock_app = Mock()
        mock_app.__call__ = AsyncMock(return_value=Response())
        
        middleware = PerformanceMonitoringMiddleware(mock_app)
        
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/health"
        mock_request.method = "GET"
        
        mock_call_next = AsyncMock(return_value=Response())
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # 健康檢查不應該被統計
        stats = get_performance_stats()
        assert stats["request_count"] == 0

    @pytest.mark.asyncio
    async def test_middleware_skip_openapi_docs(self):
        """測試跳過 OpenAPI 文檔端點"""
        middleware = PerformanceMonitoringMiddleware(Mock())
        
        paths_to_skip = ["/docs", "/openapi.json", "/redoc", "/"]
        
        for path in paths_to_skip:
            reset_performance_stats()
            
            mock_request = Mock(spec=Request)
            mock_request.url.path = path
            mock_request.method = "GET"
            
            mock_call_next = AsyncMock(return_value=Response())
            
            await middleware.dispatch(mock_request, mock_call_next)
            
            # 這些端點不應該被統計
            stats = get_performance_stats()
            assert stats["request_count"] == 0

    @pytest.mark.asyncio
    async def test_middleware_track_request(self):
        """測試追蹤正常請求"""
        middleware = PerformanceMonitoringMiddleware(Mock())
        
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/v1/test"
        mock_request.method = "GET"
        mock_request.query_params = ""
        
        mock_response = Response()
        mock_response.status_code = 200
        
        mock_call_next = AsyncMock(return_value=mock_response)
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # 應該被統計
        stats = get_performance_stats()
        assert stats["request_count"] == 1
        assert stats["average_response_time_ms"] > 0

    @pytest.mark.asyncio
    async def test_middleware_add_process_time_header(self):
        """測試添加響應時間頭"""
        middleware = PerformanceMonitoringMiddleware(Mock())
        
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/v1/test"
        mock_request.method = "GET"
        mock_request.query_params = ""
        
        mock_response = Response()
        mock_response.status_code = 200
        
        mock_call_next = AsyncMock(return_value=mock_response)
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # 應該包含 X-Process-Time 頭
        assert "X-Process-Time" in response.headers
        assert float(response.headers["X-Process-Time"]) >= 0

    @pytest.mark.asyncio
    async def test_middleware_track_slow_request(self):
        """測試追蹤慢請求"""
        middleware = PerformanceMonitoringMiddleware(Mock(), slow_request_threshold_ms=10.0)
        
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/v1/test"
        mock_request.method = "GET"
        mock_request.query_params = ""
        
        mock_response = Response()
        mock_response.status_code = 200
        
        # 模擬慢請求（超過閾值）
        async def slow_call_next(request):
            await asyncio.sleep(0.02)  # 20ms，超過 10ms 閾值
            return mock_response
        
        import asyncio
        response = await middleware.dispatch(mock_request, slow_call_next)
        
        # 應該記錄慢請求
        stats = get_performance_stats()
        assert stats["slow_requests_count"] > 0
        assert len(stats["slow_requests"]) > 0

    @pytest.mark.asyncio
    async def test_middleware_handle_exception(self):
        """測試處理異常"""
        middleware = PerformanceMonitoringMiddleware(Mock())
        
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/v1/test"
        mock_request.method = "GET"
        
        mock_call_next = AsyncMock(side_effect=Exception("Test error"))
        
        with pytest.raises(Exception):
            await middleware.dispatch(mock_request, mock_call_next)
        
        # 異常應該被記錄，但可能不會增加請求計數（取決於實現）

    @pytest.mark.asyncio
    async def test_middleware_track_error_response(self):
        """測試追蹤錯誤響應"""
        middleware = PerformanceMonitoringMiddleware(Mock())
        
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/v1/test"
        mock_request.method = "GET"
        mock_request.query_params = ""
        
        mock_response = Response()
        mock_response.status_code = 500  # 錯誤狀態碼
        
        mock_call_next = AsyncMock(return_value=mock_response)
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # 錯誤響應應該被記錄（日誌級別更高）
        stats = get_performance_stats()
        assert stats["request_count"] == 1

    def test_get_performance_stats_empty(self):
        """測試獲取空統計"""
        reset_performance_stats()
        stats = get_performance_stats()
        
        assert stats["request_count"] == 0
        assert stats["average_response_time_ms"] == 0.0
        assert stats["total_response_time_ms"] == 0.0
        assert stats["slow_requests_count"] == 0
        assert stats["slow_requests"] == []

    def test_get_performance_stats_with_data(self):
        """測試獲取有數據的統計"""
        reset_performance_stats()
        
        # 手動設置統計數據（模擬請求）
        from app.middleware.performance import _performance_stats
        _performance_stats["request_count"] = 10
        _performance_stats["total_response_time"] = 500.0
        
        stats = get_performance_stats()
        
        assert stats["request_count"] == 10
        assert stats["average_response_time_ms"] == 50.0  # 500 / 10
        assert stats["total_response_time_ms"] == 500.0

    def test_reset_performance_stats(self):
        """測試重置統計"""
        # 設置一些數據
        from app.middleware.performance import _performance_stats
        _performance_stats["request_count"] = 100
        _performance_stats["total_response_time"] = 5000.0
        _performance_stats["slow_requests"] = [{"path": "/test"}]
        
        reset_performance_stats()
        
        stats = get_performance_stats()
        assert stats["request_count"] == 0
        assert stats["total_response_time_ms"] == 0.0
        assert stats["slow_requests_count"] == 0

    @pytest.mark.asyncio
    async def test_middleware_slow_requests_limit(self):
        """測試慢請求列表限制"""
        middleware = PerformanceMonitoringMiddleware(Mock(), slow_request_threshold_ms=1.0)
        
        # 創建超過100個慢請求
        import asyncio
        for i in range(150):
            mock_request = Mock(spec=Request)
            mock_request.url.path = f"/api/v1/test{i}"
            mock_request.method = "GET"
            mock_request.query_params = ""
            
            mock_response = Response()
            mock_response.status_code = 200
            
            async def slow_call_next(request):
                await asyncio.sleep(0.002)  # 2ms，超過 1ms 閾值
                return mock_response
            
            await middleware.dispatch(mock_request, slow_call_next)
        
        stats = get_performance_stats()
        # 應該只保留最近100個慢請求
        assert len(stats["slow_requests"]) <= 100
        # get_performance_stats 返回最近20個
        assert len(stats["slow_requests"]) <= 20


class TestPerformanceStatsIntegration:
    """性能統計集成測試"""

    def test_performance_stats_through_client(self):
        """通過 TestClient 測試性能統計"""
        reset_performance_stats()
        
        client = TestClient(app)
        
        # 發送請求（健康檢查會被跳過，所以使用需要認證的端點可能失敗，但不影響統計）
        try:
            client.get("/health")  # 健康檢查，不會被統計
        except:
            pass
        
        stats = get_performance_stats()
        # 健康檢查應該被跳過
        assert stats["request_count"] == 0

