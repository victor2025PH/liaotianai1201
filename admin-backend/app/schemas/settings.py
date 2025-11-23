from typing import Optional
from pydantic import BaseModel, Field


class AlertSettings(BaseModel):
    """告警設置"""
    error_rate_threshold: float = Field(5.0, ge=0, le=100, description="錯誤率閾值（%）")
    max_response_time: int = Field(2000, ge=0, description="最大允許響應時間（毫秒）")
    notification_method: str = Field("email", description="通知方式（email/webhook）")
    email_recipients: Optional[str] = Field(None, description="Email 收件人（多個用逗號分隔）")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    webhook_enabled: bool = Field(False, description="是否啟用 Webhook")

