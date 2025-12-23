"""
AI 监控和管理 API
提供使用统计、监控和成本分析功能
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.api.deps import get_db_session
from app.models.ai_usage import AIUsageLog, AIUsageStats
from app.core.config import get_settings
from app.crud.ai_usage import get_session_stats, get_active_sessions
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-monitoring", tags=["ai-monitoring"])


class UsageSummary(BaseModel):
    """使用摘要"""
    total_requests: int
    total_tokens: int
    total_cost: float
    requests_by_provider: Dict[str, int]
    requests_by_site: Dict[str, int]
    requests_by_model: Dict[str, int]
    success_rate: float
    period_start: datetime
    period_end: datetime


class DailyStats(BaseModel):
    """每日统计"""
    date: str
    total_requests: int
    total_tokens: int
    total_cost: float
    success_requests: int
    error_requests: int


class ProviderStats(BaseModel):
    """提供商统计"""
    provider: str
    total_requests: int
    total_tokens: int
    total_cost: float
    success_rate: float
    avg_tokens_per_request: float


@router.get("/summary", response_model=UsageSummary)
async def get_usage_summary(
    days: int = Query(7, description="统计天数"),
    site_domain: Optional[str] = Query(None, description="筛选网站域名"),
    db: Session = Depends(get_db_session)
):
    """
    获取使用摘要
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 构建查询
        query = db.query(AIUsageLog).filter(
            AIUsageLog.created_at >= start_date,
            AIUsageLog.created_at <= end_date
        )
        
        if site_domain:
            query = query.filter(AIUsageLog.site_domain == site_domain)
        
        logs = query.all()
        
        # 计算统计
        total_requests = len(logs)
        total_tokens = sum(log.total_tokens for log in logs)
        total_cost = sum(log.estimated_cost for log in logs)
        
        # 按提供商统计
        requests_by_provider: Dict[str, int] = {}
        for log in logs:
            requests_by_provider[log.provider] = requests_by_provider.get(log.provider, 0) + 1
        
        # 按网站统计
        requests_by_site: Dict[str, int] = {}
        for log in logs:
            site = log.site_domain or "unknown"
            requests_by_site[site] = requests_by_site.get(site, 0) + 1
        
        # 按模型统计
        requests_by_model: Dict[str, int] = {}
        for log in logs:
            requests_by_model[log.model] = requests_by_model.get(log.model, 0) + 1
        
        # 成功率
        success_count = sum(1 for log in logs if log.status == "success")
        success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0
        
        return UsageSummary(
            total_requests=total_requests,
            total_tokens=total_tokens,
            total_cost=total_cost,
            requests_by_provider=requests_by_provider,
            requests_by_site=requests_by_site,
            requests_by_model=requests_by_model,
            success_rate=round(success_rate, 2),
            period_start=start_date,
            period_end=end_date
        )
        
    except Exception as e:
        logger.error(f"获取使用摘要失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取使用摘要失败: {str(e)}")


@router.get("/daily", response_model=List[DailyStats])
async def get_daily_stats(
    days: int = Query(7, description="统计天数"),
    site_domain: Optional[str] = Query(None, description="筛选网站域名"),
    db: Session = Depends(get_db_session)
):
    """
    获取每日统计
    """
    try:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # 构建查询
        query = db.query(
            func.date(AIUsageLog.created_at).label('date'),
            func.count(AIUsageLog.id).label('total_requests'),
            func.sum(AIUsageLog.total_tokens).label('total_tokens'),
            func.sum(AIUsageLog.estimated_cost).label('total_cost'),
            func.sum(func.case((AIUsageLog.status == "success", 1), else_=0)).label('success_requests'),
            func.sum(func.case((AIUsageLog.status == "error", 1), else_=0)).label('error_requests'),
        ).filter(
            func.date(AIUsageLog.created_at) >= start_date,
            func.date(AIUsageLog.created_at) <= end_date
        )
        
        if site_domain:
            query = query.filter(AIUsageLog.site_domain == site_domain)
        
        results = query.group_by(func.date(AIUsageLog.created_at)).order_by('date').all()
        
        stats = []
        for row in results:
            stats.append(DailyStats(
                date=row.date.isoformat(),
                total_requests=row.total_requests or 0,
                total_tokens=row.total_tokens or 0,
                total_cost=row.total_cost or 0.0,
                success_requests=row.success_requests or 0,
                error_requests=row.error_requests or 0
            ))
        
        return stats
        
    except Exception as e:
        logger.error(f"获取每日统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取每日统计失败: {str(e)}")


@router.get("/providers", response_model=List[ProviderStats])
async def get_provider_stats(
    days: int = Query(7, description="统计天数"),
    db: Session = Depends(get_db_session)
):
    """
    获取提供商统计
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 按提供商分组统计
        results = db.query(
            AIUsageLog.provider,
            func.count(AIUsageLog.id).label('total_requests'),
            func.sum(AIUsageLog.total_tokens).label('total_tokens'),
            func.sum(AIUsageLog.estimated_cost).label('total_cost'),
            func.sum(func.case((AIUsageLog.status == "success", 1), else_=0)).label('success_count'),
        ).filter(
            AIUsageLog.created_at >= start_date,
            AIUsageLog.created_at <= end_date
        ).group_by(AIUsageLog.provider).all()
        
        stats = []
        for row in results:
            success_rate = (row.success_count / row.total_requests * 100) if row.total_requests > 0 else 0
            avg_tokens = (row.total_tokens / row.total_requests) if row.total_requests > 0 else 0
            
            stats.append(ProviderStats(
                provider=row.provider,
                total_requests=row.total_requests or 0,
                total_tokens=row.total_tokens or 0,
                total_cost=row.total_cost or 0.0,
                success_rate=round(success_rate, 2),
                avg_tokens_per_request=round(avg_tokens, 2)
            ))
        
        return stats
        
    except Exception as e:
        logger.error(f"获取提供商统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取提供商统计失败: {str(e)}")


@router.get("/recent-errors")
async def get_recent_errors(
    limit: int = Query(50, description="返回数量"),
    db: Session = Depends(get_db_session)
):
    """
    获取最近的错误日志
    """
    try:
        errors = db.query(AIUsageLog).filter(
            AIUsageLog.status == "error"
        ).order_by(
            AIUsageLog.created_at.desc()
        ).limit(limit).all()
        
        return [
            {
                "id": error.id,
                "provider": error.provider,
                "model": error.model,
                "site_domain": error.site_domain,
                "error_message": error.error_message,
                "created_at": error.created_at.isoformat(),
            }
            for error in errors
        ]
        
    except Exception as e:
        logger.error(f"获取错误日志失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取错误日志失败: {str(e)}")


@router.get("/session/{session_id}")
async def get_session_statistics(
    session_id: str,
    days: int = Query(30, description="统计天数"),
    db: Session = Depends(get_db_session)
):
    """
    获取指定会话的统计信息
    """
    try:
        stats = get_session_stats(db, session_id, days=days)
        return stats
    except Exception as e:
        logger.error(f"获取会话统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取会话统计失败: {str(e)}")


@router.get("/sessions/active")
async def get_active_sessions_list(
    days: int = Query(7, description="查询天数"),
    limit: int = Query(50, description="返回数量"),
    db: Session = Depends(get_db_session)
):
    """
    获取活跃会话列表
    """
    try:
        sessions = get_active_sessions(db, days=days, limit=limit)
        return {
            "total": len(sessions),
            "sessions": sessions
        }
    except Exception as e:
        logger.error(f"获取活跃会话列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取活跃会话列表失败: {str(e)}")

