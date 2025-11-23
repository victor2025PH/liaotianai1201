from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr


class RoleRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True  # Pydantic V2: 从 orm_mode 改为 from_attributes


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    is_superuser: bool
    roles: List[RoleRead] = []
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic V2: 从 orm_mode 改为 from_attributes


class UserCreate(BaseModel):
    """創建用戶請求"""
    email: EmailStr
    password: str
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False


class UserUpdate(BaseModel):
    """更新用戶請求"""
    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserPasswordReset(BaseModel):
    """重置密碼請求"""
    new_password: str
