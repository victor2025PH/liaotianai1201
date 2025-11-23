"""
告警規則 CRUD 操作
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.group_ai import GroupAIAlertRule
from app.schemas.alert_rule import AlertRuleCreate, AlertRuleUpdate


def create_alert_rule(db: Session, *, rule: AlertRuleCreate, created_by: Optional[str] = None) -> GroupAIAlertRule:
    """創建告警規則"""
    db_rule = GroupAIAlertRule(
        name=rule.name,
        rule_type=rule.rule_type,
        alert_level=rule.alert_level,
        threshold_value=rule.threshold_value,
        threshold_operator=rule.threshold_operator,
        enabled=rule.enabled,
        notification_method=rule.notification_method,
        notification_target=rule.notification_target,
        rule_conditions=rule.rule_conditions,
        description=rule.description,
        created_by=created_by
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


def get_alert_rule(db: Session, *, rule_id: str) -> Optional[GroupAIAlertRule]:
    """根據 ID 獲取告警規則"""
    return db.query(GroupAIAlertRule).filter(GroupAIAlertRule.id == rule_id).first()


def get_alert_rule_by_name(db: Session, *, name: str) -> Optional[GroupAIAlertRule]:
    """根據名稱獲取告警規則"""
    return db.query(GroupAIAlertRule).filter(GroupAIAlertRule.name == name).first()


def list_alert_rules(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    enabled: Optional[bool] = None,
    rule_type: Optional[str] = None
) -> tuple[List[GroupAIAlertRule], int]:
    """列出告警規則"""
    query = db.query(GroupAIAlertRule)
    
    if enabled is not None:
        query = query.filter(GroupAIAlertRule.enabled == enabled)
    
    if rule_type:
        query = query.filter(GroupAIAlertRule.rule_type == rule_type)
    
    total = query.count()
    rules = query.order_by(GroupAIAlertRule.created_at.desc()).offset(skip).limit(limit).all()
    
    return rules, total


def get_enabled_alert_rules(db: Session, *, rule_type: Optional[str] = None) -> List[GroupAIAlertRule]:
    """獲取所有啟用的告警規則"""
    query = db.query(GroupAIAlertRule).filter(GroupAIAlertRule.enabled == True)
    
    if rule_type:
        query = query.filter(GroupAIAlertRule.rule_type == rule_type)
    
    return query.all()


def update_alert_rule(db: Session, *, rule_id: str, rule_update: AlertRuleUpdate) -> Optional[GroupAIAlertRule]:
    """更新告警規則"""
    db_rule = get_alert_rule(db, rule_id=rule_id)
    if not db_rule:
        return None
    
    update_data = rule_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rule, key, value)
    
    db.commit()
    db.refresh(db_rule)
    return db_rule


def delete_alert_rule(db: Session, *, rule_id: str) -> bool:
    """刪除告警規則"""
    db_rule = get_alert_rule(db, rule_id=rule_id)
    if not db_rule:
        return False
    
    db.delete(db_rule)
    db.commit()
    return True

