"""
告警管理 API
提供告警聚合、去重、级别管理、静默功能
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.services.alert_aggregator import (
    get_alert_aggregator,
    AlertSeverity,
    AlertStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alert-management"])


class AlertSuppressRequest(BaseModel):
    """告警静默请求"""
    duration_seconds: int = 3600  # 默认1小时
    reason: Optional[str] = None


class AlertAcknowledgeRequest(BaseModel):
    """告警确认请求"""
    acknowledged_by: str


class AlertStatisticsResponse(BaseModel):
    """告警统计响应"""
    total_alerts: int
    deduplicated: int
    aggregated: int
    suppressed: int
    resolved: int
    active_by_severity: dict
    total_by_severity: dict
    total_active: int
    total_aggregated: int


@router.get("/statistics", response_model=AlertStatisticsResponse)
async def get_alert_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取告警统计信息"""
    try:
        aggregator = get_alert_aggregator()
        stats = aggregator.get_alert_statistics()
        return AlertStatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"获取告警统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取告警统计失败: {str(e)}"
        )


@router.post("/{alert_key}/suppress", status_code=status.HTTP_200_OK)
async def suppress_alert(
    alert_key: str,
    request: AlertSuppressRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """静默告警（抑制一段时间）"""
    try:
        aggregator = get_alert_aggregator()
        success = aggregator.suppress_alert(
            alert_key=alert_key,
            duration_seconds=request.duration_seconds,
            reason=request.reason or f"由 {current_user.email} 静默"
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"告警 {alert_key} 不存在"
            )
        
        return {
            "message": "告警已静默",
            "alert_key": alert_key,
            "suppressed_until": (
                datetime.now().timestamp() + request.duration_seconds
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"静默告警失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"静默告警失败: {str(e)}"
        )


@router.post("/{alert_key}/acknowledge", status_code=status.HTTP_200_OK)
async def acknowledge_alert(
    alert_key: str,
    request: AlertAcknowledgeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """确认告警"""
    try:
        aggregator = get_alert_aggregator()
        acknowledged_by = request.acknowledged_by or current_user.email
        success = aggregator.acknowledge_alert(
            alert_key=alert_key,
            acknowledged_by=acknowledged_by
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"告警 {alert_key} 不存在"
            )
        
        return {
            "message": "告警已确认",
            "alert_key": alert_key,
            "acknowledged_by": acknowledged_by
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认告警失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"确认告警失败: {str(e)}"
        )


@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_old_alerts(
    max_age_hours: int = Query(24, ge=1, le=168, description="最大保留时间（小时）"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """清理旧告警"""
    try:
        aggregator = get_alert_aggregator()
        aggregator.cleanup_old_alerts(max_age_hours=max_age_hours)
        
        return {
            "message": "旧告警已清理",
            "max_age_hours": max_age_hours
        }
    except Exception as e:
        logger.error(f"清理旧告警失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理旧告警失败: {str(e)}"
        )

