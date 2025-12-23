"""
站点管理相关数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base


class Site(Base):
    """站点表"""
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="站点名称")
    url = Column(String(255), nullable=False, comment="站点 URL")
    site_type = Column(String(50), nullable=False, index=True, comment="站点类型: aizkw/hongbao/tgmini")
    status = Column(String(20), default="active", comment="状态: active/inactive")
    config = Column(JSON, comment="站点配置（JSON）")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    visits = relationship("SiteVisit", back_populates="site", cascade="all, delete-orphan")
    analytics = relationship("SiteAnalytics", back_populates="site", cascade="all, delete-orphan")
    conversations = relationship("AIConversation", back_populates="site", cascade="all, delete-orphan")
    contacts = relationship("ContactForm", back_populates="site", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_sites_site_type', 'site_type'),
    )


class SiteVisit(Base):
    """访问记录表"""
    __tablename__ = "site_visits"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)
    ip_address = Column(String(45), comment="IP 地址")
    user_agent = Column(Text, comment="用户代理")
    referer = Column(String(255), comment="来源")
    page_path = Column(String(255), comment="访问页面")
    session_id = Column(String(100), index=True, comment="会话 ID")
    visit_duration = Column(Integer, comment="访问时长（秒）")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    site = relationship("Site", back_populates="visits")

    __table_args__ = (
        Index('ix_site_visits_site_id_created_at', 'site_id', 'created_at'),
        Index('ix_site_visits_session_id', 'session_id'),
    )


class AIConversation(Base):
    """AI 对话记录表"""
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(100), index=True, comment="会话 ID")
    user_message = Column(Text, comment="用户消息")
    ai_response = Column(Text, comment="AI 回复")
    ai_provider = Column(String(20), comment="AI 提供商: gemini/openai")
    response_time = Column(Integer, comment="响应时间（毫秒）")
    tokens_used = Column(Integer, comment="使用的 Token 数")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    site = relationship("Site", back_populates="conversations")

    __table_args__ = (
        Index('ix_ai_conversations_site_id_created_at', 'site_id', 'created_at'),
        Index('ix_ai_conversations_session_id', 'session_id'),
    )


class ContactForm(Base):
    """联系表单表"""
    __tablename__ = "contact_forms"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_type = Column(String(20), comment="联系方式: telegram/whatsapp/email")
    contact_value = Column(String(255), comment="联系值")
    message = Column(Text, comment="咨询内容")
    status = Column(String(20), default="pending", comment="状态: pending/contacted/converted")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    site = relationship("Site", back_populates="contacts")

    __table_args__ = (
        Index('ix_contact_forms_site_id_created_at', 'site_id', 'created_at'),
        Index('ix_contact_forms_status', 'status'),
    )


class SiteAnalytics(Base):
    """站点统计表（按日汇总）"""
    __tablename__ = "site_analytics"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True, comment="日期")
    pv = Column(Integer, default=0, comment="页面访问量")
    uv = Column(Integer, default=0, comment="独立访客数")
    conversations = Column(Integer, default=0, comment="对话数")
    contacts = Column(Integer, default=0, comment="联系表单数")
    avg_session_duration = Column(Integer, comment="平均会话时长（秒）")
    bounce_rate = Column(Integer, comment="跳出率（百分比，0-100）")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    site = relationship("Site", back_populates="analytics")

    __table_args__ = (
        Index('ix_site_analytics_site_id_date', 'site_id', 'date', unique=True),
    )

