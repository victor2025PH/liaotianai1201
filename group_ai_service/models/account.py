"""
賬號管理相關數據模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class AccountStatusEnum(str, Enum):
    """賬號狀態枚舉"""
    OFFLINE = "offline"
    STARTING = "starting"
    ONLINE = "online"
    ERROR = "error"
    STOPPING = "stopping"


@dataclass
class AccountConfig:
    """賬號配置"""
    account_id: str
    session_file: str
    script_id: str  # 關聯的劇本 ID
    group_ids: List[int] = field(default_factory=list)  # 監聽的群組 ID 列表
    active: bool = True
    reply_rate: float = 0.3  # 回復頻率 (0-1)
    redpacket_enabled: bool = True
    redpacket_probability: float = 0.5  # 紅包參與概率
    max_replies_per_hour: int = 50
    min_reply_interval: int = 3  # 秒
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccountStatus:
    """賬號狀態"""
    account_id: str
    status: AccountStatusEnum  # 使用 Enum 類型
    online: bool
    last_activity: Optional[datetime] = None
    message_count: int = 0
    reply_count: int = 0
    redpacket_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    uptime_seconds: int = 0


@dataclass
class AccountInfo:
    """賬號信息（用於列表展示）"""
    account_id: str
    session_file: str
    script_id: str
    status: AccountStatusEnum
    group_count: int
    message_count: int
    reply_count: int
    last_activity: Optional[datetime] = None

