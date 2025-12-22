"""
Agent API Schemas - Phase 7: 后端 Agent API 实现
Pydantic 模型，用于验证 Agent 发来的数据
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class AgentRegisterRequest(BaseModel):
    """Agent 注册请求"""
    agent_id: str = Field(..., description="Agent 唯一标识")
    phone_number: Optional[str] = Field(None, description="手机号（可选）")
    device_info: Optional[Dict[str, Any]] = Field(None, description="设备指纹信息（JSON）")
    proxy_url: Optional[str] = Field(None, description="代理URL（可选）")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据（版本、平台等）")


class AgentRegisterResponse(BaseModel):
    """Agent 注册响应"""
    success: bool
    agent_id: str
    api_key: Optional[str] = None
    message: str


class HeartbeatRequest(BaseModel):
    """心跳请求"""
    status: Optional[str] = Field("online", description="状态: online, busy")
    current_task_id: Optional[str] = Field(None, description="当前执行的任务ID（可选）")
    timestamp: Optional[float] = Field(None, description="时间戳")


class HeartbeatResponse(BaseModel):
    """心跳响应"""
    status: str = "ok"
    message: Optional[str] = None


class TaskResultRequest(BaseModel):
    """任务结果请求"""
    status: str = Field(..., description="状态: completed, failed")
    result_data: Optional[Dict[str, Any]] = Field(None, description="执行结果数据（JSON）")
    error: Optional[str] = Field(None, description="错误信息（如果失败）")
    agent_id: Optional[str] = Field(None, description="Agent ID（用于验证）")


class TaskResultResponse(BaseModel):
    """任务结果响应"""
    success: bool
    message: str


class TaskResponse(BaseModel):
    """返回给 Agent 的任务数据结构"""
    task: Optional[Dict[str, Any]] = Field(None, description="任务数据，如果没有任务则为 None")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task": {
                    "task_id": "task_xxx",
                    "task_type": "scenario_execute",
                    "scenario_data": {
                        "name": "测试剧本",
                        "timeline": [
                            {
                                "time_offset": 0,
                                "role": "UserA",
                                "content": "Hello",
                                "action": "send_message"
                            }
                        ]
                    },
                    "variables": {
                        "target_user": "张三",
                        "group_id": "-1001234567890"
                    },
                    "priority": 1,
                    "created_at": "2025-12-22T10:00:00Z"
                }
            }
        }


class AgentInfo(BaseModel):
    """Agent 信息（用于响应）"""
    agent_id: str
    phone_number: Optional[str] = None
    status: str
    current_task_id: Optional[str] = None
    last_active_time: Optional[datetime] = None
    agent_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
