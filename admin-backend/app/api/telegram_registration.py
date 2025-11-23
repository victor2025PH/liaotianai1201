"""
Telegram注册API路由
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.telegram_registration_service import TelegramRegistrationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram-registration", tags=["telegram-registration"])


class RegistrationStartRequest(BaseModel):
    """开始注册请求"""
    phone: str
    country_code: str
    node_id: str
    api_id: Optional[int] = None
    api_hash: Optional[str] = None
    session_name: Optional[str] = None
    use_proxy: bool = False
    proxy_url: Optional[str] = None


class RegistrationVerifyRequest(BaseModel):
    """验证OTP请求"""
    registration_id: str
    code: str
    password: Optional[str] = None


class RegistrationCancelRequest(BaseModel):
    """取消注册请求"""
    registration_id: str


@router.post("/start")
async def start_registration(
    request: RegistrationStartRequest,
    http_request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """开始注册"""
    try:
        service = TelegramRegistrationService(db)
        
        # 获取客户端信息
        ip_address = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")
        device_fingerprint = http_request.headers.get("x-device-fingerprint")
        
        result = await service.start_registration(
            phone=request.phone,
            country_code=request.country_code,
            node_id=request.node_id,
            api_id=request.api_id,
            api_hash=request.api_hash,
            session_name=request.session_name,
            use_proxy=request.use_proxy,
            proxy_url=request.proxy_url,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
        )
        
        # 如果是模拟模式，在响应中添加提示
        if service.mock_mode:
            result['mock_mode'] = True
            result['mock_code'] = service.mock_code
            result['message'] = result.get('message', '') + f' (模拟模式，验证码: {service.mock_code})'
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"开始注册失败: {e}", exc_info=True)
        # 检查是否是唯一约束错误
        error_str = str(e)
        if "UNIQUE constraint" in error_str or "IntegrityError" in error_str:
            raise HTTPException(
                status_code=400, 
                detail=f"该手机号已在所选服务器上注册，请使用其他手机号或服务器"
            )
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@router.post("/verify")
async def verify_code(
    request: RegistrationVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """验证OTP码"""
    try:
        service = TelegramRegistrationService(db)
        
        result = await service.verify_code(
            registration_id=request.registration_id,
            code=request.code,
            password=request.password,
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"验证失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.get("/status/{registration_id}")
async def get_registration_status(
    registration_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取注册状态"""
    try:
        service = TelegramRegistrationService(db)
        
        result = service.get_registration_status(registration_id)
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.post("/cancel")
async def cancel_registration(
    request: RegistrationCancelRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """取消注册"""
    try:
        service = TelegramRegistrationService(db)
        
        result = service.cancel_registration(request.registration_id)
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"取消注册失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"取消注册失败: {str(e)}")

