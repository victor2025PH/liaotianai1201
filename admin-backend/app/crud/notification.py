"""
通知系統 CRUD 操作
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.notification import (
    NotificationConfig,
    Notification,
    NotificationType,
    NotificationStatus,
    NotificationTemplate,
)


def create_notification_config(
    db: Session,
    *,
    name: str,
    description: Optional[str] = None,
    notification_type: NotificationType,
    alert_levels: Optional[List[str]] = None,
    event_types: Optional[List[str]] = None,
    config_data: Dict[str, Any],
    recipients: List[str],
    enabled: bool = True,
) -> NotificationConfig:
    """創建通知配置"""
    config = NotificationConfig(
        name=name,
        description=description,
        notification_type=notification_type,
        alert_levels=alert_levels or [],
        event_types=event_types or [],
        config_data=config_data,
        recipients=recipients,
        enabled=enabled,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def get_notification_config(db: Session, *, config_id: int) -> Optional[NotificationConfig]:
    """獲取通知配置"""
    return db.query(NotificationConfig).filter(NotificationConfig.id == config_id).first()


def list_notification_configs(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    enabled: Optional[bool] = None,
) -> tuple[List[NotificationConfig], int]:
    """列出通知配置"""
    query = db.query(NotificationConfig)
    
    if enabled is not None:
        query = query.filter(NotificationConfig.enabled == enabled)
    
    total = query.count()
    configs = query.order_by(desc(NotificationConfig.created_at)).offset(skip).limit(limit).all()
    
    return configs, total


def update_notification_config(
    db: Session,
    *,
    config: NotificationConfig,
    name: Optional[str] = None,
    description: Optional[str] = None,
    alert_levels: Optional[List[str]] = None,
    event_types: Optional[List[str]] = None,
    config_data: Optional[Dict[str, Any]] = None,
    recipients: Optional[List[str]] = None,
    enabled: Optional[bool] = None,
) -> NotificationConfig:
    """更新通知配置"""
    if name is not None:
        config.name = name
    if description is not None:
        config.description = description
    if alert_levels is not None:
        config.alert_levels = alert_levels
    if event_types is not None:
        config.event_types = event_types
    if config_data is not None:
        config.config_data = config_data
    if recipients is not None:
        config.recipients = recipients
    if enabled is not None:
        config.enabled = enabled
    
    config.updated_at = datetime.utcnow()
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def delete_notification_config(db: Session, *, config_id: int) -> bool:
    """刪除通知配置"""
    config = db.query(NotificationConfig).filter(NotificationConfig.id == config_id).first()
    if not config:
        return False
    db.delete(config)
    db.commit()
    return True


def create_notification(
    db: Session,
    *,
    notification_type: NotificationType,
    title: str,
    message: str,
    recipient: str,
    level: Optional[str] = None,
    event_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    config_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Notification:
    """創建通知記錄"""
    notification = Notification(
        config_id=config_id,
        notification_type=notification_type,
        title=title,
        message=message,
        level=level,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        recipient=recipient,
        metadata_=metadata,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_notifications(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    recipient: Optional[str] = None,
    read: Optional[bool] = None,
    status: Optional[NotificationStatus] = None,
    notification_type: Optional[NotificationType] = None,
) -> tuple[List[Notification], int]:
    """查詢通知"""
    query = db.query(Notification)
    
    if recipient:
        query = query.filter(Notification.recipient == recipient)
    if read is not None:
        query = query.filter(Notification.read == read)
    if status:
        query = query.filter(Notification.status == status)
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)
    
    total = query.count()
    notifications = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()
    
    return notifications, total


def get_unread_count(db: Session, *, recipient: str) -> int:
    """獲取未讀通知數量"""
    return db.query(Notification).filter(
        and_(
            Notification.recipient == recipient,
            Notification.read == False,
            Notification.notification_type == NotificationType.BROWSER,
        )
    ).count()


def mark_notification_read(db: Session, *, notification_id: int, recipient: str) -> bool:
    """標記通知為已讀"""
    notification = db.query(Notification).filter(
        and_(
            Notification.id == notification_id,
            Notification.recipient == recipient,
        )
    ).first()
    if not notification:
        return False
    notification.read = True
    notification.read_at = datetime.utcnow()
    db.add(notification)
    db.commit()
    return True


def mark_all_read(db: Session, *, recipient: str) -> int:
    """標記所有通知為已讀"""
    count = db.query(Notification).filter(
        and_(
            Notification.recipient == recipient,
            Notification.read == False,
            Notification.notification_type == NotificationType.BROWSER,
        )
    ).update({"read": True, "read_at": datetime.utcnow()})
    db.commit()
    return count


def update_notification_status(
    db: Session,
    *,
    notification_id: int,
    status: NotificationStatus,
    error_message: Optional[str] = None,
) -> bool:
    """更新通知狀態"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        return False
    notification.status = status
    if status == NotificationStatus.SENT:
        notification.sent_at = datetime.utcnow()
    if error_message:
        notification.error_message = error_message
    db.add(notification)
    db.commit()
    return True


# ===================== 通知模板 CRUD =====================

def create_notification_template(
    db: Session,
    *,
    name: str,
    notification_type: NotificationType,
    title_template: str,
    body_template: str,
    description: Optional[str] = None,
    variables: Optional[List[str]] = None,
    conditions: Optional[Dict[str, Any]] = None,
    default_metadata: Optional[Dict[str, Any]] = None,
    enabled: bool = True,
) -> NotificationTemplate:
    template = NotificationTemplate(
        name=name,
        notification_type=notification_type,
        title_template=title_template,
        body_template=body_template,
        description=description,
        variables=variables or [],
        conditions=conditions or {},
        default_metadata=default_metadata or {},
        enabled=enabled,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def list_notification_templates(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    enabled: Optional[bool] = None,
) -> tuple[List[NotificationTemplate], int]:
    query = db.query(NotificationTemplate)
    if enabled is not None:
        query = query.filter(NotificationTemplate.enabled == enabled)
    total = query.count()
    templates = query.order_by(desc(NotificationTemplate.updated_at)).offset(skip).limit(limit).all()
    return templates, total


def get_notification_template(db: Session, *, template_id: int) -> Optional[NotificationTemplate]:
    return (
        db.query(NotificationTemplate)
        .filter(NotificationTemplate.id == template_id)
        .first()
    )


def update_notification_template(
    db: Session,
    *,
    template: NotificationTemplate,
    name: Optional[str] = None,
    notification_type: Optional[NotificationType] = None,
    title_template: Optional[str] = None,
    body_template: Optional[str] = None,
    description: Optional[str] = None,
    variables: Optional[List[str]] = None,
    conditions: Optional[Dict[str, Any]] = None,
    default_metadata: Optional[Dict[str, Any]] = None,
    enabled: Optional[bool] = None,
) -> NotificationTemplate:
    if name is not None:
        template.name = name
    if notification_type is not None:
        template.notification_type = notification_type
    if title_template is not None:
        template.title_template = title_template
    if body_template is not None:
        template.body_template = body_template
    if description is not None:
        template.description = description
    if variables is not None:
        template.variables = variables
    if conditions is not None:
        template.conditions = conditions
    if default_metadata is not None:
        template.default_metadata = default_metadata
    if enabled is not None:
        template.enabled = enabled

    template.updated_at = datetime.utcnow()
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def delete_notification_template(db: Session, *, template_id: int) -> bool:
    template = (
        db.query(NotificationTemplate)
        .filter(NotificationTemplate.id == template_id)
        .first()
    )
    if not template:
        return False
    db.delete(template)
    db.commit()
    return True


def find_matching_template(
    db: Session,
    *,
    notification_type: NotificationType,
    alert_level: Optional[str] = None,
    event_type: Optional[str] = None,
    resource_type: Optional[str] = None,
) -> Optional[NotificationTemplate]:
    """根據條件查找匹配的模板"""
    query = db.query(NotificationTemplate).filter(
        NotificationTemplate.notification_type == notification_type,
        NotificationTemplate.enabled == True,
    ).order_by(desc(NotificationTemplate.updated_at))

    templates = query.all()
    for template in templates:
        conditions = template.conditions or {}
        level_match = True
        event_match = True
        resource_match = True

        if conditions.get("alert_levels"):
            level_match = alert_level in conditions["alert_levels"]
        if conditions.get("event_types"):
            event_match = event_type in conditions["event_types"]
        if conditions.get("resource_types"):
            resource_match = resource_type in conditions["resource_types"]

        if level_match and event_match and resource_match:
            return template
    return None


# ===================== 批量操作 =====================

def mark_notifications_as_read(
    db: Session,
    *,
    notification_ids: List[int],
    recipient: str,
) -> int:
    if not notification_ids:
        return 0
    count = (
        db.query(Notification)
        .filter(
            Notification.id.in_(notification_ids),
            Notification.recipient == recipient,
        )
        .update({"read": True, "read_at": datetime.utcnow()}, synchronize_session=False)
    )
    db.commit()
    return count


def delete_notifications(
    db: Session,
    *,
    notification_ids: List[int],
    recipient: str,
) -> int:
    if not notification_ids:
        return 0
    count = (
        db.query(Notification)
        .filter(
            Notification.id.in_(notification_ids),
            Notification.recipient == recipient,
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    return count

