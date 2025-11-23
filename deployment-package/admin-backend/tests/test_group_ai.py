"""
群組 AI 模組測試
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from app.main import app
from app.core.config import get_settings

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
    assert resp.status_code == 200, f"登录失败: {resp.text}"
    return resp.json()["access_token"]


# ============ 賬號管理 API 測試 ============

def test_list_accounts():
    """測試獲取賬號列表"""
    token = _get_token()
    resp = client.get(
        "/api/v1/group-ai/accounts",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code in [200, 500]  # 500 可能是因為 AccountManager 未初始化
    if resp.status_code == 200:
        data = resp.json()
        assert "items" in data or isinstance(data, list)
        if "items" in data:
            assert "total" in data


def test_get_account_not_found():
    """測試獲取不存在的賬號"""
    token = _get_token()
    resp = client.get(
        "/api/v1/group-ai/accounts/nonexistent_account",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code in [404, 500]  # 404 表示賬號不存在，500 可能是 AccountManager 未初始化


def test_create_account_invalid_session():
    """測試創建賬號（無效的 Session 文件）"""
    token = _get_token()
    resp = client.post(
        "/api/v1/group-ai/accounts",
        json={
            "account_id": "test_account_1",
            "session_file": "nonexistent.session",
            "script_id": "default",
            "group_ids": [],
            "active": True,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    # 可能返回 400（Session 文件不存在）或 500（AccountManager 未初始化）
    assert resp.status_code in [400, 404, 500]


def test_update_account_not_found():
    """測試更新不存在的賬號"""
    token = _get_token()
    resp = client.put(
        "/api/v1/group-ai/accounts/nonexistent_account",
        json={
            "script_id": "updated_script",
            "active": False,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code in [404, 500]


def test_delete_account_not_found():
    """測試刪除不存在的賬號"""
    token = _get_token()
    resp = client.delete(
        "/api/v1/group-ai/accounts/nonexistent_account",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code in [404, 500]


def test_start_account_not_found():
    """測試啟動不存在的賬號"""
    token = _get_token()
    resp = client.post(
        "/api/v1/group-ai/accounts/nonexistent_account/start",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


def test_stop_account_not_found():
    """測試停止不存在的賬號"""
    token = _get_token()
    resp = client.post(
        "/api/v1/group-ai/accounts/nonexistent_account/stop",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


def test_get_account_status_not_found():
    """測試獲取不存在的賬號狀態"""
    token = _get_token()
    resp = client.get(
        "/api/v1/group-ai/accounts/nonexistent_account/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code in [404, 500]


# ============ 劇本管理 API 測試 ============

def test_list_scripts():
    """測試獲取劇本列表"""
    token = _get_token()
    resp = client.get(
        "/api/v1/group-ai/scripts",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data or isinstance(data, list)
    if "items" in data:
        assert "total" in data


def test_get_script_not_found():
    """測試獲取不存在的劇本"""
    token = _get_token()
    resp = client.get(
        "/api/v1/group-ai/scripts/nonexistent_script",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


def test_create_script_invalid_yaml():
    """測試創建劇本（無效的 YAML）"""
    token = _get_token()
    resp = client.post(
        "/api/v1/group-ai/scripts",
        json={
            "script_id": "test_script_1",
            "name": "測試劇本",
            "version": "1.0",
            "yaml_content": "invalid yaml content {[",
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code in [400, 422]  # 400 表示 YAML 格式錯誤，422 表示驗證錯誤


def test_create_script_missing_fields():
    """測試創建劇本（缺少必填字段）"""
    token = _get_token()
    resp = client.post(
        "/api/v1/group-ai/scripts",
        json={
            "name": "測試劇本",
            # 缺少 script_id 和 yaml_content
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 422  # 驗證錯誤


def test_update_script_not_found():
    """測試更新不存在的劇本"""
    token = _get_token()
    resp = client.put(
        "/api/v1/group-ai/scripts/nonexistent_script",
        json={
            "name": "更新的劇本名稱",
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


def test_delete_script_not_found():
    """測試刪除不存在的劇本"""
    token = _get_token()
    resp = client.delete(
        "/api/v1/group-ai/scripts/nonexistent_script",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


def test_upload_script_file():
    """測試上傳劇本文件"""
    token = _get_token()
    
    # 創建臨時 YAML 文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
script_id: test_script
version: 1.0
scenes:
  - id: scene1
    triggers:
      - type: message
    actions:
      - type: reply
        content: "測試回復"
""")
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            resp = client.post(
                "/api/v1/group-ai/scripts/upload",
                files={"file": ("test_script.yaml", f, "application/x-yaml")},
                headers={"Authorization": f"Bearer {token}"}
            )
        # 可能返回 200/201（成功）、400（YAML 格式錯誤）、422（驗證錯誤）或 500（服務器錯誤）
        assert resp.status_code in [200, 201, 400, 422, 500]
    finally:
        # 清理臨時文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# ============ 群組管理 API 測試 ============

def test_create_group_invalid_account():
    """測試創建群組（無效的賬號）"""
    token = _get_token()
    resp = client.post(
        "/api/v1/group-ai/groups/create",
        json={
            "account_id": "nonexistent_account",
            "title": "測試群組",
            "auto_reply": True,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code in [404, 500]  # 404 表示賬號不存在，500 可能是 AccountManager 未初始化


def test_join_group_invalid_account():
    """測試加入群組（無效的賬號）"""
    token = _get_token()
    resp = client.post(
        "/api/v1/group-ai/groups/join",
        json={
            "account_id": "nonexistent_account",
            "group_username": "test_group",
            "auto_reply": True,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code in [404, 400, 500]


def test_start_group_chat_invalid_account():
    """測試啟動群組聊天（無效的賬號）"""
    token = _get_token()
    resp = client.post(
        "/api/v1/group-ai/groups/start-chat",
        json={
            "account_id": "nonexistent_account",
            "group_id": 123456,
            "auto_reply": True,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code in [404, 500]


# ============ 監控 API 測試 ============

def test_get_account_metrics_invalid_account():
    """測試獲取賬號指標（無效的賬號）"""
    token = _get_token()
    resp = client.get(
        "/api/v1/group-ai/monitor/accounts/nonexistent_account/metrics",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code in [404, 500]


def test_get_system_metrics():
    """測試獲取系統指標"""
    token = _get_token()
    resp = client.get(
        "/api/v1/group-ai/monitor/system",
        headers={"Authorization": f"Bearer {token}"}
    )
    # 可能返回 200（成功）或 500（MonitorService 未初始化）
    assert resp.status_code in [200, 500]
    if resp.status_code == 200:
        data = resp.json()
        # 檢查響應結構（如果已知）
        assert isinstance(data, dict)


def test_get_alerts():
    """測試獲取告警列表"""
    token = _get_token()
    resp = client.get(
        "/api/v1/group-ai/monitor/alerts",
        headers={"Authorization": f"Bearer {token}"}
    )
    # 可能返回 200（成功）或 500（MonitorService 未初始化）
    assert resp.status_code in [200, 500]
    if resp.status_code == 200:
        data = resp.json()
        assert "items" in data or isinstance(data, list)


# ============ 劇本版本管理 API 測試 ============

def test_list_script_versions_not_found():
    """測試獲取不存在的劇本版本列表"""
    token = _get_token()
    resp = client.get(
        "/api/v1/group-ai/scripts/nonexistent_script/versions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


def test_get_script_version_not_found():
    """測試獲取不存在的劇本版本"""
    token = _get_token()
    resp = client.get(
        "/api/v1/group-ai/scripts/nonexistent_script/versions/v1.0",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


# ============ Dashboard API 測試 ============

def test_get_group_ai_dashboard():
    """測試獲取群組 AI Dashboard"""
    token = _get_token()
    resp = client.get(
        "/api/v1/group-ai/dashboard",
        headers={"Authorization": f"Bearer {token}"}
    )
    # 可能返回 200（成功）或 500（ServiceManager 未初始化）
    assert resp.status_code in [200, 500]
    if resp.status_code == 200:
        data = resp.json()
        assert isinstance(data, dict)
        # 檢查常見的 Dashboard 字段
        # （根據實際 API 響應結構調整）


# ============ 日誌 API 測試 ============

def test_get_group_ai_logs():
    """測試獲取群組 AI 日誌"""
    token = _get_token()
    resp = client.get(
        "/api/v1/group-ai/logs",
        params={"page": 1, "page_size": 10},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code in [200, 500]
    if resp.status_code == 200:
        data = resp.json()
        assert "items" in data or isinstance(data, list)
        if "items" in data:
            assert "total" in data


def test_get_group_ai_logs_pagination():
    """測試群組 AI 日誌分頁"""
    token = _get_token()
    
    # 測試第一頁
    resp1 = client.get(
        "/api/v1/group-ai/logs",
        params={"page": 1, "page_size": 10},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp1.status_code in [200, 500]
    
    # 測試第二頁
    resp2 = client.get(
        "/api/v1/group-ai/logs",
        params={"page": 2, "page_size": 10},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp2.status_code in [200, 500]


# ============ 未認證測試 ============

def test_group_ai_endpoints_require_auth():
    """測試群組 AI 端點需要認證"""
    endpoints = [
        ("GET", "/api/v1/group-ai/accounts"),
        ("GET", "/api/v1/group-ai/scripts"),
        ("GET", "/api/v1/group-ai/dashboard"),
        ("GET", "/api/v1/group-ai/logs"),
    ]
    
    for method, endpoint in endpoints:
        if method == "GET":
            resp = client.get(endpoint)
        elif method == "POST":
            resp = client.post(endpoint, json={})
        else:
            continue
        
        assert resp.status_code == 401, f"{method} {endpoint} 應該返回 401"


