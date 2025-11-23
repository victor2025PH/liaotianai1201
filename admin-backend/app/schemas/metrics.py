from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ResponseTimeDataPoint(BaseModel):
    """響應時間數據點"""
    hour: int = Field(..., description="小時 (0-23)")
    timestamp: str = Field(..., description="時間戳")
    avg_response_time: float = Field(..., description="平均響應時間（秒）")


class ResponseTimeMetrics(BaseModel):
    """響應時間趨勢數據"""
    data_points: List[ResponseTimeDataPoint] = Field(..., description="過去 24 小時的數據點")
    average: float = Field(..., description="平均響應時間")
    min: float = Field(..., description="最低響應時間")
    max: float = Field(..., description="最高響應時間")
    trend: str = Field(..., description="趨勢變化（例如：-12%）")


class SystemStatusItem(BaseModel):
    """系統狀態項"""
    label: str = Field(..., description="狀態標籤")
    status: str = Field(..., description="狀態（active/healthy/error）")
    value: str = Field(..., description="狀態值")
    description: str = Field(..., description="狀態描述")


class SystemMetrics(BaseModel):
    """系統狀態數據"""
    status_items: List[SystemStatusItem] = Field(..., description="系統狀態列表")
    last_updated: str = Field(..., description="最後更新時間")


class MetricsData(BaseModel):
    """完整的 Metrics 數據"""
    response_time: ResponseTimeMetrics
    system_status: SystemMetrics

