from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SystemHealth(BaseModel):
    """系統健康狀態"""
    status: str = Field(..., description="狀態（healthy/degraded/unhealthy）")
    uptime_seconds: int = Field(..., description="運行時間（秒）")
    version: str = Field(..., description="版本號")
    timestamp: str = Field(..., description="檢查時間戳")


class SystemMetrics(BaseModel):
    """系統指標"""
    cpu_usage_percent: float = Field(..., description="CPU 使用率（%）")
    memory_usage_percent: float = Field(..., description="內存使用率（%）")
    disk_usage_percent: float = Field(..., description="磁盤使用率（%）")
    active_connections: int = Field(..., description="活躍連接數")
    queue_length: int = Field(..., description="隊列長度")
    timestamp: str = Field(..., description="時間戳")


class SystemMonitorData(BaseModel):
    """系統監控數據"""
    health: SystemHealth
    metrics: SystemMetrics
    services: Dict[str, Any] = Field(..., description="服務狀態")

