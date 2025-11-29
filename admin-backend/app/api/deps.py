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

# 使用 auto_error=False 允許在 get_current_user 中手動處理認證
# 這樣可以更好地控制錯誤信息和處理邏輯，特別是在禁用認證時
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)  # 保留作為備用


def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话（别名函数，保持向后兼容）"""
    yield from get_db()


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),  # auto_error=False 时，token 可能为 None
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: Session = Depends(get_db_session)
):
    import logging
    logger = logging.getLogger(__name__)
    settings = get_settings()
    
    # 调试日志：仅在启用调试模式时输出
    if settings.debug_auth_logs:
        logger.debug("🔍 [AUTH DEBUG] get_current_user 被调用")
        logger.debug(f"🔍 [AUTH DEBUG] token from oauth2_scheme: {token[:30] + '...' if token else 'None'}")
        logger.debug(f"🔍 [AUTH DEBUG] credentials from http_bearer: {credentials is not None}")
    
    # 如果配置了禁用認證，返回匿名用戶（僅用於測試）
    if settings.disable_auth:
        if settings.debug_auth_logs:
            logger.debug("🔍 [AUTH DEBUG] disable_auth=True, 返回 None")
        return None
    
    # 從 OAuth2 或 HTTP Bearer 獲取 token
    # 当 auto_error=False 时，需要手动检查 token 是否存在
    auth_token = token
    if not auth_token and credentials:
        auth_token = credentials.credentials
        if settings.debug_auth_logs:
            logger.debug(f"🔍 [AUTH DEBUG] 从 credentials 获取 token: {auth_token[:30] + '...' if auth_token else 'None'}")
    
    if settings.debug_auth_logs:
        logger.debug(f"🔍 [AUTH DEBUG] 最终 auth_token: {auth_token[:30] + '...' if auth_token else 'None'}")
    
    if not auth_token:
        if settings.debug_auth_logs:
            logger.warning("🔍 [AUTH DEBUG] ❌ 准备抛出 401: 未找到認證 token")
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
        if settings.debug_auth_logs:
            logger.debug("🔍 [AUTH DEBUG] 开始 JWT 解码")
        payload = jwt.decode(auth_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        token_data = TokenPayload(**payload)
        if settings.debug_auth_logs:
            logger.debug(f"🔍 [AUTH DEBUG] JWT 解码成功, sub={token_data.sub}")
    except JWTError as e:
        if settings.debug_auth_logs:
            logger.warning(f"🔍 [AUTH DEBUG] ❌ 准备抛出 401: JWT 解码失败 - {str(e)}")
        raise credentials_exception
    if token_data.sub is None:
        if settings.debug_auth_logs:
            logger.warning("🔍 [AUTH DEBUG] ❌ 准备抛出 401: token_data.sub 为 None")
        raise credentials_exception
    if settings.debug_auth_logs:
        logger.debug(f"🔍 [AUTH DEBUG] 查询用户: {token_data.sub}")
    user = get_user_by_email(db, email=token_data.sub)
    if user is None:
        if settings.debug_auth_logs:
            logger.warning(f"🔍 [AUTH DEBUG] ❌ 准备抛出 401: 用户不存在 - {token_data.sub}")
        raise credentials_exception
    if settings.debug_auth_logs:
        logger.debug(f"🔍 [AUTH DEBUG] ✅ 认证成功, 用户: {user.email}")
    return user


def get_current_active_user(current_user=Depends(get_current_user)):
    import logging
    logger = logging.getLogger(__name__)
    settings = get_settings()
    
    # 调试日志：仅在启用调试模式时输出
    if settings.debug_auth_logs:
        logger.debug("🔍 [AUTH DEBUG] get_current_active_user 被调用")
        logger.debug(f"🔍 [AUTH DEBUG] current_user: {current_user.email if current_user else 'None'}")
    
    # 如果禁用认证，返回 None（允许匿名访问）
    if settings.disable_auth:
        if settings.debug_auth_logs:
            logger.debug("🔍 [AUTH DEBUG] disable_auth=True, 返回 None")
        return None
    if current_user is None:
        if settings.debug_auth_logs:
            logger.warning("🔍 [AUTH DEBUG] ❌ 准备抛出 401: current_user 为 None")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证身份",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.is_active:
        if settings.debug_auth_logs:
            logger.warning(f"🔍 [AUTH DEBUG] ❌ 准备抛出 400: 账户已禁用 - {current_user.email}")
        raise HTTPException(status_code=400, detail="账户已禁用")
    if settings.debug_auth_logs:
        logger.debug(f"🔍 [AUTH DEBUG] ✅ get_current_active_user 成功, 用户: {current_user.email}")
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


