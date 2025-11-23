"""
通知服務 - 發送各種類型的通知
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.notification import NotificationType, NotificationStatus
from app.crud.notification import (
    create_notification,
    update_notification_status,
    get_notification_config,
    list_notification_configs,
    find_matching_template,
)
# 延遲導入以避免循環依賴
def get_connection_manager():
    from app.api.notifications import get_connection_manager as _get_connection_manager
    return _get_connection_manager()

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服務類"""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def _render_template(self, template_str: str, context: Dict[str, Any]) -> str:
        """使用簡單格式化渲染模板"""
        try:
            return template_str.format(**context)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"渲染模板失敗: {exc}")
            return template_str

    def _build_template_context(
        self,
        *,
        alert_level: Optional[str],
        alert_title: Optional[str],
        alert_message: Optional[str],
        event_type: Optional[str],
        resource_type: Optional[str],
        resource_id: Optional[str],
        recipient: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        context = {
            "alert_level": alert_level or "",
            "alert_title": alert_title or "",
            "alert_message": alert_message or "",
            "event_type": event_type or "",
            "resource_type": resource_type or "",
            "resource_id": resource_id or "",
            "recipient": recipient or "",
            "timestamp": datetime.utcnow().isoformat(),
        }
        if extra:
            context.update(extra)
        return context

    def _apply_notification_template(
        self,
        *,
        notification_type: NotificationType,
        alert_level: Optional[str],
        event_type: Optional[str],
        resource_type: Optional[str],
        resource_id: Optional[str],
        base_title: str,
        base_message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """套用匹配的通知模板"""
        template = find_matching_template(
            self.db,
            notification_type=notification_type,
            alert_level=alert_level,
            event_type=event_type,
            resource_type=resource_type,
        )
        if not template:
            return {
                "title": base_title,
                "message": base_message,
                "metadata": metadata,
            }

        context = self._build_template_context(
            alert_level=alert_level,
            alert_title=base_title,
            alert_message=base_message,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
        )

        rendered_title = self._render_template(template.title_template, context)
        rendered_message = self._render_template(template.body_template, context)
        merged_metadata = {**(template.default_metadata or {}), **(metadata or {})}
        merged_metadata["template_id"] = template.id

        return {
            "title": rendered_title,
            "message": rendered_message,
            "metadata": merged_metadata,
        }
    
    async def send_email(
        self,
        *,
        recipient: str,
        subject: str,
        body: str,
        config_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """發送郵件通知"""
        try:
            # 使用配置數據或默認設置
            if config_data:
                smtp_host = config_data.get("smtp_host", self.settings.smtp_host)
                smtp_port = config_data.get("smtp_port", self.settings.smtp_port)
                smtp_user = config_data.get("smtp_user", self.settings.smtp_user)
                smtp_password = config_data.get("smtp_password", self.settings.smtp_password)
                email_from = config_data.get("email_from", self.settings.email_from)
            else:
                smtp_host = self.settings.smtp_host
                smtp_port = self.settings.smtp_port
                smtp_user = self.settings.smtp_user
                smtp_password = self.settings.smtp_password
                email_from = self.settings.email_from
            
            if not email_from or not smtp_user:
                logger.warning("郵件配置不完整，跳過發送")
                return False
            
            # 創建郵件
            msg = MIMEMultipart()
            msg["From"] = email_from
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html", "utf-8"))
            
            # 發送郵件
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"郵件已發送到 {recipient}")
            return True
        except Exception as e:
            logger.error(f"發送郵件失敗: {e}", exc_info=True)
            return False
    
    async def send_webhook(
        self,
        *,
        webhook_url: str,
        payload: Dict[str, Any],
    ) -> bool:
        """發送 Webhook 通知"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json=payload)
                response.raise_for_status()
            logger.info(f"Webhook 已發送到 {webhook_url}")
            return True
        except Exception as e:
            logger.error(f"發送 Webhook 失敗: {e}", exc_info=True)
            return False
    
    async def send_browser_notification(
        self,
        *,
        recipient: str,
        title: str,
        message: str,
        level: Optional[str] = None,
        event_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """創建瀏覽器通知記錄（實際推送通過 WebSocket/SSE）"""
        notification = create_notification(
            self.db,
            notification_type=NotificationType.BROWSER,
            title=title,
            message=message,
            recipient=recipient,
            level=level,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata,
        )
        
        # 通過 WebSocket 實時推送給前端
        try:
            connection_manager = get_connection_manager()
            if connection_manager:
                await connection_manager.send_personal_message(
                {
                    "type": "notification",
                    "id": notification.id,
                    "title": title,
                    "message": message,
                    "level": level,
                    "event_type": event_type,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "created_at": notification.created_at.isoformat(),
                    },
                    recipient,
                )
                update_notification_status(
                    self.db,
                    notification_id=notification.id,
                    status=NotificationStatus.SENT,
                )
            else:
                # 如果連接管理器不可用，標記為待發送
                update_notification_status(
                    self.db,
                    notification_id=notification.id,
                    status=NotificationStatus.PENDING,
                )
        except Exception as e:
            logger.error(f"WebSocket 推送失敗: {e}", exc_info=True)
            update_notification_status(
                self.db,
                notification_id=notification.id,
                status=NotificationStatus.FAILED,
                error_message=str(e),
            )
        
        return notification.id
    
    async def send_notification(
        self,
        *,
        notification_type: NotificationType,
        recipients: List[str],
        title: str,
        message: str,
        level: Optional[str] = None,
        event_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        config_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """發送通知（統一接口）"""
        results = {
            "success_count": 0,
            "failed_count": 0,
            "notifications": [],
        }
        
        config = None
        if config_id:
            config = get_notification_config(self.db, config_id=config_id)
        
        for recipient in recipients:
            try:
                notification_id = None
                success = False
                
                if notification_type == NotificationType.EMAIL:
                    # 發送郵件
                    config_data = config.config_data if config else None
                    success = await self.send_email(
                        recipient=recipient,
                        subject=title,
                        body=message,
                        config_data=config_data,
                    )
                    # 創建通知記錄
                    notification = create_notification(
                        self.db,
                        notification_type=NotificationType.EMAIL,
                        title=title,
                        message=message,
                        recipient=recipient,
                        level=level,
                        event_type=event_type,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        config_id=config_id,
                        metadata=metadata,
                    )
                    notification_id = notification.id
                
                elif notification_type == NotificationType.WEBHOOK:
                    # 發送 Webhook
                    webhook_url = None
                    if config:
                        webhook_url = config.config_data.get("webhook_url")
                    elif self.settings.webhook_enabled:
                        webhook_url = self.settings.webhook_url
                    
                    if webhook_url:
                        payload = {
                            "title": title,
                            "message": message,
                            "level": level,
                            "event_type": event_type,
                            "resource_type": resource_type,
                            "resource_id": resource_id,
                            "metadata": metadata,
                        }
                        success = await self.send_webhook(webhook_url=webhook_url, payload=payload)
                        # 創建通知記錄
                        notification = create_notification(
                            self.db,
                            notification_type=NotificationType.WEBHOOK,
                            title=title,
                            message=message,
                            recipient=recipient,
                            level=level,
                            event_type=event_type,
                            resource_type=resource_type,
                            resource_id=resource_id,
                            config_id=config_id,
                            metadata=metadata,
                        )
                        notification_id = notification.id
                
                elif notification_type == NotificationType.BROWSER:
                    # 創建瀏覽器通知
                    notification_id = await self.send_browser_notification(
                        recipient=recipient,
                        title=title,
                        message=message,
                        level=level,
                        event_type=event_type,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        metadata=metadata,
                    )
                    success = True
                
                # 更新通知狀態
                if notification_id:
                    update_notification_status(
                        self.db,
                        notification_id=notification_id,
                        status=NotificationStatus.SENT if success else NotificationStatus.FAILED,
                        error_message=None if success else "發送失敗",
                    )
                
                if success:
                    results["success_count"] += 1
                else:
                    results["failed_count"] += 1
                
                results["notifications"].append({
                    "recipient": recipient,
                    "notification_id": notification_id,
                    "success": success,
                })
            
            except Exception as e:
                logger.error(f"發送通知給 {recipient} 失敗: {e}", exc_info=True)
                results["failed_count"] += 1
                results["notifications"].append({
                    "recipient": recipient,
                    "notification_id": None,
                    "success": False,
                    "error": str(e),
                })
        
        return results
    
    async def send_alert_notification(
        self,
        *,
        alert_level: str,
        alert_title: str,
        alert_message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """發送告警通知（根據配置自動選擇通知方式）"""
        # 查詢所有啟用的通知配置
        configs, _ = list_notification_configs(self.db, enabled=True)
        
        results = {
            "success_count": 0,
            "failed_count": 0,
            "notifications": [],
        }
        event_type = "alert"
        
        for config in configs:
            # 檢查告警級別是否匹配
            if config.alert_levels and alert_level not in config.alert_levels:
                continue
            
            # 檢查事件類型是否匹配
            if config.event_types and "alert" not in config.event_types:
                continue
            
            metadata_payload = {"config_id": config.id}
            rendered = self._apply_notification_template(
                notification_type=config.notification_type,
                alert_level=alert_level,
                event_type=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                base_title=alert_title,
                base_message=alert_message,
                metadata=metadata_payload,
            )
            for recipient in config.recipients:
                result = await self.send_notification(
                    notification_type=config.notification_type,
                    recipients=[recipient],
                    title=rendered["title"],
                    message=rendered["message"],
                    level=alert_level,
                    event_type=event_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    config_id=config.id,
                    metadata=rendered["metadata"],
                )
                results["success_count"] += result["success_count"]
                results["failed_count"] += result["failed_count"]
                results["notifications"].extend(result["notifications"])
        
        return results

