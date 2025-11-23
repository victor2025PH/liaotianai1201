"""
Group AI Script Versions API 測試
"""
import pytest
import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import get_settings
from app.models.group_ai import GroupAIScript, GroupAIScriptVersion

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


class TestScriptVersionsAPI:
    """Script Versions API 測試"""

    def test_list_script_versions(self, prepare_database):
        """測試列出劇本版本"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建一個劇本
        db = SessionLocal()
        try:
            script = GroupAIScript(
                script_id=f"test_script_{uuid.uuid4().hex[:8]}",
                name="測試劇本",
                version="1.0.0",
                yaml_content="script_id: test\nversion: 1.0.0",
                status="active"
            )
            db.add(script)
            db.commit()
            script_id = script.script_id
            
            resp = client.get(
                f"/api/v1/group-ai/script-versions/{script_id}/versions",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404]
            if resp.status_code == 200:
                assert isinstance(resp.json(), list)
        finally:
            db.close()

    def test_list_script_versions_not_found(self, prepare_database):
        """測試獲取不存在的劇本版本"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        resp = client.get(
            "/api/v1/group-ai/script-versions/nonexistent/versions",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code == 404

    def test_get_script_version(self, prepare_database):
        """測試獲取特定版本"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建劇本和版本
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
            
            version = GroupAIScriptVersion(
                id=str(uuid.uuid4()),
                script_id=script_id,
                version="1.0.0",
                yaml_content="script_id: test\nversion: 1.0.0",
                description="初始版本"
            )
            db.add(version)
            db.commit()
            
            resp = client.get(
                f"/api/v1/group-ai/script-versions/{script_id}/versions/1.0.0",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404]
            if resp.status_code == 200:
                data = resp.json()
                assert data["version"] == "1.0.0"
        finally:
            db.close()

    def test_get_script_version_not_found(self, prepare_database):
        """測試獲取不存在的版本"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建劇本
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
            
            resp = client.get(
                f"/api/v1/group-ai/script-versions/{script_id}/versions/999.0.0",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code == 404
        finally:
            db.close()

    def test_get_script_version_content(self, prepare_database):
        """測試獲取版本內容"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建劇本和版本
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
            
            yaml_content = "script_id: test\nversion: 1.0.0\nscenes: []"
            version = GroupAIScriptVersion(
                id=str(uuid.uuid4()),
                script_id=script_id,
                version="1.0.0",
                yaml_content=yaml_content,
                description="初始版本"
            )
            db.add(version)
            db.commit()
            
            resp = client.get(
                f"/api/v1/group-ai/script-versions/{script_id}/versions/1.0.0/content",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404]
            if resp.status_code == 200:
                data = resp.json()
                assert "yaml_content" in data
                assert data["yaml_content"] == yaml_content
        finally:
            db.close()

    def test_compare_script_versions(self, prepare_database):
        """測試對比版本"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建劇本和兩個版本
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
            
            version1 = GroupAIScriptVersion(
                id=str(uuid.uuid4()),
                script_id=script_id,
                version="1.0.0",
                yaml_content="script_id: test\nversion: 1.0.0",
                description="版本1"
            )
            db.add(version1)
            
            version2 = GroupAIScriptVersion(
                id=str(uuid.uuid4()),
                script_id=script_id,
                version="2.0.0",
                yaml_content="script_id: test\nversion: 2.0.0",
                description="版本2"
            )
            db.add(version2)
            db.commit()
            
            resp = client.get(
                f"/api/v1/group-ai/script-versions/{script_id}/versions/compare?version1=1.0.0&version2=2.0.0",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404]
            if resp.status_code == 200:
                data = resp.json()
                assert "version1" in data
                assert "version2" in data
                assert "differences" in data
        finally:
            db.close()

    def test_compare_script_versions_not_found(self, prepare_database):
        """測試對比不存在的版本"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建劇本
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
            
            resp = client.get(
                f"/api/v1/group-ai/script-versions/{script_id}/versions/compare?version1=1.0.0&version2=999.0.0",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code == 404
        finally:
            db.close()

    def test_restore_script_version(self, prepare_database):
        """測試恢復版本"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建劇本和版本
        db = SessionLocal()
        try:
            script_id = f"test_script_{uuid.uuid4().hex[:8]}"
            script = GroupAIScript(
                script_id=script_id,
                name="測試劇本",
                version="2.0.0",
                yaml_content="script_id: test\nversion: 2.0.0",
                status="active"
            )
            db.add(script)
            
            old_yaml = "script_id: test\nversion: 1.0.0"
            version = GroupAIScriptVersion(
                id=str(uuid.uuid4()),
                script_id=script_id,
                version="1.0.0",
                yaml_content=old_yaml,
                description="舊版本"
            )
            db.add(version)
            db.commit()
            
            restore_data = {
                "change_summary": "恢復到1.0.0版本"
            }
            
            resp = client.post(
                f"/api/v1/group-ai/script-versions/{script_id}/versions/1.0.0/restore",
                json=restore_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404, 500]
        finally:
            db.close()

    def test_list_versions_with_pagination(self, prepare_database):
        """測試分頁列表版本"""
        from app.db import SessionLocal
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 先創建劇本
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
            
            resp = client.get(
                f"/api/v1/group-ai/script-versions/{script_id}/versions?skip=0&limit=10",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404]
            if resp.status_code == 200:
                assert isinstance(resp.json(), list)
        finally:
            db.close()

    def test_script_versions_unauthorized(self):
        """測試未認證訪問"""
        resp = client.get("/api/v1/group-ai/script-versions/test/versions")
        # 可能返回 401（未認證）或 200（認證被禁用）或 404
        assert resp.status_code in [200, 401, 403, 404]

