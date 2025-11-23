"""
告警規則 Schema
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class AlertRuleBase(BaseModel):
    """告警規則基礎 Schema"""
    name: str = Field(..., description="規則名稱", min_length=1, max_length=200)
    rule_type: str = Field(..., description="規則類型：error_rate, response_time, system_errors, account_offline 等")
    alert_level: str = Field("warning", description="告警級別：error, warning, info")
    threshold_value: float = Field(..., description="閾值")
    threshold_operator: str = Field(">", description="比較運算符：>, >=, <, <=, ==, !=")
    enabled: bool = Field(True, description="是否啟用")
    notification_method: str = Field("email", description="通知方式：email, webhook, telegram")
    notification_target: Optional[str] = Field(None, description="通知目標（郵箱地址、Webhook URL、Telegram Chat ID 等）")
    rule_conditions: Dict[str, Any] = Field(default_factory=dict, description="規則條件（JSON格式）")
    description: Optional[str] = Field(None, description="規則描述")


class AlertRuleCreate(AlertRuleBase):
    """創建告警規則 Schema"""
    pass


class AlertRuleUpdate(BaseModel):
    """更新告警規則 Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    rule_type: Optional[str] = None
    alert_level: Optional[str] = None
    threshold_value: Optional[float] = None
    threshold_operator: Optional[str] = None
    enabled: Optional[bool] = None
    notification_method: Optional[str] = None
    notification_target: Optional[str] = None
    rule_conditions: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class AlertRule(AlertRuleBase):
    """告警規則 Schema"""
    id: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AlertRuleList(BaseModel):
    """告警規則列表 Schema"""
    items: List[AlertRule]
    total: int

