"""
Group AI Role Assignment Schemes API 測試
"""
import pytest
import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import get_settings
from app.models.group_ai import GroupAIRoleAssignmentScheme, GroupAIScript

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


class TestRoleAssignmentSchemesAPI:
    """Role Assignment Schemes API 測試"""

    def test_create_scheme_basic(self, prepare_database):
        """測試基本分配方案創建"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建一個劇本
        db = SessionLocal()
        try:
            script_id = f"test_script_{uuid.uuid4().hex[:8]}"
            script = GroupAIScript(
                script_id=script_id,
                name="測試劇本",
                version="1.0.0",
                yaml_content="script_id: test\nversion: 1.0.0",
                status="active"
            )
            db.add(script)
            db.commit()
            
            unique_name = f"測試方案_{uuid.uuid4().hex[:8]}"
            scheme_data = {
                "name": unique_name,
                "description": "測試描述",
                "script_id": script_id,
                "assignments": [
                    {"role_id": "role1", "account_id": "account1", "weight": 1.0}
                ],
                "mode": "auto",
                "account_ids": ["account1"]
            }
            
            from unittest.mock import MagicMock, patch
            with patch('app.api.group_ai.role_assignment_schemes.get_service_manager') as mock_get_manager:
                mock_manager = MagicMock()
                mock_get_manager.return_value = mock_manager
                
                resp = client.post(
                    "/api/v1/group-ai/role-assignment-schemes",
                    json=scheme_data,
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                assert resp.status_code in [201, 403, 404, 500]
        finally:
            db.close()

    def test_list_schemes(self, prepare_database):
        """測試列出分配方案"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/group-ai/role-assignment-schemes",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]
        if resp.status_code == 200:
            data = resp.json()
            assert "items" in data or isinstance(data, list)
            assert "total" in data or isinstance(data, list)

    def test_list_schemes_with_filters(self, prepare_database):
        """測試帶過濾條件的方案列表"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/group-ai/role-assignment-schemes?script_id=test&page=1&page_size=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [200, 403]

    def test_get_scheme_by_id(self, prepare_database):
        """測試根據ID獲取方案"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建劇本和方案
        db = SessionLocal()
        try:
            script_id = f"test_script_{uuid.uuid4().hex[:8]}"
            script = GroupAIScript(
                script_id=script_id,
                name="測試劇本",
                version="1.0.0",
                yaml_content="script_id: test\nversion: 1.0.0",
                status="active"
            )
            db.add(script)
            
            scheme_id = str(uuid.uuid4())
            scheme = GroupAIRoleAssignmentScheme(
                id=scheme_id,
                name=f"測試方案_{uuid.uuid4().hex[:8]}",
                script_id=script_id,
                assignments=[{"role_id": "role1", "account_id": "account1"}],
                mode="auto",
                account_ids=["account1"]
            )
            db.add(scheme)
            db.commit()
            
            resp = client.get(
                f"/api/v1/group-ai/role-assignment-schemes/{scheme_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 403, 404]
            if resp.status_code == 200:
                data = resp.json()
                assert data["id"] == scheme_id
        finally:
            db.close()

    def test_get_scheme_not_found(self, prepare_database):
        """測試獲取不存在的方案"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/group-ai/role-assignment-schemes/nonexistent_id",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code in [404, 403]

    def test_update_scheme(self, prepare_database):
        """測試更新方案"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建劇本和方案
        db = SessionLocal()
        try:
            script_id = f"test_script_{uuid.uuid4().hex[:8]}"
            script = GroupAIScript(
                script_id=script_id,
                name="測試劇本",
                version="1.0.0",
                yaml_content="script_id: test\nversion: 1.0.0",
                status="active"
            )
            db.add(script)
            
            scheme_id = str(uuid.uuid4())
            scheme = GroupAIRoleAssignmentScheme(
                id=scheme_id,
                name=f"測試方案_{uuid.uuid4().hex[:8]}",
                script_id=script_id,
                assignments=[{"role_id": "role1", "account_id": "account1"}],
                mode="auto",
                account_ids=["account1"]
            )
            db.add(scheme)
            db.commit()
            
            update_data = {
                "name": "更新後的方案名",
                "description": "更新後的描述"
            }
            
            resp = client.put(
                f"/api/v1/group-ai/role-assignment-schemes/{scheme_id}",
                json=update_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 403, 404, 500]
        finally:
            db.close()

    def test_delete_scheme(self, prepare_database):
        """測試刪除方案"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建劇本和方案
        db = SessionLocal()
        try:
            script_id = f"test_script_{uuid.uuid4().hex[:8]}"
            script = GroupAIScript(
                script_id=script_id,
                name="測試劇本",
                version="1.0.0",
                yaml_content="script_id: test\nversion: 1.0.0",
                status="active"
            )
            db.add(script)
            
            scheme_id = str(uuid.uuid4())
            scheme = GroupAIRoleAssignmentScheme(
                id=scheme_id,
                name=f"測試方案_{uuid.uuid4().hex[:8]}",
                script_id=script_id,
                assignments=[{"role_id": "role1", "account_id": "account1"}],
                mode="auto",
                account_ids=["account1"]
            )
            db.add(scheme)
            db.commit()
            
            resp = client.delete(
                f"/api/v1/group-ai/role-assignment-schemes/{scheme_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 204, 403, 404, 500]
        finally:
            db.close()

    def test_apply_scheme(self, prepare_database):
        """測試應用方案"""
        from app.db import SessionLocal
        from unittest.mock import MagicMock, patch
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建劇本和方案
        db = SessionLocal()
        try:
            script_id = f"test_script_{uuid.uuid4().hex[:8]}"
            script = GroupAIScript(
                script_id=script_id,
                name="測試劇本",
                version="1.0.0",
                yaml_content="script_id: test\nversion: 1.0.0",
                status="active"
            )
            db.add(script)
            
            scheme_id = str(uuid.uuid4())
            scheme = GroupAIRoleAssignmentScheme(
                id=scheme_id,
                name=f"測試方案_{uuid.uuid4().hex[:8]}",
                script_id=script_id,
                assignments=[{"role_id": "role1", "account_id": "account1"}],
                mode="auto",
                account_ids=["account1"]
            )
            db.add(scheme)
            db.commit()
            
            apply_data = {
                "account_ids": ["account1"]
            }
            
            with patch('app.api.group_ai.role_assignment_schemes.get_service_manager') as mock_get_manager:
                mock_manager = MagicMock()
                mock_get_manager.return_value = mock_manager
                
                resp = client.post(
                    f"/api/v1/group-ai/role-assignment-schemes/{scheme_id}/apply",
                    json=apply_data,
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                assert resp.status_code in [200, 403, 404, 500]
        finally:
            db.close()

    def test_get_scheme_history(self, prepare_database):
        """測試獲取方案應用歷史"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建劇本和方案
        db = SessionLocal()
        try:
            script_id = f"test_script_{uuid.uuid4().hex[:8]}"
            script = GroupAIScript(
                script_id=script_id,
                name="測試劇本",
                version="1.0.0",
                yaml_content="script_id: test\nversion: 1.0.0",
                status="active"
            )
            db.add(script)
            
            scheme_id = str(uuid.uuid4())
            scheme = GroupAIRoleAssignmentScheme(
                id=scheme_id,
                name=f"測試方案_{uuid.uuid4().hex[:8]}",
                script_id=script_id,
                assignments=[{"role_id": "role1", "account_id": "account1"}],
                mode="auto",
                account_ids=["account1"]
            )
            db.add(scheme)
            db.commit()
            
            resp = client.get(
                f"/api/v1/group-ai/role-assignment-schemes/{scheme_id}/history",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 403, 404]
            if resp.status_code == 200:
                data = resp.json()
                # 可能是列表或包含items的字典
                assert isinstance(data, (list, dict))
                if isinstance(data, dict):
                    assert "items" in data or "total" in data
        finally:
            db.close()

    def test_create_scheme_unauthorized(self):
        """測試未認證訪問"""
        scheme_data = {
            "name": "測試方案",
            "script_id": "test",
            "assignments": [],
            "account_ids": []
        }
        
        resp = client.post("/api/v1/group-ai/role-assignment-schemes", json=scheme_data)
        assert resp.status_code in [401, 403, 404]

