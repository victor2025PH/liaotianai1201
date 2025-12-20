"""
定時消息任務管理 API
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db import get_db
from app.models.unified_features import ScheduledMessageTask, ScheduledMessageLog
from app.api.deps import get_current_active_user
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode
from app.models.user import User
from app.core.cache import cached, invalidate_cache
from app.core.db_optimization import monitor_query_performance

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scheduled-messages", tags=["Scheduled Messages"])


# ============ 請求/響應模型 ============

class ScheduledMessageCreate(BaseModel):
    """創建定時消息任務請求"""
    task_id: str
    name: str
    enabled: bool = True
    schedule_type: str = "cron"  # cron/interval/once/conditional
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    timezone: str = "Asia/Shanghai"
    condition: Optional[str] = None
    check_interval: int = 300
    groups: List[int] = []
    accounts: List[str] = []
    rotation: bool = False
    rotation_strategy: str = "round_robin"
    message_template: str = ""
    template_variables: dict = {}
    media_path: Optional[str] = None
    delay_min: int = 0
    delay_max: int = 5
    retry_times: int = 3
    retry_interval: int = 60
    description: Optional[str] = None


class ScheduledMessageUpdate(BaseModel):
    """更新定時消息任務請求"""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    schedule_type: Optional[str] = None
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    timezone: Optional[str] = None
    condition: Optional[str] = None
    check_interval: Optional[int] = None
    groups: Optional[List[int]] = None
    accounts: Optional[List[str]] = None
    rotation: Optional[bool] = None
    rotation_strategy: Optional[str] = None
    message_template: Optional[str] = None
    template_variables: Optional[dict] = None
    media_path: Optional[str] = None
    delay_min: Optional[int] = None
    delay_max: Optional[int] = None
    retry_times: Optional[int] = None
    retry_interval: Optional[int] = None
    description: Optional[str] = None


class ScheduledMessageResponse(BaseModel):
    """定時消息任務響應"""
    id: str
    task_id: str
    name: str
    enabled: bool
    schedule_type: str
    cron_expression: Optional[str]
    interval_seconds: Optional[int]
    start_time: Optional[str]
    end_time: Optional[str]
    timezone: str
    condition: Optional[str]
    check_interval: int
    groups: List[int]
    accounts: List[str]
    rotation: bool
    rotation_strategy: str
    message_template: str
    template_variables: dict
    media_path: Optional[str]
    delay_min: int
    delay_max: int
    retry_times: int
    retry_interval: int
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    run_count: int
    success_count: int
    failure_count: int
    description: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ScheduledMessageLogResponse(BaseModel):
    """定時消息執行日誌響應"""
    id: str
    task_id: str
    account_id: str
    group_id: int
    success: bool
    message_sent: Optional[str]
    error_message: Optional[str]
    executed_at: datetime
    
    class Config:
        from_attributes = True


# ============ API 端點 ============

@router.post("", response_model=ScheduledMessageResponse, status_code=status.HTTP_201_CREATED)
@check_permission(PermissionCode.GROUP_AI_MANAGE)
async def create_scheduled_message(
    data: ScheduledMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """創建定時消息任務"""
    # 檢查 task_id 是否已存在
    existing = db.query(ScheduledMessageTask).filter(
        ScheduledMessageTask.task_id == data.task_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任務 ID {data.task_id} 已存在"
        )
    
    # 創建任務
    task = ScheduledMessageTask(
        task_id=data.task_id,
        name=data.name,
        enabled=data.enabled,
        schedule_type=data.schedule_type,
        cron_expression=data.cron_expression,
        interval_seconds=data.interval_seconds,
        start_time=data.start_time,
        end_time=data.end_time,
        timezone=data.timezone,
        condition=data.condition,
        check_interval=data.check_interval,
        groups=data.groups,
        accounts=data.accounts,
        rotation=data.rotation,
        rotation_strategy=data.rotation_strategy,
        message_template=data.message_template,
        template_variables=data.template_variables,
        media_path=data.media_path,
        delay_min=data.delay_min,
        delay_max=data.delay_max,
        retry_times=data.retry_times,
        retry_interval=data.retry_interval,
        description=data.description,
        created_by=current_user.email
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    invalidate_cache("scheduled_messages")
    logger.info(f"用戶 {current_user.email} 創建了定時消息任務: {data.task_id}")
    
    return task


@router.get("", response_model=List[ScheduledMessageResponse])
@cached(ttl=30, key_prefix="scheduled_messages")  # 定時消息任務狀態可能變化，使用較短的緩存時間
@monitor_query_performance(threshold=1.0)
async def list_scheduled_messages(
    enabled: Optional[bool] = Query(None, description="篩選啟用狀態"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """獲取定時消息任務列表"""
    query = db.query(ScheduledMessageTask)
    
    if enabled is not None:
        query = query.filter(ScheduledMessageTask.enabled == enabled)
    
    tasks = query.order_by(desc(ScheduledMessageTask.created_at)).offset(skip).limit(limit).all()
    
    return tasks


@router.get("/{task_id}", response_model=ScheduledMessageResponse)
async def get_scheduled_message(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """獲取單個定時消息任務"""
    task = db.query(ScheduledMessageTask).filter(
        ScheduledMessageTask.task_id == task_id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任務 {task_id} 不存在"
        )
    
    return task


@router.put("/{task_id}", response_model=ScheduledMessageResponse)
@check_permission(PermissionCode.GROUP_AI_MANAGE)
async def update_scheduled_message(
    task_id: str,
    data: ScheduledMessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新定時消息任務"""
    task = db.query(ScheduledMessageTask).filter(
        ScheduledMessageTask.task_id == task_id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任務 {task_id} 不存在"
        )
    
    # 更新字段
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    task.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    
    invalidate_cache("scheduled_messages")
    logger.info(f"用戶 {current_user.email} 更新了定時消息任務: {task_id}")
    
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
@check_permission(PermissionCode.GROUP_AI_MANAGE)
async def delete_scheduled_message(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """刪除定時消息任務"""
    task = db.query(ScheduledMessageTask).filter(
        ScheduledMessageTask.task_id == task_id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任務 {task_id} 不存在"
        )
    
    db.delete(task)
    db.commit()
    
    invalidate_cache("scheduled_messages")
    logger.info(f"用戶 {current_user.email} 刪除了定時消息任務: {task_id}")
    
    return None


@router.get("/{task_id}/logs", response_model=List[ScheduledMessageLogResponse])
async def get_scheduled_message_logs(
    task_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """獲取定時消息任務執行日誌"""
    logs = db.query(ScheduledMessageLog).filter(
        ScheduledMessageLog.task_id == task_id
    ).order_by(desc(ScheduledMessageLog.executed_at)).offset(skip).limit(limit).all()
    
    return logs
