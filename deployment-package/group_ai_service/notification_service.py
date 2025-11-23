"""
告警通知服務 - 支持郵件、Telegram、Webhook 通知
"""
import logging
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationService:
    """告警通知服務"""
    
    def __init__(self):
        """初始化通知服務"""
        self._load_config()
    
    def _load_config(self):
        """從配置文件加載通知配置"""
        try:
            from group_ai_service.config import get_group_ai_config
            config = get_group_ai_config()
            
            self.notification_enabled = config.alert_notification_enabled
            self.email_enabled = config.alert_email_enabled
            self.telegram_enabled = config.alert_telegram_enabled
            self.webhook_enabled = config.alert_webhook_enabled
            
            # 郵件配置
            self.email_smtp_host = config.alert_email_smtp_host
            self.email_smtp_port = config.alert_email_smtp_port
            self.email_smtp_user = config.alert_email_smtp_user
            self.email_smtp_password = config.alert_email_smtp_password
            self.email_from = config.alert_email_from
            self.email_to = config.alert_email_to.split(",") if config.alert_email_to else []
            
            # Telegram 配置
            self.telegram_bot_token = config.alert_telegram_bot_token
            self.telegram_chat_id = config.alert_telegram_chat_id
            
            # Webhook 配置
            self.webhook_url = config.alert_webhook_url
            
            logger.info(f"通知服務初始化完成 (郵件: {self.email_enabled}, Telegram: {self.telegram_enabled}, Webhook: {self.webhook_enabled})")
        except Exception as e:
            logger.warning(f"加載通知配置失敗: {e}，使用默認配置")
            self.notification_enabled = False
            self.email_enabled = False
            self.telegram_enabled = False
            self.webhook_enabled = False
    
    async def send_email(
        self,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        recipients: Optional[List[str]] = None
    ) -> bool:
        """發送郵件通知"""
        if not self.notification_enabled or not self.email_enabled:
            logger.debug("郵件通知未啟用")
            return False
        
        if not self.email_smtp_host or not self.email_from:
            logger.warning("郵件配置不完整，無法發送郵件")
            return False
        
        recipients = recipients or self.email_to
        if not recipients:
            logger.warning("未指定郵件接收者")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_from
            msg['To'] = ', '.join(recipients)
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            with smtplib.SMTP(self.email_smtp_host, self.email_smtp_port) as server:
                if self.email_smtp_port == 587:
                    server.starttls()
                if self.email_smtp_user and self.email_smtp_password:
                    server.login(self.email_smtp_user, self.email_smtp_password)
                server.send_message(msg)
            
            logger.info(f"郵件通知發送成功: {subject}")
            return True
        except Exception as e:
            logger.error(f"發送郵件失敗: {e}", exc_info=True)
            return False
    
    async def send_telegram(
        self,
        message: str,
        chat_id: Optional[str] = None
    ) -> bool:
        """發送 Telegram 通知"""
        if not self.notification_enabled or not self.telegram_enabled:
            logger.debug("Telegram 通知未啟用")
            return False
        
        if not self.telegram_bot_token:
            logger.warning("Telegram Bot Token 未配置")
            return False
        
        chat_id = chat_id or self.telegram_chat_id
        if not chat_id:
            logger.warning("Telegram Chat ID 未配置")
            return False
        
        try:
            import aiohttp
            
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        logger.info("Telegram 通知發送成功")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Telegram API 返回錯誤: {response.status} - {error_text}")
                        return False
        except ImportError:
            logger.warning("aiohttp 未安裝，無法發送 Telegram 通知")
            return False
        except Exception as e:
            logger.error(f"發送 Telegram 通知失敗: {e}", exc_info=True)
            return False
    
    async def send_webhook(
        self,
        payload: Dict[str, Any],
        url: Optional[str] = None
    ) -> bool:
        """發送 Webhook 通知"""
        if not self.notification_enabled or not self.webhook_enabled:
            logger.debug("Webhook 通知未啟用")
            return False
        
        url = url or self.webhook_url
        if not url:
            logger.warning("Webhook URL 未配置")
            return False
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status in [200, 201, 204]:
                        logger.info("Webhook 通知發送成功")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Webhook 返回錯誤: {response.status} - {error_text}")
                        return False
        except ImportError:
            logger.warning("aiohttp 未安裝，無法發送 Webhook 通知")
            return False
        except Exception as e:
            logger.error(f"發送 Webhook 通知失敗: {e}", exc_info=True)
            return False
    
    async def send_alert_notification(
        self,
        alert: Dict[str, Any],
        notification_method: Optional[str] = None,
        notification_target: Optional[str] = None
    ) -> bool:
        """
        發送告警通知
        
        Args:
            alert: 告警信息字典
            notification_method: 通知方式 (email, telegram, webhook, all)
            notification_target: 通知目標（郵箱地址、Telegram Chat ID 等）
        
        Returns:
            是否發送成功
        """
        if not self.notification_enabled:
            logger.debug("告警通知未啟用")
            return False
        
        # 構建通知消息
        alert_type = alert.get("alert_type", "info")
        alert_level = alert.get("alert_level", alert_type)
        message = alert.get("message", "未知告警")
        account_id = alert.get("account_id")
        timestamp = alert.get("timestamp", datetime.now())
        
        # 格式化時間
        if isinstance(timestamp, datetime):
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            time_str = str(timestamp)
        
        # 構建主題和消息
        level_emoji = {
            "error": "🔴",
            "warning": "🟡",
            "info": "🔵"
        }
        emoji = level_emoji.get(alert_level, "⚪")
        
        subject = f"{emoji} 【告警】{message[:50]}"
        
        # 文本消息
        text_message = f"""
告警詳情：
級別：{alert_level.upper()}
類型：{alert_type}
消息：{message}
時間：{time_str}
"""
        if account_id:
            text_message += f"賬號：{account_id}\n"
        
        # HTML 消息（用於郵件）
        html_message = f"""
<html>
<body>
<h2>{emoji} 告警通知</h2>
<p><strong>級別：</strong>{alert_level.upper()}</p>
<p><strong>類型：</strong>{alert_type}</p>
<p><strong>消息：</strong>{message}</p>
<p><strong>時間：</strong>{time_str}</p>
"""
        if account_id:
            html_message += f"<p><strong>賬號：</strong>{account_id}</p>"
        html_message += "</body></html>"
        
        # Webhook 負載
        webhook_payload = {
            "type": "alert",
            "level": alert_level,
            "alert_type": alert_type,
            "message": message,
            "account_id": account_id,
            "timestamp": time_str,
            "data": alert
        }
        
        # 根據通知方式發送
        notification_method = notification_method or "all"
        success = False
        
        if notification_method in ["email", "all"] and self.email_enabled:
            recipients = [notification_target] if notification_target else None
            if await self.send_email(subject, text_message, html_message, recipients):
                success = True
        
        if notification_method in ["telegram", "all"] and self.telegram_enabled:
            chat_id = notification_target or None
            telegram_msg = f"<b>{emoji} 告警通知</b>\n\n{text_message}"
            if await self.send_telegram(telegram_msg, chat_id):
                success = True
        
        if notification_method in ["webhook", "all"] and self.webhook_enabled:
            if await self.send_webhook(webhook_payload):
                success = True
        
        return success


# 全局實例
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """獲取通知服務實例"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service

