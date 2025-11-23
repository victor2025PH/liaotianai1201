"""
Telegram注册相关数据模型
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db import Base


def generate_uuid():
    """生成UUID字符串"""
    return str(uuid.uuid4())


class UserRegistration(Base):
    """用户注册表"""
    __tablename__ = "user_registrations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    phone = Column(String(20), nullable=False, index=True)
    country_code = Column(String(5), nullable=False)
    api_id = Column(Integer, nullable=True)
    api_hash = Column(String(64), nullable=True)
    node_id = Column(String(50), nullable=False, index=True)
    session_name = Column(String(100), nullable=True)
    session_file_path = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, index=True)  # pending, code_sent, verified, completed, failed
    phone_code_hash = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    risk_score = Column(Integer, default=0)  # 0-100, 风险评分
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4或IPv6
    
    # 关系
    session_files = relationship("SessionFile", back_populates="registration", cascade="all, delete-orphan")
    anti_detection_logs = relationship("AntiDetectionLog", back_populates="registration", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_user_registrations_phone_node', 'phone', 'node_id', unique=True),
    )


class SessionFile(Base):
    """Session文件表"""
    __tablename__ = "session_files"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    registration_id = Column(String(36), ForeignKey("user_registrations.id", ondelete="CASCADE"), nullable=False, index=True)
    session_name = Column(String(100), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA256 hash
    server_node_id = Column(String(50), nullable=False, index=True)
    is_encrypted = Column(Boolean, default=False)
    encryption_key_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    last_verified_at = Column(DateTime, nullable=True)
    is_valid = Column(Boolean, default=True, index=True)
    extra_metadata = Column(JSON, nullable=True)  # 存储额外信息（避免与SQLAlchemy的metadata冲突）
    
    # 关系
    registration = relationship("UserRegistration", back_populates="session_files")


class AntiDetectionLog(Base):
    """风控日志表"""
    __tablename__ = "anti_detection_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    registration_id = Column(String(36), ForeignKey("user_registrations.id", ondelete="CASCADE"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # registration_start, code_sent, code_verified, etc.
    risk_level = Column(String(20), nullable=True, index=True)  # low, medium, high, critical
    risk_score = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4或IPv6
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(100), nullable=True)
    behavior_pattern = Column(JSON, nullable=True)
    action_taken = Column(String(100), nullable=True)  # allowed, blocked, rate_limited
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    # 关系
    registration = relationship("UserRegistration", back_populates="anti_detection_logs")

