"""
關鍵詞觸發規則管理 API
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db import get_db
from app.models.unified_features import KeywordTriggerRule
from app.api.deps import get_current_active_user
from app.middleware.permission import check_permission, check_permission_decorator, check_permission_decorator
from app.core.permissions import PermissionCode
from app.models.user import User
from app.core.cache import cached, invalidate_cache
from app.core.db_optimization import monitor_query_performance

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/keyword-triggers", tags=["Keyword Triggers"])


# ============ 請求/響應模型 ============

class KeywordTriggerCreate(BaseModel):
    """創建關鍵詞觸發規則請求"""
    rule_id: str
    name: str
    enabled: bool = True
    keywords: List[str] = []
    pattern: Optional[str] = None
    match_type: str = "any"  # simple/regex/fuzzy/all/any/context
    case_sensitive: bool = False
    sender_ids: List[int] = []
    sender_blacklist: List[int] = []
    time_range_start: Optional[str] = None
    time_range_end: Optional[str] = None
    weekdays: List[int] = []
    group_ids: List[int] = []
    message_length_min: Optional[int] = None
    message_length_max: Optional[int] = None
    condition_logic: str = "AND"
    actions: List[dict] = []
    priority: int = 0
    context_window: int = 0
    description: Optional[str] = None


class KeywordTriggerUpdate(BaseModel):
    """更新關鍵詞觸發規則請求"""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    keywords: Optional[List[str]] = None
    pattern: Optional[str] = None
    match_type: Optional[str] = None
    case_sensitive: Optional[bool] = None
    sender_ids: Optional[List[int]] = None
    sender_blacklist: Optional[List[int]] = None
    time_range_start: Optional[str] = None
    time_range_end: Optional[str] = None
    weekdays: Optional[List[int]] = None
    group_ids: Optional[List[int]] = None
    message_length_min: Optional[int] = None
    message_length_max: Optional[int] = None
    condition_logic: Optional[str] = None
    actions: Optional[List[dict]] = None
    priority: Optional[int] = None
    context_window: Optional[int] = None
    description: Optional[str] = None


class KeywordTriggerResponse(BaseModel):
    """關鍵詞觸發規則響應"""
    id: str
    rule_id: str
    name: str
    enabled: bool
    keywords: List[str]
    pattern: Optional[str]
    match_type: str
    case_sensitive: bool
    sender_ids: List[int]
    sender_blacklist: List[int]
    time_range_start: Optional[str]
    time_range_end: Optional[str]
    weekdays: List[int]
    group_ids: List[int]
    message_length_min: Optional[int]
    message_length_max: Optional[int]
    condition_logic: str
    actions: List[dict]
    priority: int
    context_window: int
    trigger_count: int
    last_triggered_at: Optional[datetime]
    description: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ API 端點 ============

@router.post("", response_model=KeywordTriggerResponse, status_code=status.HTTP_201_CREATED)
@check_permission_decorator(PermissionCode.GROUP_AI_MANAGE)
async def create_keyword_trigger(
    data: KeywordTriggerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """創建關鍵詞觸發規則"""
    # 檢查 rule_id 是否已存在
    existing = db.query(KeywordTriggerRule).filter(
        KeywordTriggerRule.rule_id == data.rule_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"規則 ID {data.rule_id} 已存在"
        )
    
    # 創建規則
    rule = KeywordTriggerRule(
        rule_id=data.rule_id,
        name=data.name,
        enabled=data.enabled,
        keywords=data.keywords,
        pattern=data.pattern,
        match_type=data.match_type,
        case_sensitive=data.case_sensitive,
        sender_ids=data.sender_ids,
        sender_blacklist=data.sender_blacklist,
        time_range_start=data.time_range_start,
        time_range_end=data.time_range_end,
        weekdays=data.weekdays,
        group_ids=data.group_ids,
        message_length_min=data.message_length_min,
        message_length_max=data.message_length_max,
        condition_logic=data.condition_logic,
        actions=data.actions,
        priority=data.priority,
        context_window=data.context_window,
        description=data.description,
        created_by=current_user.email
    )
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    invalidate_cache("keyword_triggers")
    logger.info(f"用戶 {current_user.email} 創建了關鍵詞觸發規則: {data.rule_id}")
    
    return rule


@router.get("", response_model=List[KeywordTriggerResponse])
@cached(prefix="keyword_triggers", ttl=60)
async def list_keyword_triggers(
    enabled: Optional[bool] = Query(None, description="篩選啟用狀態"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """獲取關鍵詞觸發規則列表"""
    query = db.query(KeywordTriggerRule)
    
    if enabled is not None:
        query = query.filter(KeywordTriggerRule.enabled == enabled)
    
    rules = query.order_by(desc(KeywordTriggerRule.priority), desc(KeywordTriggerRule.created_at)).offset(skip).limit(limit).all()
    
    return rules


@router.get("/{rule_id}", response_model=KeywordTriggerResponse)
async def get_keyword_trigger(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """獲取單個關鍵詞觸發規則"""
    rule = db.query(KeywordTriggerRule).filter(
        KeywordTriggerRule.rule_id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"規則 {rule_id} 不存在"
        )
    
    return rule


@router.put("/{rule_id}", response_model=KeywordTriggerResponse)
@check_permission_decorator(PermissionCode.GROUP_AI_MANAGE)
async def update_keyword_trigger(
    rule_id: str,
    data: KeywordTriggerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新關鍵詞觸發規則"""
    rule = db.query(KeywordTriggerRule).filter(
        KeywordTriggerRule.rule_id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"規則 {rule_id} 不存在"
        )
    
    # 更新字段
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    
    rule.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(rule)
    
    invalidate_cache("keyword_triggers")
    logger.info(f"用戶 {current_user.email} 更新了關鍵詞觸發規則: {rule_id}")
    
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
@check_permission_decorator(PermissionCode.GROUP_AI_MANAGE)
async def delete_keyword_trigger(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """刪除關鍵詞觸發規則"""
    rule = db.query(KeywordTriggerRule).filter(
        KeywordTriggerRule.rule_id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"規則 {rule_id} 不存在"
        )
    
    db.delete(rule)
    db.commit()
    
    invalidate_cache("keyword_triggers")
    logger.info(f"用戶 {current_user.email} 刪除了關鍵詞觸發規則: {rule_id}")
    
    return None
