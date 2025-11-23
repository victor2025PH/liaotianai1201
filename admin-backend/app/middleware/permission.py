"""
權限檢查中間件和依賴函數
"""
from typing import List, Optional, Callable
from functools import wraps
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db import get_db
from app.crud.permission import user_has_permission, user_has_any_permission, user_has_all_permissions
from app.models.user import User


def require_permission(permission_code: str):
    """
    檢查用戶是否有指定權限的依賴函數
    
    Usage:
        @router.get("/accounts")
        async def list_accounts(
            current_user: User = Depends(require_permission("account:view"))
        ):
            ...
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        from app.crud.permission import user_has_permission
        
        if not user_has_permission(db, user=current_user, permission_code=permission_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"沒有權限執行此操作，需要權限: {permission_code}"
            )
        return current_user
    
    return permission_checker


def require_any_permission(permission_codes: List[str]):
    """
    檢查用戶是否有任意一個指定權限的依賴函數
    
    Usage:
        @router.get("/accounts")
        async def list_accounts(
            current_user: User = Depends(require_any_permission(["account:view", "account:admin"]))
        ):
            ...
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not user_has_any_permission(db, user=current_user, permission_codes=permission_codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"沒有權限執行此操作，需要以下任一權限: {', '.join(permission_codes)}"
            )
        return current_user
    
    return permission_checker


def require_all_permissions(permission_codes: List[str]):
    """
    檢查用戶是否有所有指定權限的依賴函數
    
    Usage:
        @router.post("/accounts")
        async def create_account(
            current_user: User = Depends(require_all_permissions(["account:create", "account:admin"]))
        ):
            ...
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not user_has_all_permissions(db, user=current_user, permission_codes=permission_codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"沒有權限執行此操作，需要以下所有權限: {', '.join(permission_codes)}"
            )
        return current_user
    
    return permission_checker


def check_permission(
    user: User,
    permission_code: str,
    db: Session,
    raise_exception: bool = True
) -> bool:
    """
    檢查用戶是否有指定權限（在函數內部使用）
    
    Args:
        user: 用戶對象（可能為 None，如果禁用認證）
        permission_code: 權限代碼
        db: 數據庫會話
        raise_exception: 如果沒有權限是否拋出異常
    
    Returns:
        是否有權限
    
    Raises:
        HTTPException: 如果沒有權限且 raise_exception=True
    """
    from app.core.config import get_settings
    
    # 如果禁用認證，允許所有操作（開發模式）
    settings = get_settings()
    if settings.disable_auth:
        return True
    
    has_permission = user_has_permission(db, user=user, permission_code=permission_code)
    
    if not has_permission and raise_exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"沒有權限執行此操作，需要權限: {permission_code}"
        )
    
    return has_permission


def check_any_permission(
    user: User,
    permission_codes: List[str],
    db: Session,
    raise_exception: bool = True
) -> bool:
    """
    檢查用戶是否有任意一個指定權限（在函數內部使用）
    
    Args:
        user: 用戶對象
        permission_codes: 權限代碼列表
        db: 數據庫會話
        raise_exception: 如果沒有權限是否拋出異常
    
    Returns:
        是否有權限
    
    Raises:
        HTTPException: 如果沒有權限且 raise_exception=True
    """
    has_permission = user_has_any_permission(db, user=user, permission_codes=permission_codes)
    
    if not has_permission and raise_exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"沒有權限執行此操作，需要以下任一權限: {', '.join(permission_codes)}"
        )
    
    return has_permission


def check_all_permissions(
    user: User,
    permission_codes: List[str],
    db: Session,
    raise_exception: bool = True
) -> bool:
    """
    檢查用戶是否有所有指定權限（在函數內部使用）
    
    Args:
        user: 用戶對象
        permission_codes: 權限代碼列表
        db: 數據庫會話
        raise_exception: 如果沒有權限是否拋出異常
    
    Returns:
        是否有權限
    
    Raises:
        HTTPException: 如果沒有權限且 raise_exception=True
    """
    has_permission = user_has_all_permissions(db, user=user, permission_codes=permission_codes)
    
    if not has_permission and raise_exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"沒有權限執行此操作，需要以下所有權限: {', '.join(permission_codes)}"
        )
    
    return has_permission

