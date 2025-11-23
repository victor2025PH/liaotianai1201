"""
通知服務測試
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import smtplib


class TestNotificationService:
    """通知服務測試"""
    
    @pytest.fixture
    def mock_settings_disabled(self, monkeypatch):
        """Mock 設置（全部禁用）"""
        mock_config = MagicMock()
        mock_config.email_enabled = False
        mock_config.webhook_enabled = False
        mock_config.telegram_bot_token = None
        
        def get_settings():
            return mock_config
        
        monkeypatch.setattr('app.services.notification.get_settings', get_settings)
        return mock_config
    
    @pytest.fixture
    def notification_service(self, mock_settings_disabled):
        """創建通知服務實例（禁用狀態）"""
        from app.services.notification import NotificationService
        service = NotificationService()
        # 確保設置正確
        service.email_enabled = False
        service.webhook_enabled = False
        service.telegram_enabled = False
        return service
    
    @pytest.mark.asyncio
    async def test_send_email_disabled(self, notification_service):
        """測試郵件通知未啟用"""
        result = await notification_service.send_email(
            recipients=["test@example.com"],
            subject="Test",
            body="Test body"
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_email_enabled_but_no_config(self, monkeypatch):
        """測試郵件啟用但配置不完整"""
        mock_config = MagicMock()
        mock_config.email_enabled = True
        mock_config.smtp_host = "smtp.example.com"
        mock_config.smtp_port = 587
        mock_config.smtp_user = ""
        mock_config.smtp_password = ""
        mock_config.email_from = ""
        
        def get_settings():
            return mock_config
        
        monkeypatch.setattr('app.services.notification.get_settings', get_settings)
        from app.services.notification import NotificationService
        
        service = NotificationService()
        service.email_enabled = True
        result = await service.send_email(
            recipients=["test@example.com"],
            subject="Test",
            body="Test body"
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_email_success(self, monkeypatch):
        """測試郵件發送成功"""
        mock_config = MagicMock()
        mock_config.email_enabled = True
        mock_config.smtp_host = "smtp.example.com"
        mock_config.smtp_port = 587
        mock_config.smtp_user = "user@example.com"
        mock_config.smtp_password = "password"
        mock_config.email_from = "from@example.com"
        
        def get_settings():
            return mock_config
        
        monkeypatch.setattr('app.services.notification.get_settings', get_settings)
        from app.services.notification import NotificationService
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            service = NotificationService()
            service.email_enabled = True
            result = await service.send_email(
                recipients=["test@example.com"],
                subject="Test Subject",
                body="Test body",
                html_body="<p>Test body</p>"
            )
            
            assert result is True
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("user@example.com", "password")
            mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_webhook_disabled(self, notification_service):
        """測試 Webhook 通知未啟用"""
        result = await notification_service.send_webhook(
            url="",
            payload={"test": "data"}
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_webhook_success(self, monkeypatch):
        """測試 Webhook 發送成功"""
        mock_config = MagicMock()
        mock_config.webhook_enabled = True
        
        def get_settings():
            return mock_config
        
        monkeypatch.setattr('app.services.notification.get_settings', get_settings)
        from app.services.notification import NotificationService
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            service = NotificationService()
            service.webhook_enabled = True
            result = await service.send_webhook(
                url="https://example.com/webhook",
                payload={"test": "data"}
            )
            
            assert result is True
            mock_client_instance.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_webhook_failure(self, monkeypatch):
        """測試 Webhook 發送失敗"""
        mock_config = MagicMock()
        mock_config.webhook_enabled = True
        
        def get_settings():
            return mock_config
        
        monkeypatch.setattr('app.services.notification.get_settings', get_settings)
        from app.services.notification import NotificationService
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(side_effect=Exception("Connection error"))
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            service = NotificationService()
            service.webhook_enabled = True
            result = await service.send_webhook(
                url="https://example.com/webhook",
                payload={"test": "data"}
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_telegram_message_no_token(self, notification_service):
        """測試 Telegram 消息發送但無 Token"""
        result = await notification_service.send_telegram(
            chat_id="123456789",
            message="Test message"
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_alert_notification_email(self, monkeypatch):
        """測試發送告警通知（Email）"""
        mock_config = MagicMock()
        mock_config.email_enabled = True
        mock_config.smtp_host = "smtp.example.com"
        mock_config.smtp_port = 587
        mock_config.smtp_user = "user@example.com"
        mock_config.smtp_password = "password"
        mock_config.email_from = "from@example.com"
        
        def get_settings():
            return mock_config
        
        monkeypatch.setattr('app.services.notification.get_settings', get_settings)
        from app.services.notification import NotificationService
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            service = NotificationService()
            service.email_enabled = True
            result = await service.send_alert_notification(
                alert={
                    "title": "Test Alert",
                    "message": "Test message",
                    "level": "high"
                },
                notification_method="email",
                notification_target="admin@example.com"
            )
            
            assert "email" in result
            assert result["email"] is True
    
    @pytest.mark.asyncio
    async def test_send_alert_notification_webhook(self, monkeypatch):
        """測試發送告警通知（Webhook）"""
        mock_config = MagicMock()
        mock_config.webhook_enabled = True
        
        def get_settings():
            return mock_config
        
        monkeypatch.setattr('app.services.notification.get_settings', get_settings)
        from app.services.notification import NotificationService
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            service = NotificationService()
            service.webhook_enabled = True
            result = await service.send_alert_notification(
                alert={
                    "title": "Test Alert",
                    "message": "Test message",
                    "level": "high"
                },
                notification_method="webhook",
                notification_target="https://example.com/webhook"
            )
            
            assert "webhook" in result
            assert result["webhook"] is True
    
    @pytest.mark.asyncio
    async def test_send_alert_notification_unknown_method(self, notification_service):
        """測試發送告警通知（未知方法）"""
        result = await notification_service.send_alert_notification(
            alert={
                "title": "Test Alert",
                "message": "Test message"
            },
            notification_method="unknown",
            notification_target="target"
        )
        assert "unknown" in result
        assert result["unknown"] is False

