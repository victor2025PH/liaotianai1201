"""
告警規則 API 測試
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import get_settings

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
    assert resp.status_code == 200, f"登录失败: {resp.text}"
    return resp.json()["access_token"]


# ============ 創建告警規則測試 ============

def test_create_alert_rule():
    """測試創建告警規則"""
    token = _get_token()
    
    rule_data = {
        "name": "測試錯誤率告警",
        "rule_type": "error_rate",
        "alert_level": "warning",
        "threshold_value": 0.2,
        "threshold_operator": ">",
        "enabled": True,
        "notification_method": "email",
        "notification_target": "admin@example.com",
        "description": "測試告警規則"
    }
    
    resp = client.post(
        "/api/v1/group-ai/alert-rules/",
        json=rule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 201, f"創建失敗: {resp.text}"
    data = resp.json()
    assert data["name"] == rule_data["name"]
    assert data["rule_type"] == rule_data["rule_type"]
    assert data["threshold_value"] == rule_data["threshold_value"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_alert_rule_duplicate_name():
    """測試創建重複名稱的告警規則"""
    token = _get_token()
    
    rule_data = {
        "name": "重複名稱測試",
        "rule_type": "error_rate",
        "alert_level": "warning",
        "threshold_value": 0.2,
        "threshold_operator": ">",
        "enabled": True,
        "notification_method": "email",
        "notification_target": "admin@example.com"
    }
    
    # 第一次創建
    resp1 = client.post(
        "/api/v1/group-ai/alert-rules/",
        json=rule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp1.status_code == 201
    
    # 第二次創建相同名稱的規則（應該失敗）
    resp2 = client.post(
        "/api/v1/group-ai/alert-rules/",
        json=rule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp2.status_code == 400
    assert "已存在" in resp2.json()["detail"]


def test_create_alert_rule_invalid_data():
    """測試創建告警規則時使用無效數據"""
    token = _get_token()
    
    # 缺少必填字段
    invalid_rule = {
        "rule_type": "error_rate",
        "threshold_value": 0.2
    }
    
    resp = client.post(
        "/api/v1/group-ai/alert-rules/",
        json=invalid_rule,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 422  # Validation error


def test_create_alert_rule_unauthorized():
    """測試未認證的創建請求"""
    rule_data = {
        "name": "未認證測試",
        "rule_type": "error_rate",
        "threshold_value": 0.2
    }
    
    resp = client.post(
        "/api/v1/group-ai/alert-rules/",
        json=rule_data
    )
    
    assert resp.status_code == 401  # Unauthorized


# ============ 列出告警規則測試 ============

def test_list_alert_rules():
    """測試列出告警規則"""
    token = _get_token()
    
    # 先創建一個規則
    rule_data = {
        "name": "列表測試規則",
        "rule_type": "response_time",
        "alert_level": "error",
        "threshold_value": 1000,
        "threshold_operator": ">",
        "enabled": True,
        "notification_method": "webhook",
        "notification_target": "https://example.com/webhook"
    }
    create_resp = client.post(
        "/api/v1/group-ai/alert-rules/",
        json=rule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_resp.status_code == 201
    
    # 列出規則
    resp = client.get(
        "/api/v1/group-ai/alert-rules/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert data["total"] >= 1


def test_list_alert_rules_with_filter():
    """測試使用過濾器列出告警規則"""
    token = _get_token()
    
    # 創建啟用的規則
    enabled_rule = {
        "name": "啟用規則測試",
        "rule_type": "error_rate",
        "threshold_value": 0.1,
        "enabled": True,
        "notification_method": "email",
        "notification_target": "admin@example.com"
    }
    client.post(
        "/api/v1/group-ai/alert-rules/",
        json=enabled_rule,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 創建禁用的規則
    disabled_rule = {
        "name": "禁用規則測試",
        "rule_type": "error_rate",
        "threshold_value": 0.1,
        "enabled": False,
        "notification_method": "email",
        "notification_target": "admin@example.com"
    }
    client.post(
        "/api/v1/group-ai/alert-rules/",
        json=disabled_rule,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 只列出啟用的規則
    resp = client.get(
        "/api/v1/group-ai/alert-rules/?enabled=true",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert all(rule["enabled"] for rule in data["items"])


def test_list_alert_rules_with_pagination():
    """測試分頁列出告警規則"""
    token = _get_token()
    
    # 創建多個規則
    for i in range(5):
        rule_data = {
            "name": f"分頁測試規則 {i}",
            "rule_type": "error_rate",
            "threshold_value": 0.1 + i * 0.1,
            "enabled": True,
            "notification_method": "email",
            "notification_target": "admin@example.com"
        }
        client.post(
            "/api/v1/group-ai/alert-rules/",
            json=rule_data,
            headers={"Authorization": f"Bearer {token}"}
        )
    
    # 獲取第一頁（每頁2個）
    resp = client.get(
        "/api/v1/group-ai/alert-rules/?page=1&page_size=2",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 2
    assert data["total"] >= 5


# ============ 獲取單個告警規則測試 ============

def test_get_alert_rule():
    """測試獲取單個告警規則"""
    token = _get_token()
    
    # 創建規則
    rule_data = {
        "name": "獲取測試規則",
        "rule_type": "system_errors",
        "alert_level": "error",
        "threshold_value": 10,
        "threshold_operator": ">=",
        "enabled": True,
        "notification_method": "telegram",
        "notification_target": "123456789",
        "description": "系統錯誤測試"
    }
    create_resp = client.post(
        "/api/v1/group-ai/alert-rules/",
        json=rule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_resp.status_code == 201
    rule_id = create_resp.json()["id"]
    
    # 獲取規則
    resp = client.get(
        f"/api/v1/group-ai/alert-rules/{rule_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == rule_id
    assert data["name"] == rule_data["name"]
    assert data["rule_type"] == rule_data["rule_type"]
    assert data["description"] == rule_data["description"]


def test_get_alert_rule_not_found():
    """測試獲取不存在的告警規則"""
    token = _get_token()
    
    resp = client.get(
        "/api/v1/group-ai/alert-rules/non-existent-id",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 404
    assert "不存在" in resp.json()["detail"]


# ============ 更新告警規則測試 ============

def test_update_alert_rule():
    """測試更新告警規則"""
    token = _get_token()
    
    # 創建規則
    rule_data = {
        "name": "更新測試規則",
        "rule_type": "error_rate",
        "threshold_value": 0.1,
        "enabled": True,
        "notification_method": "email",
        "notification_target": "admin@example.com"
    }
    create_resp = client.post(
        "/api/v1/group-ai/alert-rules/",
        json=rule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    rule_id = create_resp.json()["id"]
    
    # 更新規則
    update_data = {
        "threshold_value": 0.3,
        "description": "更新後的描述"
    }
    resp = client.put(
        f"/api/v1/group-ai/alert-rules/{rule_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["threshold_value"] == 0.3
    assert data["description"] == "更新後的描述"
    assert data["name"] == rule_data["name"]  # 未更新的字段保持不變


def test_update_alert_rule_not_found():
    """測試更新不存在的告警規則"""
    token = _get_token()
    
    update_data = {"threshold_value": 0.3}
    resp = client.put(
        "/api/v1/group-ai/alert-rules/non-existent-id",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 404


def test_update_alert_rule_duplicate_name():
    """測試更新規則名稱與其他規則衝突"""
    token = _get_token()
    
    # 創建第一個規則
    rule1_data = {
        "name": "規則一",
        "rule_type": "error_rate",
        "threshold_value": 0.1,
        "enabled": True,
        "notification_method": "email",
        "notification_target": "admin@example.com"
    }
    create_resp1 = client.post(
        "/api/v1/group-ai/alert-rules/",
        json=rule1_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 創建第二個規則
    rule2_data = {
        "name": "規則二",
        "rule_type": "error_rate",
        "threshold_value": 0.2,
        "enabled": True,
        "notification_method": "email",
        "notification_target": "admin@example.com"
    }
    create_resp2 = client.post(
        "/api/v1/group-ai/alert-rules/",
        json=rule2_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    rule2_id = create_resp2.json()["id"]
    
    # 嘗試將規則二改名為規則一（應該失敗）
    update_data = {"name": "規則一"}
    resp = client.put(
        f"/api/v1/group-ai/alert-rules/{rule2_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 400
    assert "已存在" in resp.json()["detail"]


# ============ 刪除告警規則測試 ============

def test_delete_alert_rule():
    """測試刪除告警規則"""
    token = _get_token()
    
    # 創建規則
    rule_data = {
        "name": "刪除測試規則",
        "rule_type": "error_rate",
        "threshold_value": 0.1,
        "enabled": True,
        "notification_method": "email",
        "notification_target": "admin@example.com"
    }
    create_resp = client.post(
        "/api/v1/group-ai/alert-rules/",
        json=rule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    rule_id = create_resp.json()["id"]
    
    # 刪除規則
    resp = client.delete(
        f"/api/v1/group-ai/alert-rules/{rule_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 204
    
    # 驗證規則已刪除
    get_resp = client.get(
        f"/api/v1/group-ai/alert-rules/{rule_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_resp.status_code == 404


def test_delete_alert_rule_not_found():
    """測試刪除不存在的告警規則"""
    token = _get_token()
    
    resp = client.delete(
        "/api/v1/group-ai/alert-rules/non-existent-id",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 404


# ============ 啟用/禁用告警規則測試 ============

def test_enable_alert_rule():
    """測試啟用告警規則"""
    token = _get_token()
    
    # 創建禁用的規則
    rule_data = {
        "name": "啟用測試規則",
        "rule_type": "error_rate",
        "threshold_value": 0.1,
        "enabled": False,
        "notification_method": "email",
        "notification_target": "admin@example.com"
    }
    create_resp = client.post(
        "/api/v1/group-ai/alert-rules/",
        json=rule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    rule_id = create_resp.json()["id"]
    assert create_resp.json()["enabled"] is False
    
    # 啟用規則
    resp = client.post(
        f"/api/v1/group-ai/alert-rules/{rule_id}/enable",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["enabled"] is True


def test_disable_alert_rule():
    """測試禁用告警規則"""
    token = _get_token()
    
    # 創建啟用的規則
    rule_data = {
        "name": "禁用測試規則",
        "rule_type": "error_rate",
        "threshold_value": 0.1,
        "enabled": True,
        "notification_method": "email",
        "notification_target": "admin@example.com"
    }
    create_resp = client.post(
        "/api/v1/group-ai/alert-rules/",
        json=rule_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    rule_id = create_resp.json()["id"]
    assert create_resp.json()["enabled"] is True
    
    # 禁用規則
    resp = client.post(
        f"/api/v1/group-ai/alert-rules/{rule_id}/disable",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["enabled"] is False


def test_enable_alert_rule_not_found():
    """測試啟用不存在的告警規則"""
    token = _get_token()
    
    resp = client.post(
        "/api/v1/group-ai/alert-rules/non-existent-id/enable",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 404


def test_disable_alert_rule_not_found():
    """測試禁用不存在的告警規則"""
    token = _get_token()
    
    resp = client.post(
        "/api/v1/group-ai/alert-rules/non-existent-id/disable",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 404


# ============ 不同規則類型測試 ============

def test_create_different_rule_types():
    """測試創建不同類型的告警規則"""
    token = _get_token()
    
    rule_types = [
        {
            "name": "錯誤率告警",
            "rule_type": "error_rate",
            "threshold_value": 0.2
        },
        {
            "name": "響應時間告警",
            "rule_type": "response_time",
            "threshold_value": 1000
        },
        {
            "name": "系統錯誤告警",
            "rule_type": "system_errors",
            "threshold_value": 10
        },
        {
            "name": "賬號離線告警",
            "rule_type": "account_offline",
            "threshold_value": 0.3
        }
    ]
    
    for rule_data in rule_types:
        full_rule = {
            **rule_data,
            "alert_level": "warning",
            "threshold_operator": ">",
            "enabled": True,
            "notification_method": "email",
            "notification_target": "admin@example.com"
        }
        
        resp = client.post(
            "/api/v1/group-ai/alert-rules/",
            json=full_rule,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code == 201, f"創建 {rule_data['name']} 失敗: {resp.text}"
        assert resp.json()["rule_type"] == rule_data["rule_type"]


# ============ 通知方式測試 ============

def test_create_different_notification_methods():
    """測試創建不同通知方式的告警規則"""
    token = _get_token()
    
    notification_methods = [
        {
            "name": "郵件通知規則",
            "notification_method": "email",
            "notification_target": "admin@example.com, team@example.com"
        },
        {
            "name": "Webhook 通知規則",
            "notification_method": "webhook",
            "notification_target": "https://example.com/webhook"
        },
        {
            "name": "Telegram 通知規則",
            "notification_method": "telegram",
            "notification_target": "123456789"
        }
    ]
    
    for method_data in notification_methods:
        full_rule = {
            **method_data,
            "rule_type": "error_rate",
            "alert_level": "warning",
            "threshold_value": 0.2,
            "threshold_operator": ">",
            "enabled": True
        }
        
        resp = client.post(
            "/api/v1/group-ai/alert-rules/",
            json=full_rule,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code == 201, f"創建 {method_data['name']} 失敗: {resp.text}"
        assert resp.json()["notification_method"] == method_data["notification_method"]
        assert resp.json()["notification_target"] == method_data["notification_target"]

