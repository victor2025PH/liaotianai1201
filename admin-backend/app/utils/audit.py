"""
審計日誌工具函數
"""
from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.orm import Session

from app.models.user import User
from app.crud.audit_log import create_audit_log


def get_client_ip(request: Request) -> Optional[str]:
    """獲取客戶端 IP 地址"""
    if request.client:
        return request.client.host
    return None


def get_user_agent(request: Request) -> Optional[str]:
    """獲取用戶代理"""
    return request.headers.get("user-agent")


def log_audit(
    db: Session,
    *,
    user: Optional[User],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    description: Optional[str] = None,
    before_state: Optional[Dict[str, Any]] = None,
    after_state: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    """記錄審計日誌"""
    from app.core.config import get_settings
    from app.crud.user import get_user_by_email
    
    # 如果用戶為 None，嘗試使用默認管理員用戶
    if user is None:
        settings = get_settings()
        try:
            admin_user = get_user_by_email(db, email=settings.admin_default_email)
            if admin_user:
                user = admin_user
            else:
                # 如果找不到管理員用戶，使用匿名用戶標記
                user_id = 0
                user_email = "anonymous@system"
        except Exception:
            user_id = 0
            user_email = "anonymous@system"
    
    if user:
        user_id = user.id
        user_email = user.email
    else:
        user_id = 0
        user_email = "anonymous@system"
    
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
    
    create_audit_log(
        db,
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        before_state=before_state,
        after_state=after_state,
        ip_address=ip_address,
        user_agent=user_agent,
    )

