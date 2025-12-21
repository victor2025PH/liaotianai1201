"""
群組管理增強功能 API
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db import get_db
from app.models.unified_features import GroupJoinConfig, GroupJoinLog, GroupActivityMetrics
from app.api.deps import get_current_active_user
from app.middleware.permission import check_permission, check_permission_decorator
from app.core.permissions import PermissionCode
from app.models.user import User
from app.core.cache import cached, invalidate_cache
from app.core.db_optimization import monitor_query_performance

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/group-management", tags=["Group Management"])


# ============ 請求/響應模型 ============

class GroupJoinConfigCreate(BaseModel):
    """創建群組加入配置請求"""
    config_id: str
    name: str
    enabled: bool = True
    join_type: str = "invite_link"  # invite_link/username/group_id/search
    invite_link: Optional[str] = None
    username: Optional[str] = None
    group_id: Optional[int] = None
    search_keywords: List[str] = []
    account_ids: List[str] = []
    min_members: Optional[int] = None
    max_members: Optional[int] = None
    group_types: List[str] = []
    post_join_actions: List[dict] = []
    priority: int = 0
    description: Optional[str] = None


class GroupJoinConfigUpdate(BaseModel):
    """更新群組加入配置請求"""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    join_type: Optional[str] = None
    invite_link: Optional[str] = None
    username: Optional[str] = None
    group_id: Optional[int] = None
    search_keywords: Optional[List[str]] = None
    account_ids: Optional[List[str]] = None
    min_members: Optional[int] = None
    max_members: Optional[int] = None
    group_types: Optional[List[str]] = None
    post_join_actions: Optional[List[dict]] = None
    priority: Optional[int] = None
    description: Optional[str] = None


class GroupJoinConfigResponse(BaseModel):
    """群組加入配置響應"""
    id: str
    config_id: str
    name: str
    enabled: bool
    join_type: str
    invite_link: Optional[str]
    username: Optional[str]
    group_id: Optional[int]
    search_keywords: List[str]
    account_ids: List[str]
    min_members: Optional[int]
    max_members: Optional[int]
    group_types: List[str]
    post_join_actions: List[dict]
    priority: int
    join_count: int
    last_joined_at: Optional[datetime]
    description: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GroupActivityMetricsResponse(BaseModel):
    """群組活動指標響應"""
    id: str
    group_id: int
    message_count_24h: int
    active_members_24h: int
    new_members_24h: int
    redpacket_count_24h: int
    last_activity: Optional[datetime]
    health_score: float
    recorded_at: datetime
    
    class Config:
        from_attributes = True


# ============ API 端點 ============

@router.post("/join-configs", response_model=GroupJoinConfigResponse, status_code=status.HTTP_201_CREATED)
@check_permission_decorator(PermissionCode.GROUP_AI_MANAGE)
async def create_group_join_config(
    data: GroupJoinConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """創建群組加入配置"""
    # 檢查 config_id 是否已存在
    existing = db.query(GroupJoinConfig).filter(
        GroupJoinConfig.config_id == data.config_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"配置 ID {data.config_id} 已存在"
        )
    
    # 創建配置
    config = GroupJoinConfig(
        config_id=data.config_id,
        name=data.name,
        enabled=data.enabled,
        join_type=data.join_type,
        invite_link=data.invite_link,
        username=data.username,
        group_id=data.group_id,
        search_keywords=data.search_keywords,
        account_ids=data.account_ids,
        min_members=data.min_members,
        max_members=data.max_members,
        group_types=data.group_types,
        post_join_actions=data.post_join_actions,
        priority=data.priority,
        description=data.description,
        created_by=current_user.email
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    invalidate_cache("group_join_configs")
    logger.info(f"用戶 {current_user.email} 創建了群組加入配置: {data.config_id}")
    
    return config


@router.get("/join-configs", response_model=List[GroupJoinConfigResponse])
@cached(ttl=120, key_prefix="group_join_configs")  # 群組加入配置變化不頻繁，使用較長的緩存時間
@monitor_query_performance(threshold=1.0)
async def list_group_join_configs(
    enabled: Optional[bool] = Query(None, description="篩選啟用狀態"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """獲取群組加入配置列表"""
    query = db.query(GroupJoinConfig)
    
    if enabled is not None:
        query = query.filter(GroupJoinConfig.enabled == enabled)
    
    configs = query.order_by(desc(GroupJoinConfig.priority), desc(GroupJoinConfig.created_at)).offset(skip).limit(limit).all()
    
    return configs


@router.get("/join-configs/{config_id}", response_model=GroupJoinConfigResponse)
async def get_group_join_config(
    config_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """獲取單個群組加入配置"""
    config = db.query(GroupJoinConfig).filter(
        GroupJoinConfig.config_id == config_id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置 {config_id} 不存在"
        )
    
    return config


@router.put("/join-configs/{config_id}", response_model=GroupJoinConfigResponse)
@check_permission_decorator(PermissionCode.GROUP_AI_MANAGE)
async def update_group_join_config(
    config_id: str,
    data: GroupJoinConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新群組加入配置"""
    config = db.query(GroupJoinConfig).filter(
        GroupJoinConfig.config_id == config_id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置 {config_id} 不存在"
        )
    
    # 更新字段
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
    
    config.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(config)
    
    invalidate_cache("group_join_configs")
    logger.info(f"用戶 {current_user.email} 更新了群組加入配置: {config_id}")
    
    return config


@router.delete("/join-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
@check_permission_decorator(PermissionCode.GROUP_AI_MANAGE)
async def delete_group_join_config(
    config_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """刪除群組加入配置"""
    config = db.query(GroupJoinConfig).filter(
        GroupJoinConfig.config_id == config_id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置 {config_id} 不存在"
        )
    
    db.delete(config)
    db.commit()
    
    invalidate_cache("group_join_configs")
    logger.info(f"用戶 {current_user.email} 刪除了群組加入配置: {config_id}")
    
    return None


@router.get("/activity-metrics/{group_id}", response_model=List[GroupActivityMetricsResponse])
@cached(ttl=60)  # 群組活動指標需要較實時，使用較短的緩存時間
@monitor_query_performance(threshold=1.0)
async def get_group_activity_metrics(
    group_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """獲取群組活動指標"""
    metrics = db.query(GroupActivityMetrics).filter(
        GroupActivityMetrics.group_id == group_id
    ).order_by(desc(GroupActivityMetrics.recorded_at)).offset(skip).limit(limit).all()
    
    return metrics


@router.post("/activity-metrics", response_model=GroupActivityMetricsResponse, status_code=status.HTTP_201_CREATED)
@check_permission_decorator(PermissionCode.GROUP_AI_MANAGE)
async def create_group_activity_metrics(
    group_id: int,
    message_count_24h: int = 0,
    active_members_24h: int = 0,
    new_members_24h: int = 0,
    redpacket_count_24h: int = 0,
    health_score: float = 0.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """創建群組活動指標記錄"""
    metrics = GroupActivityMetrics(
        group_id=group_id,
        message_count_24h=message_count_24h,
        active_members_24h=active_members_24h,
        new_members_24h=new_members_24h,
        redpacket_count_24h=redpacket_count_24h,
        health_score=health_score,
        last_activity=datetime.utcnow()
    )
    
    db.add(metrics)
    db.commit()
    db.refresh(metrics)
    
    return metrics
