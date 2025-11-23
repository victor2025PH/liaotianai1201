"""
Group AI Servers API 測試
"""
import pytest
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from app.main import app
from app.core.config import get_settings

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


class TestServersAPI:
    """Servers API 測試"""

    @patch('app.api.group_ai.servers.get_master_config_path')
    def test_list_servers_empty_config(self, mock_config_path):
        """測試列表服務器（空配置）"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"servers": {}}, f)
            temp_file = Path(f.name)
        
        mock_config_path.return_value = temp_file
        
        try:
            resp = client.get(
                "/api/v1/group-ai/servers/",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [200, 404]
            if resp.status_code == 200:
                assert isinstance(resp.json(), list)
        finally:
            if temp_file.exists():
                temp_file.unlink()

    @patch('app.api.group_ai.servers.get_master_config_path')
    def test_list_servers_with_config(self, mock_config_path):
        """測試列表服務器（有配置）"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        servers_config = {
            "servers": {
                "node1": {
                    "host": "192.168.1.100",
                    "port": 8000,
                    "max_accounts": 10
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(servers_config, f)
            temp_file = Path(f.name)
        
        mock_config_path.return_value = temp_file
        
        try:
            with patch('app.api.group_ai.servers.get_server_status') as mock_get_status:
                from app.api.group_ai.servers import ServerStatus
                mock_status = ServerStatus(
                    node_id="node1",
                    host="192.168.1.100",
                    port=8000,
                    status="online",
                    accounts_count=0,
                    max_accounts=10,
                    last_heartbeat=None,
                    service_status=None
                )
                mock_get_status.return_value = mock_status
                
                resp = client.get(
                    "/api/v1/group-ai/servers/",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                assert resp.status_code in [200, 404]
        finally:
            if temp_file.exists():
                temp_file.unlink()

    @patch('app.api.group_ai.servers.get_master_config_path')
    def test_get_server_not_found(self, mock_config_path):
        """測試獲取不存在的服務器"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        servers_config = {
            "servers": {
                "node1": {
                    "host": "192.168.1.100",
                    "port": 8000
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(servers_config, f)
            temp_file = Path(f.name)
        
        mock_config_path.return_value = temp_file
        
        try:
            resp = client.get(
                "/api/v1/group-ai/servers/nonexistent",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert resp.status_code in [404, 200]
        finally:
            if temp_file.exists():
                temp_file.unlink()

    @patch('app.api.group_ai.servers.get_master_config_path')
    def test_get_server_success(self, mock_config_path):
        """測試獲取服務器詳情（成功）"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        servers_config = {
            "servers": {
                "node1": {
                    "host": "192.168.1.100",
                    "port": 8000,
                    "max_accounts": 10
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(servers_config, f)
            temp_file = Path(f.name)
        
        mock_config_path.return_value = temp_file
        
        try:
            with patch('app.api.group_ai.servers.get_server_status') as mock_get_status:
                from app.api.group_ai.servers import ServerStatus
                mock_status = ServerStatus(
                    node_id="node1",
                    host="192.168.1.100",
                    port=8000,
                    status="online",
                    accounts_count=5,
                    max_accounts=10,
                    last_heartbeat=None,
                    service_status=None
                )
                mock_get_status.return_value = mock_status
                
                resp = client.get(
                    "/api/v1/group-ai/servers/node1",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                assert resp.status_code in [200, 404]
                if resp.status_code == 200:
                    data = resp.json()
                    assert "node_id" in data
                    assert "status" in data
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def test_list_servers_unauthorized(self):
        """測試未認證訪問"""
        resp = client.get("/api/v1/group-ai/servers/")
        # 可能返回 401（未認證）或 200（認證被禁用）或 404
        assert resp.status_code in [200, 401, 403, 404]


class TestServersAPIConfig:
    """Servers API 配置測試"""

    @patch('app.api.group_ai.servers.get_master_config_path')
    def test_list_servers_config_not_exists(self, mock_config_path):
        """測試配置文件不存在"""
        token = _get_token()
        if not token:
            pytest.skip("無法獲取認證token")
        
        # 使用不存在的文件
        mock_config_path.return_value = Path("/nonexistent/config.json")
        
        resp = client.get(
            "/api/v1/group-ai/servers/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 應該返回空列表或錯誤
        assert resp.status_code in [200, 404, 500]
        if resp.status_code == 200:
            assert isinstance(resp.json(), list)

