"""
数据统计 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel

from app.db import get_db_session
from app.crud import sites as crud_sites
from app.models.sites import SiteVisit, AIConversation, ContactForm

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/overview")
async def get_analytics_overview(
    days: int = Query(7, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db_session)
):
    """获取概览数据"""
    try:
        overview = crud_sites.get_analytics_overview(db, days=days)
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取概览数据失败: {str(e)}")


@router.get("/visits")
async def get_visits(
    site_id: Optional[int] = Query(None, description="站点 ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db_session)
):
    """获取访问记录"""
    try:
        skip = (page - 1) * page_size
        
        query = db.query(SiteVisit)
        
        if site_id:
            query = query.filter(SiteVisit.site_id == site_id)
        
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.filter(SiteVisit.created_at >= start_datetime)
        
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(SiteVisit.created_at <= end_datetime)
        
        total = query.count()
        visits = query.order_by(SiteVisit.created_at.desc()).offset(skip).limit(page_size).all()
        
        items = []
        for visit in visits:
            items.append({
                "id": visit.id,
                "site_id": visit.site_id,
                "ip_address": visit.ip_address,
                "user_agent": visit.user_agent,
                "referer": visit.referer,
                "page_path": visit.page_path,
                "session_id": visit.session_id,
                "visit_duration": visit.visit_duration,
                "created_at": visit.created_at.isoformat()
            })
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取访问记录失败: {str(e)}")


@router.get("/conversations")
async def get_conversations(
    site_id: Optional[int] = Query(None, description="站点 ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db_session)
):
    """获取对话记录"""
    try:
        skip = (page - 1) * page_size
        
        query = db.query(AIConversation)
        
        if site_id:
            query = query.filter(AIConversation.site_id == site_id)
        
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.filter(AIConversation.created_at >= start_datetime)
        
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(AIConversation.created_at <= end_datetime)
        
        total = query.count()
        conversations = query.order_by(AIConversation.created_at.desc()).offset(skip).limit(page_size).all()
        
        items = []
        for conv in conversations:
            items.append({
                "id": conv.id,
                "site_id": conv.site_id,
                "session_id": conv.session_id,
                "user_message": conv.user_message,
                "ai_response": conv.ai_response,
                "ai_provider": conv.ai_provider,
                "response_time": conv.response_time,
                "tokens_used": conv.tokens_used,
                "created_at": conv.created_at.isoformat()
            })
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话记录失败: {str(e)}")


@router.get("/conversations/stats")
async def get_conversation_stats(
    days: int = Query(7, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db_session)
):
    """获取对话统计"""
    try:
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 总对话数
        total = db.query(func.count(AIConversation.id)).filter(
            AIConversation.created_at >= start_date
        ).scalar() or 0
        
        # 按提供商统计
        by_provider = {}
        provider_stats = db.query(
            AIConversation.ai_provider,
            func.count(AIConversation.id).label('count')
        ).filter(
            AIConversation.created_at >= start_date
        ).group_by(AIConversation.ai_provider).all()
        
        for provider, count in provider_stats:
            if provider:
                by_provider[provider] = count
        
        # 平均响应时间
        avg_response_time = db.query(func.avg(AIConversation.response_time)).filter(
            AIConversation.created_at >= start_date
        ).scalar()
        avg_response_time = int(avg_response_time) if avg_response_time else 0
        
        # 平均 Token 数
        avg_tokens = db.query(func.avg(AIConversation.tokens_used)).filter(
            AIConversation.created_at >= start_date
        ).scalar()
        avg_tokens = int(avg_tokens) if avg_tokens else 0
        
        # 常用问题（简化版，实际可以更复杂）
        top_questions = []
        
        return {
            "total": total,
            "by_provider": by_provider,
            "avg_response_time": avg_response_time,
            "avg_tokens": avg_tokens,
            "top_questions": top_questions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话统计失败: {str(e)}")

