from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DashboardStats(BaseModel):
    """Dashboard 統計數據"""
    today_sessions: int = Field(..., description="今日會話量")
    success_rate: float = Field(..., ge=0, le=100, description="成功率 (%)")
    token_usage: int = Field(..., description="Token 用量")
    error_count: int = Field(..., description="錯誤數")
    avg_response_time: float = Field(..., description="平均響應時間 (秒)")
    active_users: int = Field(..., description="活躍用戶數")
    
    # 變化趨勢
    sessions_change: str = Field(..., description="會話量變化")
    success_rate_change: str = Field(..., description="成功率變化")
    token_usage_change: str = Field(..., description="Token 用量變化")
    error_count_change: str = Field(..., description="錯誤數變化")
    response_time_change: str = Field(..., description="響應時間變化")
    active_users_change: str = Field(..., description="活躍用戶變化")


class RecentSession(BaseModel):
    """最近會話"""
    id: str
    user: str
    messages: int
    status: str  # completed, active, failed
    duration: str
    timestamp: str


class RecentError(BaseModel):
    """最近錯誤"""
    id: str
    type: str
    message: str
    severity: str  # high, medium, low
    timestamp: str


class DashboardData(BaseModel):
    """Dashboard 完整數據"""
    stats: DashboardStats
    recent_sessions: List[RecentSession]
    recent_errors: List[RecentError]

