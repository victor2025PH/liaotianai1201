from datetime import datetime
from typing import List

from pydantic import BaseModel


class Activity(BaseModel):
    id: str
    name: str
    status: str
    success_rate: float
    started_at: datetime
    participants: int


class ActivityList(BaseModel):
    items: List[Activity]
    total: int

