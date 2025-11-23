"""
通知服務 - 發送 Email、Webhook、Telegram 通知
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from datetime import datetime

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服務"""
    
    def __init__(self):
        self.settings = get_settings()
        self.email_enabled = getattr(self.settings, 'email_enabled', False)
        self.webhook_enabled = getattr(self.settings, 'webhook_enabled', False)
        self.telegram_enabled = getattr(self.settings, 'telegram_bot_token', None) is not None
    
    async def send_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        發送郵件
        
        Args:
            recipients: 收件人列表
            subject: 郵件主題
            body: 郵件正文（純文本）
            html_body: 郵件正文（HTML，可選）
        
        Returns:
            是否發送成功
        """
        if not self.email_enabled:
            logger.warning("郵件通知未啟用，跳過發送")
            return False
        
        try:
            smtp_host = getattr(self.settings, 'smtp_host', 'smtp.gmail.com')
            smtp_port = getattr(self.settings, 'smtp_port', 587)
            smtp_user = getattr(self.settings, 'smtp_user', '')
            smtp_password = getattr(self.settings, 'smtp_password', '')
            email_from = getattr(self.settings, 'email_from', smtp_user)
            
            if not smtp_user or not smtp_password:
                logger.warning("SMTP 配置不完整，無法發送郵件")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = email_from
            msg['To'] = ', '.join(recipients)
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"郵件發送成功: {subject} -> {recipients}")
            return True
        
        except Exception as e:
            logger.error(f"發送郵件失敗: {e}", exc_info=True)
            return False
    
    async def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        timeout: int = 10
    ) -> bool:
        """
        發送 Webhook
        
        Args:
            url: Webhook URL
            payload: 請求負載（JSON）
            timeout: 請求超時時間（秒）
        
        Returns:
            是否發送成功
        """
        if not self.webhook_enabled and not url:
            logger.warning("Webhook 通知未啟用或 URL 為空，跳過發送")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            
            logger.info(f"Webhook 發送成功: {url}")
            return True
        
        except httpx.TimeoutException:
            logger.error(f"Webhook 請求超時: {url}")
            return False
        except httpx.HTTPStatusError as e:
            logger.error(f"Webhook 請求失敗: {url}, 狀態碼: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"發送 Webhook 失敗: {url}, 錯誤: {e}", exc_info=True)
            return False
    
    async def send_telegram(
        self,
        chat_id: str,
        message: str,
        parse_mode: Optional[str] = "HTML"
    ) -> bool:
        """
        發送 Telegram 消息
        
        Args:
            chat_id: Telegram Chat ID
            message: 消息內容
            parse_mode: 解析模式（HTML 或 Markdown）
        
        Returns:
            是否發送成功
        """
        if not self.telegram_enabled:
            logger.warning("Telegram 通知未啟用，跳過發送")
            return False
        
        try:
            bot_token = getattr(self.settings, 'telegram_bot_token', None)
            if not bot_token:
                logger.warning("Telegram Bot Token 未配置，無法發送消息")
                return False
            
            api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(api_url, json=payload)
                response.raise_for_status()
            
            logger.info(f"Telegram 消息發送成功: {chat_id}")
            return True
        
        except httpx.TimeoutException:
            logger.error(f"Telegram 請求超時: {chat_id}")
            return False
        except httpx.HTTPStatusError as e:
            logger.error(f"Telegram 請求失敗: {chat_id}, 狀態碼: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"發送 Telegram 消息失敗: {chat_id}, 錯誤: {e}", exc_info=True)
            return False
    
    async def send_alert_notification(
        self,
        alert: Dict[str, Any],
        notification_method: str = "email",
        notification_target: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        發送告警通知
        
        Args:
            alert: 告警信息字典
            notification_method: 通知方式（email, webhook, telegram）
            notification_target: 通知目標（郵箱地址、Webhook URL、Telegram Chat ID）
        
        Returns:
            發送結果字典 {method: success}
        """
        results = {}
        
        if not notification_target:
            logger.warning("通知目標為空，跳過發送")
            return results
        
        alert_level = alert.get("alert_level", alert.get("alert_type", "info"))
        alert_name = alert.get("name", alert.get("title", "告警"))
        alert_message = alert.get("message", alert.get("description", ""))
        account_id = alert.get("account_id")
        timestamp = alert.get("timestamp", datetime.now())
        
        # 格式化時間戳
        if isinstance(timestamp, str):
            timestamp_str = timestamp
        elif isinstance(timestamp, datetime):
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp_str = str(timestamp)
        
        # 根據通知方式發送
        if notification_method == "email":
            recipients = [email.strip() for email in notification_target.split(",") if email.strip()]
            if recipients:
                subject = f"【{alert_level.upper()}】{alert_name}"
                body = f"""
告警詳情：
告警名稱：{alert_name}
告警級別：{alert_level}
告警時間：{timestamp_str}
{'賬號 ID：' + account_id if account_id else ''}

告警消息：
{alert_message}

---
此為自動發送的告警通知，請及時處理。
                """.strip()
                
                html_body = f"""
                <html>
                <body>
                    <h2>告警詳情</h2>
                    <table border="1" cellpadding="5">
                        <tr><td><strong>告警名稱</strong></td><td>{alert_name}</td></tr>
                        <tr><td><strong>告警級別</strong></td><td>{alert_level}</td></tr>
                        <tr><td><strong>告警時間</strong></td><td>{timestamp_str}</td></tr>
                        {f'<tr><td><strong>賬號 ID</strong></td><td>{account_id}</td></tr>' if account_id else ''}
                    </table>
                    <h3>告警消息</h3>
                    <p>{alert_message}</p>
                    <hr>
                    <p><em>此為自動發送的告警通知，請及時處理。</em></p>
                </body>
                </html>
                """
                
                results["email"] = await self.send_email(recipients, subject, body, html_body)
        
        elif notification_method == "webhook":
            payload = {
                "type": "alert",
                "alert_level": alert_level,
                "alert_name": alert_name,
                "message": alert_message,
                "account_id": account_id,
                "timestamp": timestamp_str,
                "data": alert
            }
            results["webhook"] = await self.send_webhook(notification_target, payload)
        
        elif notification_method == "telegram":
            # 格式化 Telegram 消息
            telegram_message = f"""
🔔 <b>{alert_name}</b>

<b>級別：</b>{alert_level}
<b>時間：</b>{timestamp_str}
{f'<b>賬號：</b>{account_id}' if account_id else ''}

<b>消息：</b>
{alert_message}
            """.strip()
            
            results["telegram"] = await self.send_telegram(notification_target, telegram_message)
        
        else:
            logger.warning(f"未知的通知方式: {notification_method}")
            results[notification_method] = False
        
        return results


# 全局實例（單例模式）
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """獲取通知服務實例"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service

