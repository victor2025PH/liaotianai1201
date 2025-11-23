from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CommandCreate(BaseModel):
    account: str
    command: str
    payload: Optional[str] = None


class CommandResult(BaseModel):
    command_id: str = Field(alias="commandId")
    status: str
    queued_at: datetime = Field(alias="queuedAt")

    class Config:
        populate_by_name = True

