"""
Performance API 測試
測試 /api/v1/performance/* 端點
"""
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)


def _get_token() -> str:
    """獲取認證 Token（使用測試密碼）"""
    settings = get_settings()
    test_password = "testpass123"
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": settings.admin_default_email, "password": test_password},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


class TestPerformanceAPI:
    """Performance API 測試套件"""

    def test_get_cache_stats(self):
        """測試獲取緩存統計"""
        token = _get_token()
        resp = client.get("/api/v1/performance/cache/stats", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        # 緩存統計應該是一個字典
        assert isinstance(data, dict)
        # 可能包含的字段：hits, misses, size, etc.

    def test_clear_cache(self):
        """測試清除緩存"""
        token = _get_token()
        resp = client.post("/api/v1/performance/cache/clear", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        # 應該返回操作結果
        assert isinstance(data, dict)
        # 可能包含 success 或 message 字段

    def test_get_performance_stats(self):
        """測試獲取性能統計"""
        token = _get_token()
        resp = client.get("/api/v1/performance/stats", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        # 性能統計應該是一個字典
        assert isinstance(data, dict)
        # 可能包含的字段：slow_requests, request_count, average_response_time 等

    def test_performance_endpoints_require_auth(self):
        """測試性能端點需要認證"""
        endpoints = [
            "/api/v1/performance/cache/stats",
            "/api/v1/performance/cache/clear",
            "/api/v1/performance/stats",
        ]
        
        for endpoint in endpoints:
            if endpoint.endswith("/clear"):
                resp = client.post(endpoint)
            else:
                resp = client.get(endpoint)
            
            assert resp.status_code == 401, f"{endpoint} 應該返回 401"

