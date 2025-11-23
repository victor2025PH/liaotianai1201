from datetime import datetime, timedelta
from typing import Any, Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# 嘗試初始化 passlib，如果失敗則直接使用 bcrypt
_pwd_context_initialized = False
pwd_context = None

try:
    # 嘗試初始化 passlib，可能會因為 bcrypt 版本問題失敗
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # 測試初始化是否成功
    _test_hash = pwd_context.hash("test")
    _pwd_context_initialized = True
except Exception:
    # 如果 passlib 初始化失敗，使用 bcrypt 直接實現
    import bcrypt
    _pwd_context_initialized = False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證密碼"""
    if _pwd_context_initialized and pwd_context:
        return pwd_context.verify(plain_password, hashed_password)
    else:
        # 使用 bcrypt 直接實現
        import bcrypt
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False


def get_password_hash(password: str) -> str:
    """
    獲取密碼哈希值
    
    bcrypt 限制：密碼長度不能超過 72 字節
    如果密碼過長，會自動截斷到 72 字節
    """
    if not password:
        raise ValueError("密碼不能為空")
    
    # bcrypt 限制：密碼長度不能超過 72 字節
    # 將密碼編碼為 UTF-8 字節，如果超過 72 字節則截斷
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    if _pwd_context_initialized and pwd_context:
        # 使用 passlib（如果可用）
        try:
            return pwd_context.hash(password_bytes.decode('utf-8', errors='ignore') if password_bytes else password)
        except Exception:
            # 如果 passlib 失敗，回退到 bcrypt
            pass
    
    # 使用 bcrypt 直接實現
    import bcrypt
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    if expires_delta is not None:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode: dict[str, Any] = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[str]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return str(payload.get("sub"))
    except Exception:
        return None

