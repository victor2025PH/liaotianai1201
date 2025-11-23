"""
告警規則管理 API
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.crud import alert_rule as crud_alert_rule
from app.schemas.alert_rule import (
    AlertRule,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleList
)

router = APIRouter()


@router.post("/", response_model=AlertRule, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    rule: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """創建告警規則"""
    # 檢查規則名稱是否已存在
    existing_rule = crud_alert_rule.get_alert_rule_by_name(db, name=rule.name)
    if existing_rule:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"告警規則名稱 '{rule.name}' 已存在"
        )
    
    db_rule = crud_alert_rule.create_alert_rule(
        db,
        rule=rule,
        created_by=current_user.email if current_user else "system"
    )
    return db_rule


@router.get("/", response_model=AlertRuleList)
async def list_alert_rules(
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁數量"),
    enabled: Optional[bool] = Query(None, description="是否啟用"),
    rule_type: Optional[str] = Query(None, description="規則類型"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """列出告警規則"""
    skip = (page - 1) * page_size
    rules, total = crud_alert_rule.list_alert_rules(
        db,
        skip=skip,
        limit=page_size,
        enabled=enabled,
        rule_type=rule_type
    )
    return AlertRuleList(items=rules, total=total)


@router.get("/{rule_id}", response_model=AlertRule)
async def get_alert_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """獲取告警規則詳情"""
    rule = crud_alert_rule.get_alert_rule(db, rule_id=rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"告警規則 {rule_id} 不存在"
        )
    return rule


@router.put("/{rule_id}", response_model=AlertRule)
async def update_alert_rule(
    rule_id: str,
    rule_update: AlertRuleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """更新告警規則"""
    # 如果更新名稱，檢查是否與其他規則衝突
    if rule_update.name:
        existing_rule = crud_alert_rule.get_alert_rule_by_name(db, name=rule_update.name)
        if existing_rule and existing_rule.id != rule_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"告警規則名稱 '{rule_update.name}' 已存在"
            )
    
    rule = crud_alert_rule.update_alert_rule(db, rule_id=rule_id, rule_update=rule_update)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"告警規則 {rule_id} 不存在"
        )
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """刪除告警規則"""
    success = crud_alert_rule.delete_alert_rule(db, rule_id=rule_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"告警規則 {rule_id} 不存在"
        )


@router.post("/{rule_id}/enable", response_model=AlertRule)
async def enable_alert_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """啟用告警規則"""
    rule = crud_alert_rule.update_alert_rule(
        db,
        rule_id=rule_id,
        rule_update=AlertRuleUpdate(enabled=True)
    )
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"告警規則 {rule_id} 不存在"
        )
    return rule


@router.post("/{rule_id}/disable", response_model=AlertRule)
async def disable_alert_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """禁用告警規則"""
    rule = crud_alert_rule.update_alert_rule(
        db,
        rule_id=rule_id,
        rule_update=AlertRuleUpdate(enabled=False)
    )
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"告警規則 {rule_id} 不存在"
        )
    return rule

