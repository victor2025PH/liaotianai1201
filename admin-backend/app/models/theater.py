"""
智能剧场模型 - Phase 3: 多账号协同表演
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime, Text
from sqlalchemy.sql import func

from app.db import Base


def generate_uuid():
    """生成UUID字符串"""
    return str(uuid.uuid4())


class TheaterScenario(Base):
    """剧场场景表"""
    __tablename__ = "theater_scenarios"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False, index=True)  # 场景名称
    description = Column(Text, nullable=True)  # 场景描述
    roles = Column(JSON, nullable=False, default=list)  # 角色列表: ["UserA", "UserB", "UserC"]
    timeline = Column(JSON, nullable=False, default=list)  # 时间轴动作列表
    # timeline 结构示例:
    # [
    #   { "time_offset": 2, "role": "UserA", "content": "看多", "action": "send_message" },
    #   { "time_offset": 5, "role": "UserB", "content": "看空", "action": "send_message" },
    #   { "time_offset": 10, "role": "UserA", "content": "我也看空", "action": "send_message" }
    # ]
    enabled = Column(Boolean, default=True, nullable=False, index=True)  # 是否启用
    created_by = Column(String(100), nullable=True)  # 创建者用户ID
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class TheaterExecution(Base):
    """剧场执行记录表"""
    __tablename__ = "theater_executions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    scenario_id = Column(String(36), nullable=False, index=True)  # 关联的场景ID
    scenario_name = Column(String(200), nullable=False)  # 场景名称（快照）
    group_id = Column(String(100), nullable=False, index=True)  # 目标群组ID
    agent_mapping = Column(JSON, nullable=False, default=dict)  # Agent 映射: {"UserA": "agent_id_1", "UserB": "agent_id_2"}
    status = Column(String(20), nullable=False, index=True, default="pending")  # 状态: pending, running, completed, failed, cancelled
    started_at = Column(DateTime, nullable=True)  # 开始时间
    completed_at = Column(DateTime, nullable=True)  # 完成时间
    duration_seconds = Column(Integer, nullable=True)  # 执行时长（秒）
    executed_actions = Column(JSON, default=list)  # 已执行的动作列表（用于重试和恢复）
    error_message = Column(Text, nullable=True)  # 错误信息
    created_by = Column(String(100), nullable=True)  # 创建者用户ID
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
