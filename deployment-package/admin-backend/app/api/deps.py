from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.crud.user import get_user_by_email
from app.db import get_db
from app.schemas.auth import TokenPayload
from app.models.user import User

# 使用 auto_error=False 允許可選認證
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: Session = Depends(get_db_session)
):
    settings = get_settings()
    
    # 如果配置了禁用認證，返回匿名用戶（僅用於測試）
    if settings.disable_auth:
        # 返回一個默認的用戶對象（如果需要的話）
        # 這裡簡化處理，直接返回 None，由調用方處理
        return None
    
    # 從 OAuth2 或 HTTP Bearer 獲取 token
    auth_token = token
    if not auth_token and credentials:
        auth_token = credentials.credentials
    
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证身份",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证身份",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(auth_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        token_data = TokenPayload(**payload)
    except JWTError:
        raise credentials_exception
    if token_data.sub is None:
        raise credentials_exception
    user = get_user_by_email(db, email=token_data.sub)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user=Depends(get_current_user)):
    settings = get_settings()
    # 如果禁用认证，返回 None（允许匿名访问）
    if settings.disable_auth:
        return None
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证身份",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="账户已禁用")
    return current_user


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: Session = Depends(get_db_session)
):
    """可選認證：如果沒有提供 token，返回 None（僅用於測試）"""
    settings = get_settings()
    
    # 如果配置了禁用認證，返回 None（允許匿名訪問）
    if settings.disable_auth:
        return None
    
    try:
        # 從 OAuth2 或 HTTP Bearer 獲取 token
        auth_token = token
        if not auth_token and credentials:
            auth_token = credentials.credentials
        
        if not auth_token:
            return None
        
        payload = jwt.decode(auth_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            return None
        user = get_user_by_email(db, email=token_data.sub)
        return user if user and user.is_active else None
    except (JWTError, Exception):
        # 認證失敗時返回 None，允許匿名訪問（僅用於測試環境）
        return None


def require_superuser(current_user=Depends(get_current_active_user)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权访问")
    return current_user

