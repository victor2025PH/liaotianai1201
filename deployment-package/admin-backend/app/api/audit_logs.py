"""
審計日誌查詢 API
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_current_active_user, get_db_session
from app.models.user import User
from app.middleware.permission import check_permission
from app.core.permissions import PermissionCode
from app.crud.audit_log import get_audit_logs, get_audit_log_by_id
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


# ============ 響應模型 ============

class AuditLogRead(BaseModel):
    """審計日誌讀取模型"""
    id: int
    user_id: int
    user_email: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    description: Optional[str] = None
    before_state: Optional[dict] = None
    after_state: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """審計日誌列表響應"""
    items: List[AuditLogRead]
    total: int
    skip: int
    limit: int


# ============ API 端點 ============

@router.get("/", response_model=AuditLogListResponse)
async def list_audit_logs(
    skip: int = Query(0, ge=0, description="跳過記錄數"),
    limit: int = Query(100, ge=1, le=1000, description="返回記錄數"),
    user_id: Optional[int] = Query(None, description="用戶 ID"),
    action: Optional[str] = Query(None, description="操作類型"),
    resource_type: Optional[str] = Query(None, description="資源類型"),
    resource_id: Optional[str] = Query(None, description="資源 ID"),
    start_date: Optional[datetime] = Query(None, description="開始時間"),
    end_date: Optional[datetime] = Query(None, description="結束時間"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """查詢審計日誌（需要 audit:view 權限）"""
    check_permission(current_user, PermissionCode.AUDIT_VIEW.value, db)
    
    try:
        logs, total = get_audit_logs(
            db,
            skip=skip,
            limit=limit,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        return AuditLogListResponse(
            items=[AuditLogRead.model_validate(log) for log in logs],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"查詢審計日誌失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢審計日誌失敗: {str(e)}"
        )


@router.get("/{log_id}", response_model=AuditLogRead)
async def get_audit_log(
    log_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """獲取審計日誌詳情（需要 audit:view 權限）"""
    check_permission(current_user, PermissionCode.AUDIT_VIEW.value, db)
    
    try:
        log = get_audit_log_by_id(db, log_id=log_id)
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"審計日誌 {log_id} 不存在"
            )
        
        return AuditLogRead.model_validate(log)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取審計日誌失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取審計日誌失敗: {str(e)}"
        )

