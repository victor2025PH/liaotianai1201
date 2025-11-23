"""
通知系統 API
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.api.deps import get_current_active_user, get_db_session
from app.models.user import User
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode
from app.models.notification import NotificationType, NotificationStatus
from app.crud.notification import (
    create_notification_config,
    get_notification_config,
    list_notification_configs,
    update_notification_config,
    delete_notification_config,
    get_notifications,
    get_unread_count,
    mark_notification_read,
    mark_all_read,
    create_notification_template,
    list_notification_templates,
    get_notification_template,
    update_notification_template,
    delete_notification_template,
    mark_notifications_as_read,
    delete_notifications,
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ============ 請求/響應模型 ============

class NotificationConfigCreate(BaseModel):
    """創建通知配置請求"""
    name: str
    description: Optional[str] = None
    notification_type: NotificationType
    alert_levels: Optional[List[str]] = None
    event_types: Optional[List[str]] = None
    config_data: dict
    recipients: List[str]
    enabled: bool = True


class NotificationConfigUpdate(BaseModel):
    """更新通知配置請求"""
    name: Optional[str] = None
    description: Optional[str] = None
    alert_levels: Optional[List[str]] = None
    event_types: Optional[List[str]] = None
    config_data: Optional[dict] = None
    recipients: Optional[List[str]] = None
    enabled: Optional[bool] = None


class NotificationConfigRead(BaseModel):
    """通知配置讀取模型"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None
    notification_type: NotificationType
    alert_levels: Optional[List[str]] = None
    event_types: Optional[List[str]] = None
    config_data: dict
    recipients: List[str]
    enabled: bool
    created_at: str
    updated_at: str


class NotificationRead(BaseModel):
    """通知讀取模型"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: int
    config_id: Optional[int] = None
    notification_type: NotificationType
    title: str
    message: str
    level: Optional[str] = None
    event_type: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    recipient: str
    status: NotificationStatus
    sent_at: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[dict] = Field(default=None, alias="metadata_")
    read: bool
    read_at: Optional[str] = None
    created_at: str


class NotificationListResponse(BaseModel):
    """通知列表響應"""
    items: List[NotificationRead]
    total: int
    skip: int
    limit: int
    unread_count: int


class NotificationTemplateCondition(BaseModel):
    alert_levels: Optional[List[str]] = None
    event_types: Optional[List[str]] = None
    resource_types: Optional[List[str]] = None


class NotificationTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    notification_type: NotificationType
    title_template: str
    body_template: str
    variables: Optional[List[str]] = None
    conditions: Optional[NotificationTemplateCondition] = None
    default_metadata: Optional[Dict[str, Any]] = None
    enabled: bool = True


class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    notification_type: Optional[NotificationType] = None
    title_template: Optional[str] = None
    body_template: Optional[str] = None
    variables: Optional[List[str]] = None
    conditions: Optional[NotificationTemplateCondition] = None
    default_metadata: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class NotificationTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None
    notification_type: NotificationType
    title_template: str
    body_template: str
    variables: Optional[List[str]] = None
    conditions: Optional[Dict[str, Any]] = None
    default_metadata: Optional[Dict[str, Any]] = None
    enabled: bool
    created_at: str
    updated_at: str


class NotificationTemplateListResponse(BaseModel):
    items: List[NotificationTemplateRead]
    total: int
    skip: int
    limit: int


class NotificationTemplatePreviewRequest(BaseModel):
    template_id: Optional[int] = None
    title_template: Optional[str] = None
    body_template: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class NotificationTemplatePreviewResponse(BaseModel):
    title: str
    message: str


class NotificationBatchRequest(BaseModel):
    notification_ids: List[int]


# ============ 通知配置 API ============

@router.post("/configs", response_model=NotificationConfigRead, status_code=status.HTTP_201_CREATED)
async def create_notification_config_endpoint(
    config_create: NotificationConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """創建通知配置（需要管理權限）"""
    check_permission(current_user, PermissionCode.ALERT_RULE_CREATE.value, db)
    
    try:
        config = create_notification_config(
            db,
            name=config_create.name,
            description=config_create.description,
            notification_type=config_create.notification_type,
            alert_levels=config_create.alert_levels,
            event_types=config_create.event_types,
            config_data=config_create.config_data,
            recipients=config_create.recipients,
            enabled=config_create.enabled,
        )
        return NotificationConfigRead.model_validate(config)
    except Exception as e:
        db.rollback()
        logger.error(f"創建通知配置失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建通知配置失敗: {str(e)}"
        )


@router.get("/configs", response_model=List[NotificationConfigRead])
async def list_notification_configs_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    enabled: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """列出通知配置（需要查看權限）"""
    check_permission(current_user, PermissionCode.ALERT_RULE_VIEW.value, db)
    
    try:
        configs, _ = list_notification_configs(db, skip=skip, limit=limit, enabled=enabled)
        return [NotificationConfigRead.model_validate(config) for config in configs]
    except Exception as e:
        logger.error(f"列出通知配置失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出通知配置失敗: {str(e)}"
        )


@router.get("/configs/{config_id}", response_model=NotificationConfigRead)
async def get_notification_config_endpoint(
    config_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """獲取通知配置詳情"""
    check_permission(current_user, PermissionCode.ALERT_RULE_VIEW.value, db)
    
    config = get_notification_config(db, config_id=config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"通知配置 {config_id} 不存在"
        )
    return NotificationConfigRead.model_validate(config)


@router.put("/configs/{config_id}", response_model=NotificationConfigRead)
async def update_notification_config_endpoint(
    config_id: int,
    config_update: NotificationConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """更新通知配置"""
    check_permission(current_user, PermissionCode.ALERT_RULE_UPDATE.value, db)
    
    config = get_notification_config(db, config_id=config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"通知配置 {config_id} 不存在"
        )
    
    try:
        updated_config = update_notification_config(
            db,
            config=config,
            name=config_update.name,
            description=config_update.description,
            alert_levels=config_update.alert_levels,
            event_types=config_update.event_types,
            config_data=config_update.config_data,
            recipients=config_update.recipients,
            enabled=config_update.enabled,
        )
        return NotificationConfigRead.model_validate(updated_config)
    except Exception as e:
        db.rollback()
        logger.error(f"更新通知配置失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新通知配置失敗: {str(e)}"
        )


@router.delete("/configs/{config_id}", status_code=status.HTTP_200_OK)
async def delete_notification_config_endpoint(
    config_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """刪除通知配置"""
    check_permission(current_user, PermissionCode.ALERT_RULE_DELETE.value, db)
    
    success = delete_notification_config(db, config_id=config_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"通知配置 {config_id} 不存在"
        )
    return {"message": f"通知配置 {config_id} 已刪除"}


# ============ 通知模板 API ============

@router.post("/templates", response_model=NotificationTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_notification_template_endpoint(
    template_create: NotificationTemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    check_permission(current_user, PermissionCode.ALERT_RULE_CREATE.value, db)
    try:
        template = create_notification_template(
            db,
            name=template_create.name,
            description=template_create.description,
            notification_type=template_create.notification_type,
            title_template=template_create.title_template,
            body_template=template_create.body_template,
            variables=template_create.variables,
            conditions=template_create.conditions.model_dump() if template_create.conditions else None,
            default_metadata=template_create.default_metadata,
            enabled=template_create.enabled,
        )
        return NotificationTemplateRead.model_validate(template)
    except Exception as e:
        db.rollback()
        logger.error(f"創建通知模板失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"創建通知模板失敗: {str(e)}")


@router.get("/templates", response_model=NotificationTemplateListResponse)
async def list_notification_templates_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    enabled: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    check_permission(current_user, PermissionCode.ALERT_RULE_VIEW.value, db)
    templates, total = list_notification_templates(db, skip=skip, limit=limit, enabled=enabled)
    return NotificationTemplateListResponse(
        items=[NotificationTemplateRead.model_validate(t) for t in templates],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/templates/{template_id}", response_model=NotificationTemplateRead)
async def get_notification_template_endpoint(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    check_permission(current_user, PermissionCode.ALERT_RULE_VIEW.value, db)
    template = get_notification_template(db, template_id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"通知模板 {template_id} 不存在")
    return NotificationTemplateRead.model_validate(template)


@router.put("/templates/{template_id}", response_model=NotificationTemplateRead)
async def update_notification_template_endpoint(
    template_id: int,
    template_update: NotificationTemplateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    check_permission(current_user, PermissionCode.ALERT_RULE_UPDATE.value, db)
    template = get_notification_template(db, template_id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"通知模板 {template_id} 不存在")
    try:
        updated = update_notification_template(
            db,
            template=template,
            name=template_update.name,
            notification_type=template_update.notification_type,
            title_template=template_update.title_template,
            body_template=template_update.body_template,
            description=template_update.description,
            variables=template_update.variables,
            conditions=template_update.conditions.model_dump() if template_update.conditions else None,
            default_metadata=template_update.default_metadata,
            enabled=template_update.enabled,
        )
        return NotificationTemplateRead.model_validate(updated)
    except Exception as e:
        db.rollback()
        logger.error(f"更新通知模板失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新通知模板失敗: {str(e)}")


@router.delete("/templates/{template_id}", status_code=status.HTTP_200_OK)
async def delete_notification_template_endpoint(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    check_permission(current_user, PermissionCode.ALERT_RULE_DELETE.value, db)
    success = delete_notification_template(db, template_id=template_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"通知模板 {template_id} 不存在")
    return {"message": f"通知模板 {template_id} 已刪除"}


@router.post("/templates/preview", response_model=NotificationTemplatePreviewResponse)
async def preview_notification_template_endpoint(
    preview: NotificationTemplatePreviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    check_permission(current_user, PermissionCode.ALERT_RULE_VIEW.value, db)
    template = None
    if preview.template_id:
        template = get_notification_template(db, template_id=preview.template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"通知模板 {preview.template_id} 不存在")

    title_template = preview.title_template or (template.title_template if template else None)
    body_template = preview.body_template or (template.body_template if template else None)
    if not title_template or not body_template:
        raise HTTPException(status_code=400, detail="缺少模板內容")

    try:
        title = title_template.format(**preview.context)
        message = body_template.format(**preview.context)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"模板渲染失敗: {str(e)}") from e

    return NotificationTemplatePreviewResponse(title=title, message=message)


# ============ 通知查詢 API ============

def _get_recipient_email(current_user: Optional[User], db: Session) -> str:
    """獲取接收者郵箱（處理禁用認證的情況）"""
    from app.core.config import get_settings
    settings = get_settings()
    
    # 如果禁用認證，使用默認管理員郵箱
    if settings.disable_auth or current_user is None:
        try:
            from app.crud.user import get_user_by_email
            admin = get_user_by_email(db, email=settings.admin_default_email)
            return admin.email if admin else settings.admin_default_email
        except Exception:
            return settings.admin_default_email
    else:
        return current_user.email


@router.get("/", response_model=NotificationListResponse)
async def list_notifications_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    read: Optional[bool] = Query(None),
    notification_type: Optional[NotificationType] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """查詢通知（當前用戶）"""
    recipient_email = _get_recipient_email(current_user, db)
    
    try:
        notifications, total = get_notifications(
            db,
            skip=skip,
            limit=limit,
            recipient=recipient_email,
            read=read,
            notification_type=notification_type,
        )
        unread_count = get_unread_count(db, recipient=recipient_email)
        
        # 手動轉換通知對象，確保 datetime 字段正確序列化為字符串
        notification_items = []
        for n in notifications:
            notification_items.append(NotificationRead(
                id=n.id,
                config_id=n.config_id,
                notification_type=n.notification_type,
                title=n.title,
                message=n.message,
                level=n.level,
                event_type=n.event_type,
                resource_type=n.resource_type,
                resource_id=n.resource_id,
                recipient=n.recipient,
                status=n.status,
                sent_at=n.sent_at.isoformat() if n.sent_at else None,
                error_message=n.error_message,
                metadata=n.metadata_ if hasattr(n, 'metadata_') else None,
                read=n.read,
                read_at=n.read_at.isoformat() if n.read_at else None,
                created_at=n.created_at.isoformat() if n.created_at else "",
            ))
        
        return NotificationListResponse(
            items=notification_items,
            total=total,
            skip=skip,
            limit=limit,
            unread_count=unread_count,
        )
    except Exception as e:
        logger.error(f"查詢通知失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢通知失敗: {str(e)}"
        )


@router.get("/unread-count", response_model=dict)
async def get_unread_count_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """獲取未讀通知數量"""
    recipient_email = _get_recipient_email(current_user, db)
    count = get_unread_count(db, recipient=recipient_email)
    return {"unread_count": count}


@router.post("/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_read_endpoint(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """標記通知為已讀"""
    recipient_email = _get_recipient_email(current_user, db)
    success = mark_notification_read(db, notification_id=notification_id, recipient=recipient_email)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"通知 {notification_id} 不存在或無權限"
        )
    return {"message": "通知已標記為已讀"}


@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_read_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """標記所有通知為已讀"""
    recipient_email = _get_recipient_email(current_user, db)
    count = mark_all_read(db, recipient=recipient_email)
    return {"message": f"已標記 {count} 條通知為已讀", "count": count}


@router.post("/batch/read", status_code=status.HTTP_200_OK)
async def batch_mark_notifications_read_endpoint(
    request: NotificationBatchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    recipient_email = _get_recipient_email(current_user, db)
    updated = mark_notifications_as_read(
        db,
        notification_ids=request.notification_ids,
        recipient=recipient_email,
    )
    return {"message": f"已標記 {updated} 條通知為已讀", "count": updated}


@router.post("/batch/delete", status_code=status.HTTP_200_OK)
async def batch_delete_notifications_endpoint(
    request: NotificationBatchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    recipient_email = _get_recipient_email(current_user, db)
    deleted = delete_notifications(
        db,
        notification_ids=request.notification_ids,
        recipient=recipient_email,
    )
    return {"message": f"已刪除 {deleted} 條通知", "count": deleted}


# ============ WebSocket 實時推送 ============

class ConnectionManager:
    """WebSocket 連接管理器"""
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_email: str):
        await websocket.accept()
        self.active_connections[user_email] = websocket
        logger.info(f"用戶 {user_email} 已連接 WebSocket")
    
    def disconnect(self, user_email: str):
        if user_email in self.active_connections:
            del self.active_connections[user_email]
            logger.info(f"用戶 {user_email} 已斷開 WebSocket")
    
    async def send_personal_message(self, message: dict, user_email: str):
        if user_email in self.active_connections:
            try:
                await self.active_connections[user_email].send_json(message)
            except Exception as e:
                logger.error(f"發送消息給 {user_email} 失敗: {e}")
                self.disconnect(user_email)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for user_email, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"廣播消息給 {user_email} 失敗: {e}")
                disconnected.append(user_email)
        
        for user_email in disconnected:
            self.disconnect(user_email)


# 全局連接管理器
connection_manager = ConnectionManager()


@router.websocket("/ws/{user_email}")
async def websocket_endpoint(websocket: WebSocket, user_email: str):
    """WebSocket 端點（實時推送通知）"""
    await connection_manager.connect(websocket, user_email)
    try:
        while True:
            # 保持連接活躍，等待服務器推送消息
            data = await websocket.receive_text()
            # 可以處理客戶端發送的心跳消息
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        connection_manager.disconnect(user_email)


# 導出連接管理器供其他模塊使用
def get_connection_manager() -> ConnectionManager:
    """獲取連接管理器實例"""
    return connection_manager

