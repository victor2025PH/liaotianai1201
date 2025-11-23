from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class Session(BaseModel):
    """會話記錄"""
    id: str
    user: str
    user_id: Optional[str] = None
    messages: int
    status: str  # completed, active, failed
    duration: str
    started_at: Union[datetime, str]
    ended_at: Optional[Union[datetime, str]] = None
    token_usage: Optional[int] = None
    model: Optional[str] = None

    @field_validator("started_at", mode="before")
    @classmethod
    def parse_started_at(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except:
                return datetime.utcnow()
        return v

    @field_validator("ended_at", mode="before")
    @classmethod
    def parse_ended_at(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except:
                return None
        return v


class SessionList(BaseModel):
    """會話列表"""
    items: List[Session]
    total: int
    page: int = 1
    page_size: int = 20

