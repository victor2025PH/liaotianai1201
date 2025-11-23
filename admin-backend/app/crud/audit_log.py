"""
審計日誌 CRUD 操作
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    *,
    user_id: int,
    user_email: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    description: Optional[str] = None,
    before_state: Optional[Dict[str, Any]] = None,
    after_state: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """創建審計日誌"""
    audit_log = AuditLog(
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        before_state=before_state,
        after_state=after_state,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def get_audit_logs(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> tuple[List[AuditLog], int]:
    """查詢審計日誌"""
    query = db.query(AuditLog)
    
    # 構建查詢條件
    conditions = []
    
    if user_id is not None:
        conditions.append(AuditLog.user_id == user_id)
    
    if action:
        conditions.append(AuditLog.action == action)
    
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    
    if resource_id:
        conditions.append(AuditLog.resource_id == resource_id)
    
    if start_date:
        conditions.append(AuditLog.created_at >= start_date)
    
    if end_date:
        conditions.append(AuditLog.created_at <= end_date)
    
    if conditions:
        query = query.filter(and_(*conditions))
    
    # 獲取總數
    total = query.count()
    
    # 排序和分頁
    logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
    
    return logs, total


def get_audit_log_by_id(db: Session, *, log_id: int) -> Optional[AuditLog]:
    """根據 ID 獲取審計日誌"""
    return db.query(AuditLog).filter(AuditLog.id == log_id).first()

