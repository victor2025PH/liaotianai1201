from datetime import datetime
from typing import List

from pydantic import BaseModel


class Alert(BaseModel):
    id: str
    level: str
    title: str
    description: str
    status: str
    created_at: datetime


class AlertList(BaseModel):
    items: List[Alert]
    total: int

