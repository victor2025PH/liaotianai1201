"""
AI 使用统计模型
用于记录和统计 AI API 调用情况
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Index
from sqlalchemy.sql import func
from app.db import Base


class AIUsageLog(Base):
    """AI 使用日志"""
    __tablename__ = "ai_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    # 请求信息
    request_id = Column(String(100), unique=True, index=True, nullable=False)
    session_id = Column(String(100), index=True)  # 会话 ID
    user_ip = Column(String(50), index=True)
    user_agent = Column(Text)
    site_domain = Column(String(200), index=True)  # 来源网站域名
    
    # AI 信息
    provider = Column(String(50), index=True, nullable=False)  # "gemini" | "openai"
    model = Column(String(100), nullable=False)
    
    # 使用统计
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # 成本估算（美元）
    estimated_cost = Column(Float, default=0.0)
    
    # 请求状态
    status = Column(String(20), default="success")  # "success" | "error"
    error_message = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 索引
    __table_args__ = (
        Index('idx_provider_created', 'provider', 'created_at'),
        Index('idx_site_created', 'site_domain', 'created_at'),
    )


class AIUsageStats(Base):
    """AI 使用统计汇总（每日）"""
    __tablename__ = "ai_usage_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 统计维度
    stat_date = Column(DateTime(timezone=True), index=True, nullable=False)
    provider = Column(String(50), index=True, nullable=False)
    model = Column(String(100), nullable=False)
    site_domain = Column(String(200), index=True, nullable=True)
    
    # 统计数据
    total_requests = Column(Integer, default=0)
    success_requests = Column(Integer, default=0)
    error_requests = Column(Integer, default=0)
    
    total_prompt_tokens = Column(Integer, default=0)
    total_completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # 成本
    total_cost = Column(Float, default=0.0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 唯一索引：确保每天每个 provider+model+site 只有一条记录
    __table_args__ = (
        Index('idx_unique_stat', 'stat_date', 'provider', 'model', 'site_domain', unique=True),
    )

