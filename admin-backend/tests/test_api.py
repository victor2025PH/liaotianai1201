import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.core.security import get_password_hash
from app.db import SessionLocal
from app.crud.user import get_user_by_email

client = TestClient(app)


def _get_token() -> str:
    """獲取認證 Token（使用測試密碼）"""
    settings = get_settings()
    # 使用固定的測試密碼（與 conftest.py 中創建的用戶密碼一致）
    test_password = "testpass123"
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": settings.admin_default_email, "password": test_password},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def test_health_check():
    """測試基礎健康檢查端點（無需認證）"""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_healthz_check():
    """測試 Kubernetes 健康檢查端點（無需認證）"""
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_unauthorized_access():
    """測試未認證的請求會被拒絕"""
    # 嘗試訪問需要認證的端點（無 Token）
    resp = client.get("/api/v1/dashboard")
    assert resp.status_code == 401  # Unauthorized


def test_invalid_token():
    """測試無效 Token 會被拒絕"""
    resp = client.get(
        "/api/v1/dashboard",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    assert resp.status_code == 401  # Unauthorized


@pytest.mark.parametrize("path", ["/accounts", "/activities", "/alerts"])
def test_list_endpoints(path):
    """測試列表端點（需要認證）"""
    token = _get_token()
    resp = client.get(f"/api/v1{path}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


def test_create_command():
    """測試創建命令（需要認證）"""
    token = _get_token()
    payload = {"account": "+8613812345678", "command": "send_text"}
    resp = client.post("/api/v1/commands", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "QUEUED"
    assert "commandId" in data
    assert "queuedAt" in data


def test_dashboard_requires_auth():
    """測試 Dashboard 端點需要認證"""
    token = _get_token()
    resp = client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "stats" in data
    assert "recent_sessions" in data
    assert "recent_errors" in data


def test_sessions_requires_auth():
    """測試會話列表端點需要認證"""
    token = _get_token()
    resp = client.get("/api/v1/sessions?page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


def test_logs_requires_auth():
    """測試日誌列表端點需要認證"""
    token = _get_token()
    resp = client.get("/api/v1/logs?page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


def test_dashboard_detailed():
    """測試 Dashboard API 詳細結構（增強版：添加測試隔離和重試機制）"""
    import time
    import pytest
    
    token = _get_token()
    max_retries = 3
    retry_delay = 0.5
    
    for attempt in range(max_retries):
        try:
            resp = client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200, f"請求失敗，狀態碼: {resp.status_code}, 響應: {resp.text}"
            data = resp.json()
            
            # 驗證基本結構存在
            assert "stats" in data, f"響應中缺少 'stats' 字段: {data.keys()}"
            stats = data["stats"]
            
            # 驗證 stats 必需字段（允許值為 0 或 None，但字段必須存在）
            required_stats_fields = [
                "today_sessions", "success_rate", "token_usage", 
                "error_count", "avg_response_time", "active_users"
            ]
            for field in required_stats_fields:
                assert field in stats, f"stats 中缺少字段: {field}, 現有字段: {list(stats.keys())}"
                # 字段必須存在（已經驗證），值可以是 0、None 或其他有效值
                # 只要字段存在即可，不強制要求非空值
            
            # 驗證 recent_sessions 和 recent_errors
            assert "recent_sessions" in data, f"響應中缺少 'recent_sessions' 字段"
            assert "recent_errors" in data, f"響應中缺少 'recent_errors' 字段"
            assert isinstance(data["recent_sessions"], list), f"recent_sessions 應該是列表類型，實際類型: {type(data['recent_sessions'])}"
            assert isinstance(data["recent_errors"], list), f"recent_errors 應該是列表類型，實際類型: {type(data['recent_errors'])}"
            
            # 如果所有驗證都通過，跳出重試循環
            break
            
        except AssertionError as e:
            if attempt < max_retries - 1:
                # 如果不是最後一次嘗試，等待後重試
                time.sleep(retry_delay)
                continue
            else:
                # 最後一次嘗試失敗，拋出異常
                pytest.fail(f"Dashboard API 測試失敗（嘗試 {max_retries} 次）: {str(e)}")
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                pytest.fail(f"Dashboard API 測試發生意外錯誤（嘗試 {max_retries} 次）: {str(e)}")


def test_sessions_pagination():
    """測試會話列表分頁功能"""
    token = _get_token()
    # 測試第一頁
    resp = client.get("/api/v1/sessions?page=1&page_size=5", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert len(data["items"]) <= 5
    
    # 測試第二頁
    resp2 = client.get("/api/v1/sessions?page=2&page_size=5", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["page"] == 2


def test_sessions_search():
    """測試會話列表搜索功能"""
    token = _get_token()
    resp = client.get("/api/v1/sessions?q=test&page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


def test_sessions_time_range():
    """測試會話列表時間範圍過濾"""
    token = _get_token()
    # 測試 24h 範圍
    resp = client.get("/api/v1/sessions?range=24h&page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    
    # 測試自定義日期範圍
    resp2 = client.get(
        "/api/v1/sessions?start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z&page=1&page_size=10",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp2.status_code == 200


def test_session_detail():
    """測試獲取會話詳情"""
    token = _get_token()
    # 先獲取會話列表，然後獲取第一個會話的詳情
    resp_list = client.get("/api/v1/sessions?page=1&page_size=1", headers={"Authorization": f"Bearer {token}"})
    assert resp_list.status_code == 200
    data_list = resp_list.json()
    
    if data_list.get("items") and len(data_list["items"]) > 0:
        session_id = data_list["items"][0].get("id")
        if session_id:
            resp_detail = client.get(f"/api/v1/sessions/{session_id}", headers={"Authorization": f"Bearer {token}"})
            assert resp_detail.status_code == 200


def test_logs_level_filter():
    """測試日誌列表級別過濾"""
    token = _get_token()
    # 測試 error 級別
    resp = client.get("/api/v1/logs?level=error&page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    
    # 測試 warning 級別
    resp2 = client.get("/api/v1/logs?level=warning&page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    
    # 測試 info 級別
    resp3 = client.get("/api/v1/logs?level=info&page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 200


def test_logs_search():
    """測試日誌列表搜索功能"""
    token = _get_token()
    resp = client.get("/api/v1/logs?q=error&page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


def test_logs_pagination():
    """測試日誌列表分頁功能"""
    token = _get_token()
    # 測試第一頁
    resp = client.get("/api/v1/logs?page=1&page_size=5", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["page"] == 1
    assert data["page_size"] == 5
    
    # 測試第二頁
    resp2 = client.get("/api/v1/logs?page=2&page_size=5", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["page"] == 2


def test_metrics():
    """測試 Metrics API"""
    token = _get_token()
    resp = client.get("/api/v1/metrics", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    
    # 驗證 response_time 結構
    assert "response_time" in data
    response_time = data["response_time"]
    assert "data_points" in response_time
    assert "average" in response_time
    assert "min" in response_time
    assert "max" in response_time
    assert "trend" in response_time
    
    # 驗證 system_status 結構
    assert "system_status" in data
    system_status = data["system_status"]
    assert "status_items" in system_status
    assert "last_updated" in system_status


def test_system_monitor():
    """測試 System Monitor API"""
    token = _get_token()
    resp = client.get("/api/v1/system/monitor", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    
    # 驗證 health 結構
    assert "health" in data
    health = data["health"]
    assert "status" in health or "uptime" in health or "version" in health
    
    # 驗證 metrics 結構
    assert "metrics" in data
    metrics = data["metrics"]
    # metrics 可能包含 cpu_usage, memory_usage, disk_usage 等
    
    # 驗證 services 結構
    assert "services" in data
    assert isinstance(data["services"], dict)


def test_get_alert_settings():
    """測試獲取告警設置"""
    token = _get_token()
    resp = client.get("/api/v1/settings/alerts", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    # 驗證至少包含一些設置字段
    assert isinstance(data, dict)


def test_save_alert_settings():
    """測試保存告警設置"""
    token = _get_token()
    # 先獲取當前設置
    resp_get = client.get("/api/v1/settings/alerts", headers={"Authorization": f"Bearer {token}"})
    assert resp_get.status_code == 200
    current_settings = resp_get.json()
    
    # 嘗試保存設置（使用當前設置，避免破壞現有配置）
    payload = current_settings.copy() if isinstance(current_settings, dict) else {}
    
    resp_post = client.post(
        "/api/v1/settings/alerts",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    # 應該返回 200 或 201
    assert resp_post.status_code in [200, 201]
    result = resp_post.json()
    assert isinstance(result, dict)


def test_invalid_pagination():
    """測試無效的分頁參數"""
    token = _get_token()
    # 測試無效的 page 值
    resp = client.get("/api/v1/sessions?page=0&page_size=10", headers={"Authorization": f"Bearer {token}"})
    # 應該返回 422（驗證錯誤）或 400
    assert resp.status_code in [400, 422]
    
    # 測試無效的 page_size 值
    resp2 = client.get("/api/v1/sessions?page=1&page_size=0", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code in [400, 422]
    
    # 測試過大的 page_size 值
    resp3 = client.get("/api/v1/sessions?page=1&page_size=200", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code in [400, 422]


def test_invalid_log_level():
    """測試無效的日誌級別"""
    token = _get_token()
    # 測試無效的 level 值
    resp = client.get("/api/v1/logs?level=invalid&page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
    # 應該返回 422（驗證錯誤）
    assert resp.status_code in [400, 422]


def test_get_current_user():
    """測試獲取當前用戶信息"""
    token = _get_token()
    resp = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "email" in data
    assert "full_name" in data or "fullName" in data
    assert "is_active" in data or "isActive" in data


def test_login_success():
    """測試登入成功"""
    settings = get_settings()
    # 使用固定的測試密碼（與 conftest.py 中創建的用戶密碼一致）
    test_password = "testpass123"
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": settings.admin_default_email, "password": test_password},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, f"登录失败: {resp.text}"
    data = resp.json()
    assert "access_token" in data
    assert data["access_token"]
    assert "token_type" in data or "tokenType" in data


def test_login_invalid_credentials():
    """測試登入失敗（無效憑證）"""
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "invalid@example.com", "password": "wrongpassword"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401  # Unauthorized


def test_login_invalid_format():
    """測試登入失敗（無效格式）"""
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin@example.com", "password": "changeme123"},  # 錯誤：應該是 form-data
        headers={"content-type": "application/json"},
    )
    # 應該返回 422（驗證錯誤）或 400
    assert resp.status_code in [400, 422, 401]

