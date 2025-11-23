from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """日誌條目"""
    id: str
    level: str  # error, warning, info
    type: str
    message: str
    severity: str  # high, medium, low
    timestamp: datetime
    source: Optional[str] = None
    metadata: Optional[dict] = None


class LogList(BaseModel):
    """日誌列表"""
    items: List[LogEntry]
    total: int
    page: int = 1
    page_size: int = 20

