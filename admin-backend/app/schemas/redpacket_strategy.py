"""
紅包策略 Schema
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class RedPacketStrategyBase(BaseModel):
    """紅包策略基礎 Schema"""
    name: str = Field(..., description="策略名稱", max_length=200)
    description: Optional[str] = Field(None, description="策略描述")
    keywords: List[str] = Field(default_factory=list, description="關鍵詞列表，例如 ['USDT', 'TON', '積分', '紅包']")
    delay_min: int = Field(1000, ge=0, description="最小延遲（毫秒）")
    delay_max: int = Field(5000, ge=0, description="最大延遲（毫秒）")
    target_groups: List[int] = Field(default_factory=list, description="目標群組 ID 列表")
    probability: Optional[int] = Field(100, ge=0, le=100, description="搶包概率 (0-100)，可選，模擬偶爾沒看到的情況")
    enabled: bool = Field(True, description="是否啟用")
    
    @validator("delay_max")
    def validate_delay_max(cls, v, values):
        """驗證最大延遲必須大於等於最小延遲"""
        if "delay_min" in values and v < values["delay_min"]:
            raise ValueError("最大延遲必須大於等於最小延遲")
        return v
    
    @validator("keywords")
    def validate_keywords(cls, v):
        """驗證關鍵詞列表不能為空"""
        if not v:
            raise ValueError("關鍵詞列表不能為空")
        return v


class RedPacketStrategyCreate(RedPacketStrategyBase):
    """創建紅包策略 Schema"""
    pass


class RedPacketStrategyUpdate(BaseModel):
    """更新紅包策略 Schema"""
    name: Optional[str] = Field(None, description="策略名稱", max_length=200)
    description: Optional[str] = Field(None, description="策略描述")
    keywords: Optional[List[str]] = Field(None, description="關鍵詞列表")
    delay_min: Optional[int] = Field(None, ge=0, description="最小延遲（毫秒）")
    delay_max: Optional[int] = Field(None, ge=0, description="最大延遲（毫秒）")
    target_groups: Optional[List[int]] = Field(None, description="目標群組 ID 列表")
    probability: Optional[int] = Field(None, ge=0, le=100, description="搶包概率 (0-100)")
    enabled: Optional[bool] = Field(None, description="是否啟用")
    
    @validator("delay_max")
    def validate_delay_max(cls, v, values):
        """驗證最大延遲必須大於等於最小延遲"""
        if v is not None and "delay_min" in values and values["delay_min"] is not None:
            if v < values["delay_min"]:
                raise ValueError("最大延遲必須大於等於最小延遲")
        return v


class RedPacketStrategyResponse(RedPacketStrategyBase):
    """紅包策略響應 Schema"""
    id: str
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
