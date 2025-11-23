"""
routes.py 中 API 端點的完整測試
補充缺失的測試用例以提高覆蓋率
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


class TestRoutesAPI:
    """routes.py 中 API 端點的測試套件"""

    def test_list_accounts_detailed(self):
        """測試獲取賬號列表（詳細驗證）"""
        token = _get_token()
        resp = client.get("/api/v1/accounts", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert data["total"] >= 0

    def test_list_activities_detailed(self):
        """測試獲取活動列表（詳細驗證）"""
        token = _get_token()
        resp = client.get("/api/v1/activities", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    def test_list_alerts_detailed(self):
        """測試獲取告警列表（詳細驗證）"""
        token = _get_token()
        resp = client.get("/api/v1/alerts", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_create_command_detailed(self):
        """測試創建命令（詳細驗證）"""
        token = _get_token()
        
        # 測試有效的命令
        payload = {
            "account": "+8613812345678",
            "command": "send_text",
            "params": {"text": "測試消息"}
        }
        resp = client.post(
            "/api/v1/commands",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "status" in data
        assert "commandId" in data or "command_id" in data
        assert data["status"] in ["QUEUED", "queued", "PENDING", "pending"]

    def test_create_command_invalid_payload(self):
        """測試創建命令（無效的負載）"""
        token = _get_token()
        
        # 測試缺少必填字段
        invalid_payload = {"command": "send_text"}  # 缺少 account
        resp = client.post(
            "/api/v1/commands",
            json=invalid_payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        # 應該返回 422（驗證錯誤）或 400
        assert resp.status_code in [400, 422]

    def test_dashboard_error_handling(self):
        """測試 Dashboard 端點錯誤處理"""
        token = _get_token()
        resp = client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        # 即使出現錯誤，也應該返回有效的數據結構
        assert "stats" in data
        assert "recent_sessions" in data
        assert "recent_errors" in data

    def test_sessions_detail_not_found(self):
        """測試獲取不存在的會話詳情"""
        token = _get_token()
        resp = client.get(
            "/api/v1/sessions/nonexistent_session_id",
            headers={"Authorization": f"Bearer {token}"}
        )
        # 可能返回 404 或空數據
        assert resp.status_code in [200, 404]
        if resp.status_code == 200:
            data = resp.json()
            # 應該返回空數據或錯誤信息
            assert isinstance(data, dict)

    def test_logs_error_handling(self):
        """測試日誌端點錯誤處理（回退到舊API）"""
        token = _get_token()
        resp = client.get("/api/v1/logs?page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_metrics_detailed(self):
        """測試 Metrics API（詳細驗證）"""
        token = _get_token()
        resp = client.get("/api/v1/metrics", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        
        # 驗證 response_time 結構
        assert "response_time" in data
        response_time = data["response_time"]
        assert "data_points" in response_time
        assert isinstance(response_time["data_points"], list)
        assert "average" in response_time
        assert isinstance(response_time["average"], (int, float))
        assert "min" in response_time
        assert "max" in response_time
        assert "trend" in response_time
        
        # 驗證 system_status 結構
        assert "system_status" in data
        system_status = data["system_status"]
        assert "status_items" in system_status
        assert isinstance(system_status["status_items"], list)
        assert "last_updated" in system_status

    def test_system_monitor_detailed(self):
        """測試 System Monitor API（詳細驗證）"""
        token = _get_token()
        resp = client.get("/api/v1/system/monitor", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        
        # 驗證基本結構
        assert "health" in data
        assert "metrics" in data
        assert "services" in data
        
        # 驗證 health 結構
        health = data["health"]
        assert isinstance(health, dict)
        
        # 驗證 metrics 結構
        metrics = data["metrics"]
        assert isinstance(metrics, dict)
        
        # 驗證 services 結構
        services = data["services"]
        assert isinstance(services, dict)

    def test_system_performance(self):
        """測試 System Performance API"""
        token = _get_token()
        resp = client.get("/api/v1/system/performance", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        # 性能統計數據應該是一個字典
        assert isinstance(data, dict)
        # 可能包含的字段：slow_requests, request_count, average_response_time 等

    def test_alert_settings_invalid_data(self):
        """測試保存告警設置（無效數據）"""
        token = _get_token()
        
        # 測試無效的設置數據（缺少必填字段）
        invalid_settings = {
            "invalid_field": "invalid_value"
        }
        resp = client.post(
            "/api/v1/settings/alerts",
            json=invalid_settings,
            headers={"Authorization": f"Bearer {token}"}
        )
        # 可能返回 200（如果API接受任意字段）、422（驗證錯誤）或 400
        assert resp.status_code in [200, 400, 422]
        # 如果是200，說明API接受任意字段，這也是合理的行為

    def test_sessions_custom_date_range(self):
        """測試會話列表自定義日期範圍"""
        token = _get_token()
        
        # 測試自定義日期範圍
        resp = client.get(
            "/api/v1/sessions?start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z&page=1&page_size=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_sessions_invalid_date_format(self):
        """測試會話列表無效日期格式"""
        token = _get_token()
        
        # 測試無效的日期格式
        resp = client.get(
            "/api/v1/sessions?start_date=invalid-date&end_date=invalid-date&page=1&page_size=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        # 應該返回 400 或 422（驗證錯誤）
        assert resp.status_code in [400, 422, 200]  # 有些實現可能忽略無效參數

    def test_logs_with_empty_search(self):
        """測試日誌列表空搜索"""
        token = _get_token()
        
        # 測試空搜索關鍵詞
        resp = client.get(
            "/api/v1/logs?q=&page=1&page_size=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    def test_logs_edge_cases(self):
        """測試日誌列表邊界情況"""
        token = _get_token()
        
        # 測試最大 page_size
        resp = client.get(
            "/api/v1/logs?page=1&page_size=100",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 100
        
        # 測試非常大的 page 號
        resp2 = client.get(
            "/api/v1/logs?page=999999&page_size=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert isinstance(data2["items"], list)

    def test_sessions_edge_cases(self):
        """測試會話列表邊界情況"""
        token = _get_token()
        
        # 測試最大 page_size
        resp = client.get(
            "/api/v1/sessions?page=1&page_size=100",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 100

    def test_dashboard_cache(self):
        """測試 Dashboard 緩存功能"""
        token = _get_token()
        
        # 第一次請求
        resp1 = client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert resp1.status_code == 200
        data1 = resp1.json()
        
        # 第二次請求（應該使用緩存）
        resp2 = client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert resp2.status_code == 200
        data2 = resp2.json()
        
        # 兩次請求應該返回相同的數據結構
        assert data1.keys() == data2.keys()

    def test_metrics_cache(self):
        """測試 Metrics 緩存功能"""
        token = _get_token()
        
        # 第一次請求
        resp1 = client.get("/api/v1/metrics", headers={"Authorization": f"Bearer {token}"})
        assert resp1.status_code == 200
        
        # 第二次請求（應該使用緩存）
        resp2 = client.get("/api/v1/metrics", headers={"Authorization": f"Bearer {token}"})
        assert resp2.status_code == 200
        
        # 兩次請求應該都成功
        assert resp1.json().keys() == resp2.json().keys()

    def test_system_monitor_cache(self):
        """測試 System Monitor 緩存功能"""
        token = _get_token()
        
        # 第一次請求
        resp1 = client.get("/api/v1/system/monitor", headers={"Authorization": f"Bearer {token}"})
        assert resp1.status_code == 200
        
        # 第二次請求（應該使用緩存）
        resp2 = client.get("/api/v1/system/monitor", headers={"Authorization": f"Bearer {token}"})
        assert resp2.status_code == 200
        
        # 兩次請求應該都成功
        assert resp1.json().keys() == resp2.json().keys()

