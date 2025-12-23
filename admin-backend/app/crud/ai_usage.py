"""
AI 使用统计 CRUD 操作
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict
import uuid

from app.models.ai_usage import AIUsageLog, AIUsageStats


def create_usage_log(
    db: Session,
    provider: str,
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    estimated_cost: float = 0.0,
    status: str = "success",
    error_message: Optional[str] = None,
    user_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    site_domain: Optional[str] = None,
    session_id: Optional[str] = None,
) -> AIUsageLog:
    """创建使用日志"""
    request_id = str(uuid.uuid4())
    
    log = AIUsageLog(
        request_id=request_id,
        session_id=session_id,
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost=estimated_cost,
        status=status,
        error_message=error_message,
        user_ip=user_ip,
        user_agent=user_agent,
        site_domain=site_domain,
    )
    
    db.add(log)
    db.commit()
    db.refresh(log)
    
    # 更新每日统计
    update_daily_stats(db, log)
    
    return log


def update_daily_stats(db: Session, log: AIUsageLog) -> None:
    """更新每日统计"""
    today = date.today()
    
    stats = db.query(AIUsageStats).filter(AIUsageStats.stat_date == today).first()
    
    if not stats:
        stats = AIUsageStats(
            stat_date=today,
            total_requests=0,
            total_tokens=0,
            total_cost=0.0,
            requests_by_provider={},
            tokens_by_provider={},
            cost_by_provider={},
            requests_by_model={},
            tokens_by_model={},
            cost_by_model={},
        )
        db.add(stats)
    
    # 更新统计
    stats.total_requests += 1
    stats.total_tokens += log.total_tokens
    stats.total_cost += log.estimated_cost
    
    # 按提供商统计
    if log.provider not in stats.requests_by_provider:
        stats.requests_by_provider[log.provider] = 0
        stats.tokens_by_provider[log.provider] = 0
        stats.cost_by_provider[log.provider] = 0.0
    
    stats.requests_by_provider[log.provider] += 1
    stats.tokens_by_provider[log.provider] += log.total_tokens
    stats.cost_by_provider[log.provider] += log.estimated_cost
    
    # 按模型统计
    if log.model not in stats.requests_by_model:
        stats.requests_by_model[log.model] = 0
        stats.tokens_by_model[log.model] = 0
        stats.cost_by_model[log.model] = 0.0
    
    stats.requests_by_model[log.model] += 1
    stats.tokens_by_model[log.model] += log.total_tokens
    stats.cost_by_model[log.model] += log.estimated_cost
    
    db.commit()


def get_daily_stats(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[AIUsageStats]:
    """获取每日统计"""
    query = db.query(AIUsageStats)
    
    if start_date:
        query = query.filter(AIUsageStats.stat_date >= start_date)
    if end_date:
        query = query.filter(AIUsageStats.stat_date <= end_date)
    
    return query.order_by(AIUsageStats.stat_date.desc()).all()


def get_provider_stats(
    db: Session,
    provider: Optional[str] = None,
    days: int = 7,
) -> Dict:
    """获取提供商统计"""
    start_date = date.today() - timedelta(days=days)
    
    query = db.query(AIUsageLog).filter(AIUsageLog.created_at >= start_date)
    
    if provider:
        query = query.filter(AIUsageLog.provider == provider)
    
    logs = query.all()
    
    stats = {
        'total_requests': len(logs),
        'total_tokens': sum(log.total_tokens for log in logs),
        'total_cost': sum(log.estimated_cost for log in logs),
        'success_count': len([log for log in logs if log.status == 'success']),
        'error_count': len([log for log in logs if log.status == 'error']),
    }
    
    return stats


def get_session_stats(
    db: Session,
    session_id: str,
    days: int = 30,
) -> Dict:
    """获取会话统计"""
    start_date = datetime.now() - timedelta(days=days)
    
    logs = db.query(AIUsageLog).filter(
        and_(
            AIUsageLog.session_id == session_id,
            AIUsageLog.created_at >= start_date
        )
    ).all()
    
    stats = {
        'session_id': session_id,
        'total_requests': len(logs),
        'total_tokens': sum(log.total_tokens for log in logs),
        'total_cost': sum(log.estimated_cost for log in logs),
        'requests_by_provider': {},
        'requests_by_model': {},
        'first_request': min([log.created_at for log in logs]) if logs else None,
        'last_request': max([log.created_at for log in logs]) if logs else None,
    }
    
    # 按提供商统计
    for log in logs:
        if log.provider not in stats['requests_by_provider']:
            stats['requests_by_provider'][log.provider] = 0
        stats['requests_by_provider'][log.provider] += 1
    
    # 按模型统计
    for log in logs:
        if log.model not in stats['requests_by_model']:
            stats['requests_by_model'][log.model] = 0
        stats['requests_by_model'][log.model] += 1
    
    return stats


def get_recent_errors(
    db: Session,
    limit: int = 10,
) -> List[AIUsageLog]:
    """获取最近的错误日志"""
    return db.query(AIUsageLog).filter(
        AIUsageLog.status == 'error'
    ).order_by(
        AIUsageLog.created_at.desc()
    ).limit(limit).all()


def get_active_sessions(
    db: Session,
    days: int = 7,
    limit: int = 50,
) -> List[Dict]:
    """获取活跃会话列表"""
    start_date = datetime.now() - timedelta(days=days)
    
    # 查询有会话 ID 的日志，按会话分组
    from sqlalchemy import distinct
    
    sessions = db.query(
        AIUsageLog.session_id,
        func.count(AIUsageLog.id).label('request_count'),
        func.sum(AIUsageLog.total_tokens).label('total_tokens'),
        func.sum(AIUsageLog.estimated_cost).label('total_cost'),
        func.min(AIUsageLog.created_at).label('first_request'),
        func.max(AIUsageLog.created_at).label('last_request'),
    ).filter(
        and_(
            AIUsageLog.session_id.isnot(None),
            AIUsageLog.session_id != '',
            AIUsageLog.created_at >= start_date
        )
    ).group_by(
        AIUsageLog.session_id
    ).order_by(
        func.max(AIUsageLog.created_at).desc()
    ).limit(limit).all()
    
    result = []
    for session in sessions:
        result.append({
            'session_id': session.session_id,
            'request_count': session.request_count,
            'total_tokens': session.total_tokens or 0,
            'total_cost': float(session.total_cost or 0.0),
            'first_request': session.first_request.isoformat() if session.first_request else None,
            'last_request': session.last_request.isoformat() if session.last_request else None,
        })
    
    return result


def calculate_cost(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """计算成本（美元）"""
    # 价格表（每 1000 tokens，美元）
    pricing = {
        'openai': {
            'gpt-4o-mini': {'prompt': 0.00015, 'completion': 0.0006},
            'gpt-4o': {'prompt': 0.005, 'completion': 0.015},
            'gpt-4-turbo': {'prompt': 0.01, 'completion': 0.03},
        },
        'gemini': {
            'gemini-2.5-flash-latest': {'prompt': 0.0, 'completion': 0.0},  # 免费
            'gemini-pro': {'prompt': 0.0, 'completion': 0.0},  # 免费
        },
    }
    
    provider_pricing = pricing.get(provider, {})
    model_pricing = provider_pricing.get(model, {'prompt': 0.0, 'completion': 0.0})
    
    prompt_cost = (prompt_tokens / 1000.0) * model_pricing['prompt']
    completion_cost = (completion_tokens / 1000.0) * model_pricing['completion']
    
    return prompt_cost + completion_cost
