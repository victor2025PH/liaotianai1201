"""
AI 使用统计 CRUD 操作
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
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
) -> AIUsageLog:
    """创建使用日志"""
    request_id = str(uuid.uuid4())
    
    log = AIUsageLog(
        request_id=request_id,
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


def update_daily_stats(db: Session, log: AIUsageLog):
    """更新每日统计"""
    stat_date = log.created_at.date()
    
    # 查找或创建统计记录
    stats = db.query(AIUsageStats).filter(
        AIUsageStats.stat_date == stat_date,
        AIUsageStats.provider == log.provider,
        AIUsageStats.model == log.model,
        AIUsageStats.site_domain == (log.site_domain or None)
    ).first()
    
    if stats:
        # 更新现有统计
        stats.total_requests += 1
        if log.status == "success":
            stats.success_requests += 1
        else:
            stats.error_requests += 1
        stats.total_prompt_tokens += log.prompt_tokens
        stats.total_completion_tokens += log.completion_tokens
        stats.total_tokens += log.total_tokens
        stats.total_cost += log.estimated_cost
        stats.updated_at = datetime.utcnow()
    else:
        # 创建新统计
        stats = AIUsageStats(
            stat_date=stat_date,
            provider=log.provider,
            model=log.model,
            site_domain=log.site_domain,
            total_requests=1,
            success_requests=1 if log.status == "success" else 0,
            error_requests=0 if log.status == "success" else 1,
            total_prompt_tokens=log.prompt_tokens,
            total_completion_tokens=log.completion_tokens,
            total_tokens=log.total_tokens,
            total_cost=log.estimated_cost,
        )
        db.add(stats)
    
    db.commit()


def calculate_cost(provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """计算 API 调用成本（美元）"""
    # 价格表（每 1000 tokens，美元）
    pricing = {
        "openai": {
            "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},  # 每 1M tokens
            "gpt-4o": {"prompt": 2.50, "completion": 10.00},
            "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
        },
        "gemini": {
            "gemini-2.5-flash-latest": {"prompt": 0.075, "completion": 0.30},  # 每 1M tokens
            "gemini-pro": {"prompt": 0.50, "completion": 1.50},
        }
    }
    
    if provider in pricing and model in pricing[provider]:
        model_pricing = pricing[provider][model]
        prompt_cost = (prompt_tokens / 1_000_000) * model_pricing["prompt"]
        completion_cost = (completion_tokens / 1_000_000) * model_pricing["completion"]
        return prompt_cost + completion_cost
    
    return 0.0

