"""
AI 提供商管理 API - 支持 OpenAI、Gemini、Grok 切换和动态 Key 管理
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_current_active_user
from app.models.user import User
from app.api.workers import _add_command, _get_all_workers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-provider", tags=["AI Provider"])


# ============ 數據模型 ============

class AIProvider(str, Enum):
    """AI 提供商枚举"""
    OPENAI = "openai"
    GEMINI = "gemini"
    GROK = "grok"
    MOCK = "mock"


class AIProviderStatus(BaseModel):
    """AI 提供商状态"""
    provider: str = Field(..., description="当前使用的提供商")
    api_key_configured: bool = Field(..., description="API Key 是否已配置")
    api_key_preview: str = Field(..., description="API Key 预览（前4位+后4位）")
    is_valid: bool = Field(..., description="API Key 是否有效")
    last_tested: Optional[str] = Field(None, description="最后测试时间")
    auto_failover_enabled: bool = Field(default=True, description="是否启用自动故障切换")
    failover_providers: List[str] = Field(default_factory=list, description="故障切换提供商列表")
    usage_stats: Dict[str, Any] = Field(default_factory=dict, description="使用统计")


class UpdateAIProviderRequest(BaseModel):
    """更新 AI 提供商请求"""
    provider: str = Field(..., description="提供商: openai/gemini/grok")
    api_key: Optional[str] = Field(None, description="API Key（可选，不传则使用现有Key）")
    auto_failover_enabled: bool = Field(default=True, description="是否启用自动故障切换")
    failover_providers: List[str] = Field(default_factory=list, description="故障切换提供商列表")


class TestAPIKeyRequest(BaseModel):
    """测试 API Key 请求"""
    provider: str = Field(..., description="提供商")
    api_key: str = Field(..., description="API Key")


class TestAPIKeyResponse(BaseModel):
    """测试 API Key 响应"""
    success: bool
    message: str
    provider: str
    tested_at: str


class AIProviderUsageStats(BaseModel):
    """AI 提供商使用统计"""
    provider: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    last_used: Optional[str] = None


# ============ 存储管理 ============

# 简单的内存存储（生产环境应使用数据库或Redis）
_ai_provider_config: Dict[str, Any] = {
    "current_provider": "openai",
    "providers": {
        "openai": {
            "api_key": None,
            "is_valid": False,
            "last_tested": None,
        },
        "gemini": {
            "api_key": None,
            "is_valid": False,
            "last_tested": None,
        },
        "grok": {
            "api_key": None,
            "is_valid": False,
            "last_tested": None,
        },
    },
    "auto_failover_enabled": True,
    "failover_providers": ["gemini", "grok"],
    "usage_stats": {
        "openai": {"total_requests": 0, "successful_requests": 0, "failed_requests": 0, "total_tokens": 0, "total_cost": 0.0},
        "gemini": {"total_requests": 0, "successful_requests": 0, "failed_requests": 0, "total_tokens": 0, "total_cost": 0.0},
        "grok": {"total_requests": 0, "successful_requests": 0, "failed_requests": 0, "total_tokens": 0, "total_cost": 0.0},
    }
}


def _get_api_key_preview(api_key: Optional[str]) -> str:
    """获取 API Key 预览"""
    if not api_key:
        return "未配置"
    if len(api_key) <= 8:
        return "****"
    return f"{api_key[:4]}...{api_key[-4:]}"


# ============ API 端点 ============

@router.get("/status", response_model=AIProviderStatus, status_code=status.HTTP_200_OK)
async def get_ai_provider_status(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """获取当前 AI 提供商状态"""
    current_provider = _ai_provider_config["current_provider"]
    provider_config = _ai_provider_config["providers"].get(current_provider, {})
    
    return AIProviderStatus(
        provider=current_provider,
        api_key_configured=provider_config.get("api_key") is not None,
        api_key_preview=_get_api_key_preview(provider_config.get("api_key")),
        is_valid=provider_config.get("is_valid", False),
        last_tested=provider_config.get("last_tested"),
        auto_failover_enabled=_ai_provider_config.get("auto_failover_enabled", True),
        failover_providers=_ai_provider_config.get("failover_providers", []),
        usage_stats=_ai_provider_config.get("usage_stats", {}).get(current_provider, {})
    )


@router.get("/providers", status_code=status.HTTP_200_OK)
async def get_all_providers(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """获取所有提供商状态"""
    providers = []
    for provider_name in ["openai", "gemini", "grok"]:
        provider_config = _ai_provider_config["providers"].get(provider_name, {})
        providers.append({
            "name": provider_name,
            "api_key_configured": provider_config.get("api_key") is not None,
            "api_key_preview": _get_api_key_preview(provider_config.get("api_key")),
            "is_valid": provider_config.get("is_valid", False),
            "last_tested": provider_config.get("last_tested"),
            "is_current": _ai_provider_config["current_provider"] == provider_name,
            "usage_stats": _ai_provider_config.get("usage_stats", {}).get(provider_name, {})
        })
    
    return {
        "success": True,
        "providers": providers,
        "current_provider": _ai_provider_config["current_provider"],
        "auto_failover_enabled": _ai_provider_config.get("auto_failover_enabled", True)
    }


@router.post("/switch", status_code=status.HTTP_200_OK)
async def switch_ai_provider(
    request: UpdateAIProviderRequest,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """切换 AI 提供商"""
    if request.provider not in ["openai", "gemini", "grok"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的提供商: {request.provider}"
        )
    
    # 更新提供商配置
    provider_config = _ai_provider_config["providers"].get(request.provider, {})
    
    # 如果提供了新的 API Key，更新它
    if request.api_key:
        provider_config["api_key"] = request.api_key
        provider_config["is_valid"] = False  # 需要重新测试
        provider_config["last_tested"] = None
    
    # 如果该提供商没有 API Key，返回错误
    if not provider_config.get("api_key"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"提供商 {request.provider} 的 API Key 未配置"
        )
    
    # 切换提供商
    _ai_provider_config["current_provider"] = request.provider
    _ai_provider_config["auto_failover_enabled"] = request.auto_failover_enabled
    _ai_provider_config["failover_providers"] = request.failover_providers
    
    # 发送命令到所有工作节点
    command = {
        "action": "switch_ai_provider",
        "params": {
            "provider": request.provider,
            "api_key": provider_config["api_key"],
            "auto_failover_enabled": request.auto_failover_enabled,
            "failover_providers": request.failover_providers
        },
        "timestamp": datetime.now().isoformat()
    }
    
    workers = _get_all_workers()
    for node_id in workers:
        _add_command(node_id, command)
    
    logger.info(f"AI 提供商已切换为: {request.provider}")
    
    return {
        "success": True,
        "message": f"已切换到 {request.provider}",
        "provider": request.provider,
        "api_key_preview": _get_api_key_preview(provider_config.get("api_key"))
    }


@router.post("/update-key", status_code=status.HTTP_200_OK)
async def update_api_key(
    provider: str = Query(..., description="AI提供商: openai/gemini/grok"),
    api_key: str = Query(..., description="API Key"),
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """更新指定提供商的 API Key"""
    if provider not in ["openai", "gemini", "grok"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的提供商: {provider}"
        )
    
    if not api_key or len(api_key.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API Key 格式无效"
        )
    
    # 更新 API Key
    provider_config = _ai_provider_config["providers"].get(provider, {})
    provider_config["api_key"] = api_key.strip()
    provider_config["is_valid"] = False  # 需要重新测试
    provider_config["last_tested"] = None
    
    # 如果这是当前提供商，发送更新命令到工作节点
    if _ai_provider_config["current_provider"] == provider:
        command = {
            "action": "update_ai_api_key",
            "params": {
                "provider": provider,
                "api_key": api_key.strip()
            },
            "timestamp": datetime.now().isoformat()
        }
        
        workers = _get_all_workers()
        for node_id in workers:
            _add_command(node_id, command)
    
    logger.info(f"已更新 {provider} 的 API Key")
    
    return {
        "success": True,
        "message": f"已更新 {provider} 的 API Key",
        "provider": provider,
        "api_key_preview": _get_api_key_preview(api_key.strip())
    }


@router.post("/test", response_model=TestAPIKeyResponse, status_code=status.HTTP_200_OK)
async def test_api_key(
    request: TestAPIKeyRequest,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """测试 API Key 是否有效"""
    try:
        is_valid = False
        message = ""
        
        if request.provider == "openai":
            try:
                import openai
                client = openai.OpenAI(api_key=request.api_key)
                # 简单的测试：列出模型
                client.models.list(limit=1)
                is_valid = True
                message = "OpenAI API Key 有效"
            except Exception as e:
                is_valid = False
                message = f"OpenAI API Key 无效: {str(e)}"
        
        elif request.provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=request.api_key)
                # 简单的测试：列出模型
                list(genai.list_models())
                is_valid = True
                message = "Gemini API Key 有效"
            except Exception as e:
                is_valid = False
                message = f"Gemini API Key 无效: {str(e)}"
        
        elif request.provider == "grok":
            try:
                import requests
                # Grok API 测试（需要根据实际API调整）
                response = requests.get(
                    "https://api.x.ai/v1/models",
                    headers={"Authorization": f"Bearer {request.api_key}"},
                    timeout=10
                )
                if response.status_code == 200:
                    is_valid = True
                    message = "Grok API Key 有效"
                else:
                    is_valid = False
                    message = f"Grok API Key 无效: {response.status_code}"
            except Exception as e:
                is_valid = False
                message = f"Grok API Key 无效: {str(e)}"
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的提供商: {request.provider}"
            )
        
        # 更新配置
        if is_valid:
            provider_config = _ai_provider_config["providers"].get(request.provider, {})
            provider_config["api_key"] = request.api_key
            provider_config["is_valid"] = True
            provider_config["last_tested"] = datetime.now().isoformat()
        
        return TestAPIKeyResponse(
            success=is_valid,
            message=message,
            provider=request.provider,
            tested_at=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"测试 API Key 失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试失败: {str(e)}"
        )


@router.get("/usage-stats", status_code=status.HTTP_200_OK)
async def get_usage_stats(
    provider: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """获取使用统计"""
    if provider:
        if provider not in ["openai", "gemini", "grok"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的提供商: {provider}"
            )
        stats = _ai_provider_config.get("usage_stats", {}).get(provider, {})
        return {
            "success": True,
            "provider": provider,
            "stats": stats
        }
    else:
        # 返回所有提供商统计
        return {
            "success": True,
            "stats": _ai_provider_config.get("usage_stats", {})
        }

