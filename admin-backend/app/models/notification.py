"""
通知系統數據模型
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.db import Base


class NotificationType(str, PyEnum):
    """通知類型"""
    EMAIL = "email"
    BROWSER = "browser"
    WEBHOOK = "webhook"


class NotificationStatus(str, PyEnum):
    """通知狀態"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationConfig(Base):
    """通知配置模型"""
    __tablename__ = "notification_configs"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    
    # 配置名稱
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # 通知類型
    notification_type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    
    # 通知規則
    alert_levels = Column(JSON, nullable=True)  # 告警級別列表：["high", "medium", "low"]
    event_types = Column(JSON, nullable=True)  # 事件類型列表：["alert", "error", "info"]
    
    # 配置內容（根據通知類型不同）
    config_data = Column(JSON, nullable=False)  # 配置數據（郵件服務器、Webhook URL 等）
    
    # 接收人配置
    recipients = Column(JSON, nullable=False)  # 接收人列表：["user@example.com", "user_id"]
    
    # 狀態
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Notification(Base):
    """通知記錄模型"""
    __tablename__ = "notifications"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    
    # 通知配置 ID
    config_id = Column(Integer, nullable=True, index=True)
    
    # 通知類型
    notification_type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    
    # 通知內容
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String(50), nullable=True, index=True)  # high, medium, low, info
    event_type = Column(String(100), nullable=True, index=True)  # alert, error, info
    
    # 關聯資源
    resource_type = Column(String(100), nullable=True)  # account, script, system
    resource_id = Column(String(100), nullable=True)
    
    # 接收人
    recipient = Column(String(255), nullable=False, index=True)  # 用戶郵箱或用戶 ID
    
    # 狀態
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 額外數據
    metadata_ = Column("metadata", JSON, nullable=True)  # 額外的通知數據
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 已讀狀態（用於瀏覽器通知）
    read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)


class NotificationTemplate(Base):
    """通知模板模型"""
    __tablename__ = "notification_templates"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    notification_type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    title_template = Column(String(255), nullable=False)
    body_template = Column(Text, nullable=False)

    # 模板可用變數與條件
    variables = Column(JSON, nullable=True)  # 可用變數列表
    conditions = Column(JSON, nullable=True)  # 條件：alert_levels, event_types, resource_types 等
    default_metadata = Column(JSON, nullable=True)

    enabled = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

