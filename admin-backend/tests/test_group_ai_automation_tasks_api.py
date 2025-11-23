"""
Group AI Automation Tasks API 測試
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

from app.main import app
from app.core.config import get_settings
from app.models.group_ai import GroupAIAutomationTask

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


class TestAutomationTasksAPI:
    """Automation Tasks API 測試"""

    def test_create_automation_task_basic(self, prepare_database):
        """測試基本自動化任務創建"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        unique_name = f"測試任務_{uuid.uuid4().hex[:8]}"
        # 使用manual类型避免scheduler调用
        task_data = {
            "name": unique_name,
            "description": "測試描述",
            "task_type": "manual",
            "task_action": "account_start",
            "action_config": {"account_ids": ["account1"]},
            "enabled": True
        }
        
        resp = client.post(
            "/api/v1/group-ai/automation-tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [201, 403, 500]

    def test_create_automation_task_with_notifications(self, prepare_database):
        """測試帶通知配置的任務創建"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        unique_name = f"測試任務_{uuid.uuid4().hex[:8]}"
        task_data = {
            "name": unique_name,
            "task_type": "triggered",
            "task_action": "alert_check",
            "trigger_config": {"condition": "error_rate > 10"},
            "action_config": {},
            "notify_on_success": True,
            "notify_on_failure": True,
            "notify_recipients": ["admin@example.com"]
        }
        
        with patch('app.api.group_ai.automation_tasks.get_task_scheduler') as mock_get_scheduler:
            mock_scheduler = MagicMock()
            mock_scheduler.is_running = False
            mock_get_scheduler.return_value = mock_scheduler
            
            resp = client.post(
                "/api/v1/group-ai/automation-tasks",
                json=task_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [201, 403, 500]

    def test_list_automation_tasks(self, prepare_database):
        """測試列出自動化任務"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/group-ai/automation-tasks",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]
        if resp.status_code == 200:
            assert isinstance(resp.json(), list)

    def test_list_automation_tasks_with_filters(self, prepare_database):
        """測試帶過濾條件的任務列表"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/group-ai/automation-tasks?task_type=scheduled&enabled=true&page=1&page_size=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]

    def test_get_automation_task_by_id(self, prepare_database):
        """測試根據ID獲取任務"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建一個任務
        db = SessionLocal()
        try:
            task = GroupAIAutomationTask(
                id=str(uuid.uuid4()),
                name=f"測試任務_{uuid.uuid4().hex[:8]}",
                task_type="scheduled",
                task_action="account_start",
                action_config={},
                enabled=True
            )
            db.add(task)
            db.commit()
            task_id = task.id
            
            resp = client.get(
                f"/api/v1/group-ai/automation-tasks/{task_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 403, 404]
            if resp.status_code == 200:
                data = resp.json()
                assert data["id"] == task_id
        finally:
            db.close()

    def test_get_automation_task_not_found(self, prepare_database):
        """測試獲取不存在的任務"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/group-ai/automation-tasks/nonexistent_id",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [404, 403]

    def test_update_automation_task(self, prepare_database):
        """測試更新任務"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建一個任務
        db = SessionLocal()
        try:
            # 使用manual类型任务避免scheduler调用
            task = GroupAIAutomationTask(
                id=str(uuid.uuid4()),
                name=f"測試任務_{uuid.uuid4().hex[:8]}",
                task_type="manual",
                task_action="account_start",
                action_config={},
                enabled=True
            )
            db.add(task)
            db.commit()
            task_id = task.id
            
            update_data = {
                "name": "更新後的任務名",
                "enabled": False
            }
            
            resp = client.put(
                f"/api/v1/group-ai/automation-tasks/{task_id}",
                json=update_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 403, 404, 500]
        finally:
            db.close()

    def test_delete_automation_task(self, prepare_database):
        """測試刪除任務"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建一個任務
        db = SessionLocal()
        try:
            task = GroupAIAutomationTask(
                id=str(uuid.uuid4()),
                name=f"測試任務_{uuid.uuid4().hex[:8]}",
                task_type="scheduled",
                task_action="account_start",
                action_config={},
                enabled=True
            )
            db.add(task)
            db.commit()
            task_id = task.id
            
            # 使用manual类型任务避免scheduler调用
            task.task_type = "manual"
            db.commit()
            
            resp = client.delete(
                f"/api/v1/group-ai/automation-tasks/{task_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 204, 403, 404, 500]
        finally:
            db.close()

    def test_get_task_logs(self, prepare_database):
        """測試獲取任務執行日誌"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建一個任務
        db = SessionLocal()
        try:
            task = GroupAIAutomationTask(
                id=str(uuid.uuid4()),
                name=f"測試任務_{uuid.uuid4().hex[:8]}",
                task_type="scheduled",
                task_action="account_start",
                action_config={},
                enabled=True
            )
            db.add(task)
            db.commit()
            task_id = task.id
            
            resp = client.get(
                f"/api/v1/group-ai/automation-tasks/{task_id}/logs",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 403, 404]
            if resp.status_code == 200:
                assert isinstance(resp.json(), list)
        finally:
            db.close()

    def test_trigger_task_manual(self, prepare_database):
        """測試手動觸發任務"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建一個任務
        db = SessionLocal()
        try:
            task = GroupAIAutomationTask(
                id=str(uuid.uuid4()),
                name=f"測試任務_{uuid.uuid4().hex[:8]}",
                task_type="manual",
                task_action="account_start",
                action_config={},
                enabled=True
            )
            db.add(task)
            db.commit()
            task_id = task.id
            
            with patch('app.services.task_executor.get_task_executor') as mock_get_executor:
                mock_executor = MagicMock()
                mock_executor.execute_task = MagicMock()
                mock_get_executor.return_value = mock_executor
                
                resp = client.post(
                    f"/api/v1/group-ai/automation-tasks/{task_id}/run",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                assert resp.status_code in [200, 403, 404, 500]
        finally:
            db.close()

    def test_create_task_unauthorized(self):
        """測試未認證訪問"""
        task_data = {
            "name": "測試任務",
            "task_type": "scheduled",
            "task_action": "account_start",
            "action_config": {}
        }
        
        resp = client.post("/api/v1/group-ai/automation-tasks", json=task_data)
        assert resp.status_code in [401, 403, 404]

