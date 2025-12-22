"""
Agent API 数据模型 - Phase 7: 后端 Agent API 实现
"""

from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime, Text, Index
from sqlalchemy.sql import func

from app.db import Base


def generate_uuid():
    """生成UUID字符串"""
    return str(uuid.uuid4())


class Agent(Base):
    """Agent 设备表"""
    __tablename__ = "agents"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_id = Column(String(100), unique=True, nullable=False, index=True)  # Agent 唯一标识
    phone_number = Column(String(20), nullable=True, index=True)  # 手机号（可选）
    device_info = Column(JSON, nullable=True)  # 设备指纹信息
    proxy_url = Column(String(500), nullable=True)  # 代理URL（可选）
    status = Column(String(20), nullable=False, default="offline", index=True)  # online, offline, busy, error
    current_task_id = Column(String(36), nullable=True, index=True)  # 当前执行的任务ID
    api_key = Column(String(100), nullable=True)  # API 密钥（用于鉴权）
    metadata = Column(JSON, nullable=True, default=dict)  # 元数据（版本、平台等）
    last_active_time = Column(DateTime, nullable=True, index=True)  # 最后活跃时间
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_agents_status_active', 'status', 'last_active_time'),
    )


class AgentTask(Base):
    """Agent 任务表"""
    __tablename__ = "agent_tasks"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(100), unique=True, nullable=False, index=True)  # 任务唯一标识
    agent_id = Column(String(100), nullable=True, index=True)  # 分配的 Agent ID（可选，未分配时为 None）
    task_type = Column(String(50), nullable=False, index=True)  # scenario_execute, redpacket, etc.
    scenario_data = Column(JSON, nullable=True)  # 剧本数据（JSON）
    variables = Column(JSON, nullable=True, default=dict)  # 变量（JSON）
    priority = Column(Integer, default=1, nullable=False, index=True)  # 优先级（1-10，数字越大优先级越高）
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, in_progress, completed, failed, cancelled
    result_data = Column(JSON, nullable=True)  # 执行结果（JSON）
    error_message = Column(Text, nullable=True)  # 错误信息
    assigned_at = Column(DateTime, nullable=True)  # 分配时间
    started_at = Column(DateTime, nullable=True)  # 开始执行时间
    executed_at = Column(DateTime, nullable=True)  # 完成时间
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_agent_tasks_status_priority', 'status', 'priority', 'created_at'),
        Index('idx_agent_tasks_agent_status', 'agent_id', 'status'),
    )
