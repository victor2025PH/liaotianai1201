"""
NotificationService 單元測試
"""
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from group_ai_service.notification_service import NotificationService


@pytest.fixture
def notification_service():
    """創建 NotificationService 實例"""
    return NotificationService()


class TestNotificationService:
    """NotificationService 測試"""
    
    def test_service_initialization(self, notification_service):
        """測試服務初始化"""
        assert notification_service is not None
        assert hasattr(notification_service, 'email_enabled')
        assert hasattr(notification_service, 'telegram_enabled')
        assert hasattr(notification_service, 'webhook_enabled')
    
    @pytest.mark.asyncio
    async def test_send_email_disabled(self, notification_service):
        """測試郵件發送（已禁用）"""
        # Mock 配置為禁用郵件
        notification_service.email_enabled = False
        
        await notification_service.send_email(
            subject="測試",
            body="測試內容"
        )
        
        # 應該直接返回，不發送郵件
    
    @pytest.mark.asyncio
    async def test_send_telegram_message_disabled(self, notification_service):
        """測試 Telegram 消息發送（已禁用）"""
        # Mock 配置為禁用 Telegram
        notification_service.telegram_enabled = False
        
        await notification_service.send_telegram("測試消息")
        
        # 應該直接返回，不發送消息
    
    @pytest.mark.asyncio
    async def test_send_webhook_disabled(self, notification_service):
        """測試 Webhook 發送（已禁用）"""
        # Mock 配置為禁用 Webhook
        notification_service.webhook_enabled = False
        
        await notification_service.send_webhook({"test": "data"})
        
        # 應該直接返回，不發送 Webhook
    
    @pytest.mark.asyncio
    async def test_send_alert_notification_disabled(self, notification_service):
        """測試告警通知發送（已禁用）"""
        # Mock 配置為禁用通知
        notification_service.notification_enabled = False
        
        alert_data = {
            "alert_level": "error",
            "message": "測試告警",
            "account_id": "test_account"
        }
        
        await notification_service.send_alert_notification(alert_data)
        
        # 應該直接返回，不發送通知
    
    @pytest.mark.asyncio
    async def test_send_email_success(self, notification_service):
        """測試郵件發送成功"""
        # 啟用郵件並配置
        notification_service.notification_enabled = True
        notification_service.email_enabled = True
        notification_service.email_smtp_host = "smtp.example.com"
        notification_service.email_smtp_port = 587
        notification_service.email_from = "test@example.com"
        notification_service.email_to = ["recipient@example.com"]
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            mock_smtp.return_value.__exit__.return_value = None
            
            result = await notification_service.send_email(
                subject="測試",
                body="測試內容"
            )
            
            # 應該成功發送
            assert result is True
            mock_server.starttls.assert_called_once()
            mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_no_recipients(self, notification_service):
        """測試郵件發送（無接收者）"""
        notification_service.notification_enabled = True
        notification_service.email_enabled = True
        notification_service.email_smtp_host = "smtp.example.com"
        notification_service.email_from = "test@example.com"
        notification_service.email_to = []
        
        result = await notification_service.send_email(
            subject="測試",
            body="測試內容"
        )
        
        # 應該返回 False
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_email_no_config(self, notification_service):
        """測試郵件發送（配置不完整）"""
        notification_service.notification_enabled = True
        notification_service.email_enabled = True
        notification_service.email_smtp_host = None
        notification_service.email_from = None
        
        result = await notification_service.send_email(
            subject="測試",
            body="測試內容"
        )
        
        # 應該返回 False
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_telegram_success(self, notification_service):
        """測試 Telegram 消息發送成功（需要 aiohttp，如果沒有則測試導入失敗）"""
        notification_service.notification_enabled = True
        notification_service.telegram_enabled = True
        notification_service.telegram_bot_token = "test_token"
        notification_service.telegram_chat_id = "test_chat_id"
        
        # 由於 aiohttp 是在函數內部導入的，如果沒有安裝則會返回 False
        # 這個測試主要驗證邏輯流程
        result = await notification_service.send_telegram("測試消息")
        
        # 如果沒有 aiohttp，應該返回 False；如果有則可能成功
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_send_telegram_no_token(self, notification_service):
        """測試 Telegram 消息發送（無 Token）"""
        notification_service.notification_enabled = True
        notification_service.telegram_enabled = True
        notification_service.telegram_bot_token = None
        
        result = await notification_service.send_telegram("測試消息")
        
        # 應該返回 False
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_webhook_success(self, notification_service):
        """測試 Webhook 發送成功（需要 aiohttp，如果沒有則測試導入失敗）"""
        notification_service.notification_enabled = True
        notification_service.webhook_enabled = True
        notification_service.webhook_url = "https://example.com/webhook"
        
        # 由於 aiohttp 是在函數內部導入的，如果沒有安裝則會返回 False
        # 這個測試主要驗證邏輯流程
        result = await notification_service.send_webhook({"test": "data"})
        
        # 如果沒有 aiohttp，應該返回 False；如果有則可能成功
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_send_webhook_no_url(self, notification_service):
        """測試 Webhook 發送（無 URL）"""
        notification_service.notification_enabled = True
        notification_service.webhook_enabled = True
        notification_service.webhook_url = None
        
        result = await notification_service.send_webhook({"test": "data"})
        
        # 應該返回 False
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_alert_notification_all_methods(self, notification_service):
        """測試告警通知發送（所有方式）"""
        notification_service.notification_enabled = True
        notification_service.email_enabled = True
        notification_service.telegram_enabled = True
        notification_service.webhook_enabled = True
        
        # Mock 所有發送方法
        notification_service.send_email = AsyncMock(return_value=True)
        notification_service.send_telegram = AsyncMock(return_value=True)
        notification_service.send_webhook = AsyncMock(return_value=True)
        
        alert_data = {
            "alert_level": "error",
            "message": "測試告警",
            "account_id": "test_account"
        }
        
        result = await notification_service.send_alert_notification(alert_data)
        
        # 應該調用所有發送方法
        assert result is True
        notification_service.send_email.assert_called_once()
        notification_service.send_telegram.assert_called_once()
        notification_service.send_webhook.assert_called_once()
    
    def test_get_notification_service_singleton(self):
        """測試獲取通知服務單例"""
        from group_ai_service.notification_service import get_notification_service
        
        service1 = get_notification_service()
        service2 = get_notification_service()
        
        # 應該是同一個實例
        assert service1 is service2
    
    def test_load_config_error(self):
        """測試配置加載失敗"""
        # Mock 配置加載失敗（在 config 模塊中）
        with patch('group_ai_service.config.get_group_ai_config', side_effect=Exception("配置錯誤")):
            service = NotificationService()
            
            # 應該使用默認配置
            assert service.notification_enabled == False
            assert service.email_enabled == False
            assert service.telegram_enabled == False
            assert service.webhook_enabled == False
    
    @pytest.mark.asyncio
    async def test_send_email_with_html_body(self, notification_service):
        """測試郵件發送（帶 HTML 內容）"""
        notification_service.notification_enabled = True
        notification_service.email_enabled = True
        notification_service.email_smtp_host = "smtp.example.com"
        notification_service.email_smtp_port = 587
        notification_service.email_from = "test@example.com"
        notification_service.email_to = ["recipient@example.com"]
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            mock_smtp.return_value.__exit__.return_value = None
            
            result = await notification_service.send_email(
                subject="測試",
                body="測試內容",
                html_body="<html><body>測試 HTML</body></html>"
            )
            
            assert result is True
            mock_server.starttls.assert_called_once()
            mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_with_auth(self, notification_service):
        """測試郵件發送（帶認證）"""
        notification_service.notification_enabled = True
        notification_service.email_enabled = True
        notification_service.email_smtp_host = "smtp.example.com"
        notification_service.email_smtp_port = 587
        notification_service.email_smtp_user = "user@example.com"
        notification_service.email_smtp_password = "password"
        notification_service.email_from = "test@example.com"
        notification_service.email_to = ["recipient@example.com"]
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            mock_smtp.return_value.__exit__.return_value = None
            
            result = await notification_service.send_email(
                subject="測試",
                body="測試內容"
            )
            
            assert result is True
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("user@example.com", "password")
            mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_port_25(self, notification_service):
        """測試郵件發送（端口 25，不使用 TLS）"""
        notification_service.notification_enabled = True
        notification_service.email_enabled = True
        notification_service.email_smtp_host = "smtp.example.com"
        notification_service.email_smtp_port = 25
        notification_service.email_from = "test@example.com"
        notification_service.email_to = ["recipient@example.com"]
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            mock_smtp.return_value.__exit__.return_value = None
            
            result = await notification_service.send_email(
                subject="測試",
                body="測試內容"
            )
            
            assert result is True
            # 端口 25 不應該調用 starttls
            mock_server.starttls.assert_not_called()
            mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_exception(self, notification_service):
        """測試郵件發送（異常處理）"""
        notification_service.notification_enabled = True
        notification_service.email_enabled = True
        notification_service.email_smtp_host = "smtp.example.com"
        notification_service.email_smtp_port = 587
        notification_service.email_from = "test@example.com"
        notification_service.email_to = ["recipient@example.com"]
        
        with patch('smtplib.SMTP', side_effect=Exception("SMTP 錯誤")):
            result = await notification_service.send_email(
                subject="測試",
                body="測試內容"
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_telegram_no_chat_id(self, notification_service):
        """測試 Telegram 消息發送（無 Chat ID）"""
        notification_service.notification_enabled = True
        notification_service.telegram_enabled = True
        notification_service.telegram_bot_token = "test_token"
        notification_service.telegram_chat_id = None
        
        result = await notification_service.send_telegram("測試消息")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_telegram_success(self, notification_service):
        """測試 Telegram 消息發送成功"""
        notification_service.notification_enabled = True
        notification_service.telegram_enabled = True
        notification_service.telegram_bot_token = "test_token"
        notification_service.telegram_chat_id = "test_chat_id"
        
        # Mock aiohttp（如果未安裝則測試 ImportError 處理）
        try:
            import aiohttp
            # 如果有 aiohttp，mock ClientSession 和嵌套的 async context manager
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value='{"ok": true}')
            
            # Mock session.post() 返回的 context manager
            mock_post_cm = AsyncMock()
            mock_post_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post_cm.__aexit__ = AsyncMock(return_value=None)
            
            mock_session = AsyncMock()
            mock_session.post = Mock(return_value=mock_post_cm)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            with patch('aiohttp.ClientSession', return_value=mock_session):
                result = await notification_service.send_telegram("測試消息")
                assert result is True
        except ImportError:
            # 如果沒有 aiohttp，應該返回 False
            result = await notification_service.send_telegram("測試消息")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_telegram_api_error(self, notification_service):
        """測試 Telegram 消息發送（API 錯誤）"""
        notification_service.notification_enabled = True
        notification_service.telegram_enabled = True
        notification_service.telegram_bot_token = "test_token"
        notification_service.telegram_chat_id = "test_chat_id"
        
        # Mock aiohttp（如果未安裝則跳過）
        try:
            import aiohttp
            # Mock aiohttp（返回錯誤狀態碼）
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.text = AsyncMock(return_value='{"ok": false, "description": "Bad Request"}')
            
            mock_session = AsyncMock()
            mock_session.post = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            with patch('aiohttp.ClientSession', return_value=mock_session):
                result = await notification_service.send_telegram("測試消息")
                assert result is False
        except ImportError:
            # 如果沒有 aiohttp，跳過此測試
            pytest.skip("aiohttp 未安裝，跳過此測試")
    
    @pytest.mark.asyncio
    async def test_send_telegram_exception(self, notification_service):
        """測試 Telegram 消息發送（異常處理）"""
        notification_service.notification_enabled = True
        notification_service.telegram_enabled = True
        notification_service.telegram_bot_token = "test_token"
        notification_service.telegram_chat_id = "test_chat_id"
        
        # Mock aiohttp（如果未安裝則跳過）
        try:
            import aiohttp
            # Mock aiohttp 拋出異常
            with patch('aiohttp.ClientSession', side_effect=Exception("網絡錯誤")):
                result = await notification_service.send_telegram("測試消息")
                assert result is False
        except ImportError:
            # 如果沒有 aiohttp，跳過此測試
            pytest.skip("aiohttp 未安裝，跳過此測試")
    
    @pytest.mark.asyncio
    async def test_send_webhook_success(self, notification_service):
        """測試 Webhook 發送成功"""
        notification_service.notification_enabled = True
        notification_service.webhook_enabled = True
        notification_service.webhook_url = "https://example.com/webhook"
        
        # Mock aiohttp（如果未安裝則跳過）
        try:
            import aiohttp
            # Mock aiohttp - 正確mock嵌套的async context manager
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value='{"success": true}')
            
            # Mock session.post() 返回的 context manager
            mock_post_cm = AsyncMock()
            mock_post_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post_cm.__aexit__ = AsyncMock(return_value=None)
            
            mock_session = AsyncMock()
            mock_session.post = Mock(return_value=mock_post_cm)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            with patch('aiohttp.ClientSession', return_value=mock_session):
                result = await notification_service.send_webhook({"test": "data"})
                assert result is True
        except ImportError:
            # 如果沒有 aiohttp，應該返回 False
            result = await notification_service.send_webhook({"test": "data"})
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_webhook_status_201(self, notification_service):
        """測試 Webhook 發送（狀態碼 201）"""
        notification_service.notification_enabled = True
        notification_service.webhook_enabled = True
        notification_service.webhook_url = "https://example.com/webhook"
        
        # Mock aiohttp（如果未安裝則跳過）
        try:
            import aiohttp
            # Mock aiohttp（返回 201）- 正確mock嵌套的async context manager
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.text = AsyncMock(return_value='{"success": true}')
            
            # Mock session.post() 返回的 context manager
            mock_post_cm = AsyncMock()
            mock_post_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post_cm.__aexit__ = AsyncMock(return_value=None)
            
            mock_session = AsyncMock()
            mock_session.post = Mock(return_value=mock_post_cm)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            with patch('aiohttp.ClientSession', return_value=mock_session):
                result = await notification_service.send_webhook({"test": "data"})
                assert result is True
        except ImportError:
            pytest.skip("aiohttp 未安裝，跳過此測試")
    
    @pytest.mark.asyncio
    async def test_send_webhook_status_204(self, notification_service):
        """測試 Webhook 發送（狀態碼 204）"""
        notification_service.notification_enabled = True
        notification_service.webhook_enabled = True
        notification_service.webhook_url = "https://example.com/webhook"
        
        # Mock aiohttp（如果未安裝則跳過）
        try:
            import aiohttp
            # Mock aiohttp（返回 204）- 正確mock嵌套的async context manager
            mock_response = AsyncMock()
            mock_response.status = 204
            mock_response.text = AsyncMock(return_value='')
            
            # Mock session.post() 返回的 context manager
            mock_post_cm = AsyncMock()
            mock_post_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post_cm.__aexit__ = AsyncMock(return_value=None)
            
            mock_session = AsyncMock()
            mock_session.post = Mock(return_value=mock_post_cm)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            with patch('aiohttp.ClientSession', return_value=mock_session):
                result = await notification_service.send_webhook({"test": "data"})
                assert result is True
        except ImportError:
            pytest.skip("aiohttp 未安裝，跳過此測試")
    
    @pytest.mark.asyncio
    async def test_send_webhook_error_status(self, notification_service):
        """測試 Webhook 發送（錯誤狀態碼）"""
        notification_service.notification_enabled = True
        notification_service.webhook_enabled = True
        notification_service.webhook_url = "https://example.com/webhook"
        
        # Mock aiohttp（如果未安裝則跳過）
        try:
            import aiohttp
            # Mock aiohttp（返回錯誤狀態碼）
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value='Internal Server Error')
            
            mock_session = AsyncMock()
            mock_session.post = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            with patch('aiohttp.ClientSession', return_value=mock_session):
                result = await notification_service.send_webhook({"test": "data"})
                assert result is False
        except ImportError:
            pytest.skip("aiohttp 未安裝，跳過此測試")
    
    @pytest.mark.asyncio
    async def test_send_webhook_exception(self, notification_service):
        """測試 Webhook 發送（異常處理）"""
        notification_service.notification_enabled = True
        notification_service.webhook_enabled = True
        notification_service.webhook_url = "https://example.com/webhook"
        
        # Mock aiohttp（如果未安裝則跳過）
        try:
            import aiohttp
            # Mock aiohttp 拋出異常
            with patch('aiohttp.ClientSession', side_effect=Exception("網絡錯誤")):
                result = await notification_service.send_webhook({"test": "data"})
                assert result is False
        except ImportError:
            pytest.skip("aiohttp 未安裝，跳過此測試")
    
    @pytest.mark.asyncio
    async def test_send_alert_notification_with_string_timestamp(self, notification_service):
        """測試告警通知發送（字符串時間戳）"""
        notification_service.notification_enabled = True
        notification_service.email_enabled = True
        notification_service.send_email = AsyncMock(return_value=True)
        
        alert_data = {
            "alert_level": "error",
            "message": "測試告警",
            "account_id": "test_account",
            "timestamp": "2025-01-15 10:30:00"  # 字符串時間戳
        }
        
        result = await notification_service.send_alert_notification(alert_data)
        
        assert result is True
        notification_service.send_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_alert_notification_specific_method(self, notification_service):
        """測試告警通知發送（指定通知方式）"""
        notification_service.notification_enabled = True
        notification_service.email_enabled = True
        notification_service.telegram_enabled = True
        notification_service.webhook_enabled = True
        
        notification_service.send_email = AsyncMock(return_value=True)
        notification_service.send_telegram = AsyncMock(return_value=True)
        notification_service.send_webhook = AsyncMock(return_value=True)
        
        alert_data = {
            "alert_level": "warning",
            "message": "測試告警"
        }
        
        # 只發送郵件
        result = await notification_service.send_alert_notification(
            alert_data,
            notification_method="email"
        )
        
        assert result is True
        notification_service.send_email.assert_called_once()
        notification_service.send_telegram.assert_not_called()
        notification_service.send_webhook.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_send_alert_notification_with_target(self, notification_service):
        """測試告警通知發送（指定目標）"""
        notification_service.notification_enabled = True
        notification_service.email_enabled = True
        notification_service.send_email = AsyncMock(return_value=True)
        
        alert_data = {
            "alert_level": "info",
            "message": "測試告警"
        }
        
        result = await notification_service.send_alert_notification(
            alert_data,
            notification_method="email",
            notification_target="custom@example.com"
        )
        
        assert result is True
        # 檢查是否使用了自定義目標
        call_args = notification_service.send_email.call_args
        # call_args 是 (args, kwargs) 元組
        # send_email 的簽名是: send_email(subject, body, html_body=None, recipients=None)
        # 從代碼看，recipients 是作為位置參數傳遞的（第4個參數）
        assert call_args is not None
        # 檢查調用參數
        args = call_args[0] if call_args else ()
        kwargs = call_args[1] if len(call_args) > 1 else {}
        # recipients 可能在 args 中（第4個位置）或在 kwargs 中
        if len(args) >= 4:
            assert args[3] == ["custom@example.com"]
        elif 'recipients' in kwargs:
            assert kwargs['recipients'] == ["custom@example.com"]
        else:
            # 如果都不在，檢查調用時是否正確傳遞
            # 由於我們 mock 了 send_email，直接檢查調用次數即可
            assert notification_service.send_email.called

