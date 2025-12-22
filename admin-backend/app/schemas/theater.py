"""
智能剧场 Schema
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


# Timeline 动作结构
class TimelineAction(BaseModel):
    """时间轴动作"""
    time_offset: int = Field(..., ge=0, description="时间偏移（秒）")
    role: str = Field(..., description="角色名称")
    content: str = Field(..., description="消息内容")
    action: str = Field("send_message", description="动作类型: send_message, send_redpacket, etc.")
    payload: Optional[Dict[str, Any]] = Field(None, description="额外参数")


# Scenario 基础 Schema
class TheaterScenarioBase(BaseModel):
    """剧场场景基础 Schema"""
    name: str = Field(..., description="场景名称", max_length=200)
    description: Optional[str] = Field(None, description="场景描述")
    roles: List[str] = Field(default_factory=list, description="角色列表")
    timeline: List[TimelineAction] = Field(default_factory=list, description="时间轴动作列表")
    enabled: bool = Field(True, description="是否启用")
    
    @validator("roles")
    def validate_roles(cls, v):
        """验证角色列表不能为空"""
        if not v:
            raise ValueError("角色列表不能为空")
        return v
    
    @validator("timeline")
    def validate_timeline(cls, v):
        """验证时间轴动作"""
        if not v:
            raise ValueError("时间轴动作列表不能为空")
        
        # 检查所有动作的角色是否在角色列表中
        roles_in_timeline = {action.role for action in v}
        # 注意：这里需要从 timeline 中提取 roles，但 timeline 可能是 dict 列表
        # 暂时跳过这个验证，在创建时再验证
        return v


class TheaterScenarioCreate(TheaterScenarioBase):
    """创建剧场场景 Schema"""
    pass


class TheaterScenarioUpdate(BaseModel):
    """更新剧场场景 Schema"""
    name: Optional[str] = Field(None, description="场景名称", max_length=200)
    description: Optional[str] = Field(None, description="场景描述")
    roles: Optional[List[str]] = Field(None, description="角色列表")
    timeline: Optional[List[TimelineAction]] = Field(None, description="时间轴动作列表")
    enabled: Optional[bool] = Field(None, description="是否启用")


class TheaterScenarioResponse(TheaterScenarioBase):
    """剧场场景响应 Schema"""
    id: str
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Execution Schema
class TheaterExecutionCreate(BaseModel):
    """创建执行记录 Schema"""
    scenario_id: str = Field(..., description="场景ID")
    group_id: str = Field(..., description="目标群组ID")
    agent_mapping: Dict[str, str] = Field(..., description="Agent 映射: {'UserA': 'agent_id_1'}")


class TheaterExecutionResponse(BaseModel):
    """执行记录响应 Schema"""
    id: str
    scenario_id: str
    scenario_name: str
    group_id: str
    agent_mapping: Dict[str, str]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    executed_actions: List[Dict[str, Any]]
    error_message: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
