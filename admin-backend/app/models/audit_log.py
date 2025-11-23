"""
審計日誌數據模型
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, JSON, Index
from sqlalchemy.orm import relationship

from app.db import Base


class AuditLog(Base):
    """審計日誌模型"""
    __tablename__ = "audit_logs"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    
    # 用戶信息
    user_id = Column(Integer, nullable=False, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    
    # 操作信息
    action = Column(String(100), nullable=False, index=True)  # 操作類型：create, update, delete, assign, revoke 等
    resource_type = Column(String(100), nullable=False, index=True)  # 資源類型：user, role, permission, account, script 等
    resource_id = Column(String(100), nullable=True, index=True)  # 資源 ID（可為字符串）
    
    # 操作詳情
    description = Column(Text, nullable=True)  # 操作描述
    before_state = Column(JSON, nullable=True)  # 操作前狀態
    after_state = Column(JSON, nullable=True)  # 操作後狀態
    
    # 請求信息
    ip_address = Column(String(45), nullable=True)  # IPv4 或 IPv6
    user_agent = Column(String(500), nullable=True)  # 用戶代理
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 索引：用於快速查詢
    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_created', 'created_at'),
    )

