from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Account(BaseModel):
    phone: str
    display_name: str = Field(alias="displayName")
    roles: List[str]
    status: str
    last_heartbeat: Optional[datetime] = Field(default=None, alias="lastHeartbeat")

    class Config:
        populate_by_name = True


class AccountList(BaseModel):
    items: List[Account]
    total: int

