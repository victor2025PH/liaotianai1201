"""
審計日誌工具測試
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import Request

from app.utils.audit import get_client_ip, get_user_agent, log_audit
from app.models.user import User


class TestClientIP:
    """客戶端IP獲取測試"""

    def test_get_client_ip_with_client(self):
        """測試獲取客戶端IP（有client）"""
        mock_request = Mock(spec=Request)
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.100"
        
        ip = get_client_ip(mock_request)
        assert ip == "192.168.1.100"

    def test_get_client_ip_no_client(self):
        """測試獲取客戶端IP（無client）"""
        mock_request = Mock(spec=Request)
        mock_request.client = None
        
        ip = get_client_ip(mock_request)
        assert ip is None


class TestUserAgent:
    """用戶代理獲取測試"""

    def test_get_user_agent_exists(self):
        """測試獲取用戶代理（存在）"""
        mock_request = Mock(spec=Request)
        mock_request.headers = {"user-agent": "Mozilla/5.0"}
        
        ua = get_user_agent(mock_request)
        assert ua == "Mozilla/5.0"

    def test_get_user_agent_not_exists(self):
        """測試獲取用戶代理（不存在）"""
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        
        ua = get_user_agent(mock_request)
        assert ua is None


class TestLogAudit:
    """審計日誌記錄測試"""

    @patch('app.utils.audit.create_audit_log')
    def test_log_audit_basic(self, mock_create_audit_log):
        """測試基本審計日誌記錄"""
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test@example.com"
        
        log_audit(
            db=mock_db,
            user=mock_user,
            action="CREATE",
            resource_type="user"
        )
        
        mock_create_audit_log.assert_called_once()
        call_kwargs = mock_create_audit_log.call_args[1]
        assert call_kwargs["user_id"] == 1
        assert call_kwargs["user_email"] == "test@example.com"
        assert call_kwargs["action"] == "CREATE"
        assert call_kwargs["resource_type"] == "user"

    @patch('app.utils.audit.create_audit_log')
    def test_log_audit_with_resource_id(self, mock_create_audit_log):
        """測試帶資源ID的審計日誌"""
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test@example.com"
        
        log_audit(
            db=mock_db,
            user=mock_user,
            action="UPDATE",
            resource_type="user",
            resource_id="123"
        )
        
        call_kwargs = mock_create_audit_log.call_args[1]
        assert call_kwargs["resource_id"] == "123"

    @patch('app.utils.audit.create_audit_log')
    def test_log_audit_with_description(self, mock_create_audit_log):
        """測試帶描述的審計日誌"""
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test@example.com"
        
        log_audit(
            db=mock_db,
            user=mock_user,
            action="DELETE",
            resource_type="user",
            description="刪除用戶"
        )
        
        call_kwargs = mock_create_audit_log.call_args[1]
        assert call_kwargs["description"] == "刪除用戶"

    @patch('app.utils.audit.create_audit_log')
    def test_log_audit_with_states(self, mock_create_audit_log):
        """測試帶狀態變化的審計日誌"""
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test@example.com"
        
        before_state = {"status": "active"}
        after_state = {"status": "inactive"}
        
        log_audit(
            db=mock_db,
            user=mock_user,
            action="UPDATE",
            resource_type="user",
            before_state=before_state,
            after_state=after_state
        )
        
        call_kwargs = mock_create_audit_log.call_args[1]
        assert call_kwargs["before_state"] == before_state
        assert call_kwargs["after_state"] == after_state

    @patch('app.utils.audit.create_audit_log')
    @patch('app.utils.audit.get_client_ip')
    @patch('app.utils.audit.get_user_agent')
    def test_log_audit_with_request(self, mock_get_ua, mock_get_ip, mock_create_audit_log):
        """測試帶請求信息的審計日誌"""
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test@example.com"
        
        mock_request = Mock(spec=Request)
        mock_get_ip.return_value = "192.168.1.100"
        mock_get_ua.return_value = "Mozilla/5.0"
        
        log_audit(
            db=mock_db,
            user=mock_user,
            action="CREATE",
            resource_type="user",
            request=mock_request
        )
        
        call_kwargs = mock_create_audit_log.call_args[1]
        assert call_kwargs["ip_address"] == "192.168.1.100"
        assert call_kwargs["user_agent"] == "Mozilla/5.0"

    @patch('app.utils.audit.create_audit_log')
    def test_log_audit_without_request(self, mock_create_audit_log):
        """測試無請求信息的審計日誌"""
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test@example.com"
        
        log_audit(
            db=mock_db,
            user=mock_user,
            action="CREATE",
            resource_type="user",
            request=None
        )
        
        call_kwargs = mock_create_audit_log.call_args[1]
        assert call_kwargs.get("ip_address") is None
        assert call_kwargs.get("user_agent") is None

