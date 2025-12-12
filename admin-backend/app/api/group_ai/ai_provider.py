"""
AI 提供商管理 API - 支持 OpenAI、Gemini、Grok 切换和动态 Key 管理
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_current_active_user
from app.models.user import User
from app.models.group_ai import AIProviderConfig, AIProviderSettings
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

def _load_ai_provider_config(db: Session) -> Dict[str, Any]:
    """从数据库加载 AI Provider 配置"""
    # 加载全局设置
    settings = db.query(AIProviderSettings).filter(AIProviderSettings.id == "singleton").first()
    if not settings:
        # 创建默认设置
        settings = AIProviderSettings(
            id="singleton",
            current_provider="openai",
            auto_failover_enabled=True,
            failover_providers=["gemini", "grok"]
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    # 加载各提供商的配置（支持多个 Key，但返回当前激活的 Key）
    providers = {}
    for provider_name in ["openai", "gemini", "grok"]:
        # 获取当前激活的 Key
        provider_config = db.query(AIProviderConfig).filter(
            AIProviderConfig.provider_name == provider_name,
            AIProviderConfig.is_active == True
        ).first()
        
        if not provider_config:
            # 如果没有激活的 Key，尝试获取任意一个
            provider_config = db.query(AIProviderConfig).filter(
                AIProviderConfig.provider_name == provider_name
            ).first()
        
        if not provider_config:
            # 创建默认配置
            provider_config = AIProviderConfig(
                provider_name=provider_name,
                key_name="default",
                api_key=None,
                is_valid=False,
                last_tested=None,
                is_active=True,
                usage_stats={}
            )
            db.add(provider_config)
            db.commit()
            db.refresh(provider_config)
        
        providers[provider_name] = {
            "api_key": provider_config.api_key,
            "is_valid": provider_config.is_valid,
            "last_tested": provider_config.last_tested.isoformat() if provider_config.last_tested else None,
            "usage_stats": provider_config.usage_stats or {},
            "key_id": provider_config.id,
            "key_name": provider_config.key_name
        }
    
    return {
        "current_provider": settings.current_provider,
        "providers": providers,
        "auto_failover_enabled": settings.auto_failover_enabled,
        "failover_providers": settings.failover_providers or [],
        "usage_stats": {
            provider_name: providers[provider_name].get("usage_stats", {})
            for provider_name in ["openai", "gemini", "grok"]
        }
    }


def _save_ai_provider_config(db: Session, config: Dict[str, Any]):
    """保存 AI Provider 配置到数据库"""
    # 保存全局设置
    settings = db.query(AIProviderSettings).filter(AIProviderSettings.id == "singleton").first()
    if not settings:
        settings = AIProviderSettings(id="singleton")
        db.add(settings)
    
    settings.current_provider = config.get("current_provider", "openai")
    settings.auto_failover_enabled = config.get("auto_failover_enabled", True)
    settings.failover_providers = config.get("failover_providers", [])
    settings.updated_at = datetime.now()
    
    # 保存各提供商的配置（更新当前激活的 Key）
    for provider_name, provider_data in config.get("providers", {}).items():
        # 获取当前激活的 Key
        provider_config = db.query(AIProviderConfig).filter(
            AIProviderConfig.provider_name == provider_name,
            AIProviderConfig.is_active == True
        ).first()
        
        if not provider_config:
            # 如果没有激活的 Key，创建新的
            provider_config = AIProviderConfig(
                provider_name=provider_name,
                key_name=provider_data.get("key_name", "default"),
                is_active=True
            )
            db.add(provider_config)
        
        if "api_key" in provider_data:
            provider_config.api_key = provider_data["api_key"]
        if "is_valid" in provider_data:
            provider_config.is_valid = provider_data["is_valid"]
        if "last_tested" in provider_data:
            if provider_data["last_tested"]:
                try:
                    if isinstance(provider_data["last_tested"], str):
                        provider_config.last_tested = datetime.fromisoformat(provider_data["last_tested"].replace("Z", "+00:00"))
                    else:
                        provider_config.last_tested = provider_data["last_tested"]
                except:
                    provider_config.last_tested = datetime.now()
            else:
                provider_config.last_tested = None
        if "usage_stats" in provider_data:
            provider_config.usage_stats = provider_data["usage_stats"]
        if "key_name" in provider_data:
            provider_config.key_name = provider_data["key_name"]
        
        provider_config.updated_at = datetime.now()
    
    db.commit()


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
    config = _load_ai_provider_config(db)
    current_provider = config["current_provider"]
    provider_config = config["providers"].get(current_provider, {})
    
    return AIProviderStatus(
        provider=current_provider,
        api_key_configured=provider_config.get("api_key") is not None,
        api_key_preview=_get_api_key_preview(provider_config.get("api_key")),
        is_valid=provider_config.get("is_valid", False),
        last_tested=provider_config.get("last_tested"),
        auto_failover_enabled=config.get("auto_failover_enabled", True),
        failover_providers=config.get("failover_providers", []),
        usage_stats=config.get("usage_stats", {}).get(current_provider, {})
    )


@router.get("/providers", status_code=status.HTTP_200_OK)
async def get_all_providers(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """获取所有提供商状态"""
    config = _load_ai_provider_config(db)
    providers = []
    for provider_name in ["openai", "gemini", "grok"]:
        provider_config = config["providers"].get(provider_name, {})
        providers.append({
            "name": provider_name,
            "api_key_configured": provider_config.get("api_key") is not None,
            "api_key_preview": _get_api_key_preview(provider_config.get("api_key")),
            "is_valid": provider_config.get("is_valid", False),
            "last_tested": provider_config.get("last_tested"),
            "is_current": config["current_provider"] == provider_name,
            "usage_stats": config.get("usage_stats", {}).get(provider_name, {})
        })
    
    return {
        "success": True,
        "providers": providers,
        "current_provider": config["current_provider"],
        "auto_failover_enabled": config.get("auto_failover_enabled", True)
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
    
    # 从数据库加载配置
    config = _load_ai_provider_config(db)
    provider_config = config["providers"].get(request.provider, {})
    
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
    config["current_provider"] = request.provider
    config["auto_failover_enabled"] = request.auto_failover_enabled
    config["failover_providers"] = request.failover_providers
    
    # 保存到数据库
    _save_ai_provider_config(db, config)
    
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
    
    # 从数据库加载配置
    config = _load_ai_provider_config(db)
    provider_config = config["providers"].get(provider, {})
    
    # 检查 API Key 是否发生变化
    old_api_key = provider_config.get("api_key")
    new_api_key = api_key.strip()
    
    # 更新 API Key
    provider_config["api_key"] = new_api_key
    
    # 只有当 API Key 发生变化时，才重置验证状态
    # 如果 API Key 没有变化，保留原有的验证状态
    if old_api_key != new_api_key:
        provider_config["is_valid"] = False  # 需要重新测试
        provider_config["last_tested"] = None
    # 如果 API Key 没有变化，保留原有的 is_valid 和 last_tested 状态
    
    # 保存到数据库
    _save_ai_provider_config(db, config)
    
    # 如果这是当前提供商，发送更新命令到工作节点
    if config["current_provider"] == provider:
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
                # 简单的测试：列出模型（不使用 limit 参数，因为某些版本不支持）
                models = client.models.list()
                # 尝试获取第一个模型来验证
                list(models)[0] if models else None
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
                models = genai.list_models()
                # 尝试获取第一个模型来验证
                list(models)[0] if models else None
                is_valid = True
                message = "Gemini API Key 有效"
            except ImportError as e:
                is_valid = False
                message = f"Gemini API Key 无效: 缺少依赖包 'google-generativeai'，请运行: pip install google-generativeai"
            except Exception as e:
                is_valid = False
                message = f"Gemini API Key 无效: {str(e)}"
        
        elif request.provider == "grok":
            try:
                import requests
                # Grok API 测试（使用 xAI 的 API）
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
                    message = f"Grok API Key 无效: HTTP {response.status_code}"
            except ImportError as e:
                is_valid = False
                message = f"Grok API Key 无效: 缺少依赖包 'requests'，请运行: pip install requests"
            except Exception as e:
                is_valid = False
                message = f"Grok API Key 无效: {str(e)}"
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的提供商: {request.provider}"
            )
        
        # 从数据库加载配置并更新
        config = _load_ai_provider_config(db)
        provider_config = config["providers"].get(request.provider, {})
        
        # 如果测试成功，更新配置
        if is_valid:
            provider_config["api_key"] = request.api_key
            provider_config["is_valid"] = True
            provider_config["last_tested"] = datetime.now().isoformat()
        else:
            # 即使测试失败，也更新 last_tested 时间
            provider_config["is_valid"] = False
            provider_config["last_tested"] = None
        
        # 保存到数据库
        _save_ai_provider_config(db, config)
        
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
        config = _load_ai_provider_config(db)
        stats = config.get("usage_stats", {}).get(provider, {})
        return {
            "success": True,
            "provider": provider,
            "stats": stats
        }
    else:
        # 返回所有提供商统计
        config = _load_ai_provider_config(db)
        return {
            "success": True,
            "stats": config.get("usage_stats", {})
        }


# ============ 多 Key 管理 API ============

@router.get("/keys", status_code=status.HTTP_200_OK)
async def list_api_keys(
    provider: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """列出所有 API Key（支持按提供商筛选）"""
    query = db.query(AIProviderConfig)
    
    if provider:
        if provider not in ["openai", "gemini", "grok"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的提供商: {provider}"
            )
        query = query.filter(AIProviderConfig.provider_name == provider)
    
    keys = query.order_by(AIProviderConfig.created_at.desc()).all()
    
    return {
        "success": True,
        "keys": [
            {
                "id": key.id,
                "provider": key.provider_name,
                "key_name": key.key_name,
                "api_key_preview": _get_api_key_preview(key.api_key),
                "is_valid": key.is_valid,
                "is_active": key.is_active,
                "last_tested": key.last_tested.isoformat() if key.last_tested else None,
                "created_at": key.created_at.isoformat(),
                "updated_at": key.updated_at.isoformat(),
                "usage_stats": key.usage_stats or {}
            }
            for key in keys
        ]
    }


@router.post("/keys/add", status_code=status.HTTP_200_OK)
async def add_api_key(
    provider: str = Query(..., description="AI提供商: openai/gemini/grok"),
    api_key: str = Query(..., description="API Key"),
    key_name: str = Query("default", description="Key 名称/别名"),
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """添加新的 API Key"""
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
    
    # 检查是否已存在同名 Key
    existing = db.query(AIProviderConfig).filter(
        AIProviderConfig.provider_name == provider,
        AIProviderConfig.key_name == key_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Key 名称 '{key_name}' 已存在，请使用不同的名称或先删除旧 Key"
        )
    
    # 创建新 Key（默认不激活）
    new_key = AIProviderConfig(
        provider_name=provider,
        key_name=key_name,
        api_key=api_key.strip(),
        is_valid=False,
        is_active=False,  # 新添加的 Key 默认不激活
        usage_stats={}
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    
    logger.info(f"已添加 {provider} 的新 Key: {key_name}")
    
    return {
        "success": True,
        "message": f"已添加 {provider} 的 Key: {key_name}",
        "key": {
            "id": new_key.id,
            "provider": new_key.provider_name,
            "key_name": new_key.key_name,
            "api_key_preview": _get_api_key_preview(new_key.api_key),
            "is_valid": new_key.is_valid,
            "is_active": new_key.is_active
        }
    }


@router.delete("/keys/{key_id}", status_code=status.HTTP_200_OK)
async def delete_api_key(
    key_id: str,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """删除指定的 API Key"""
    key = db.query(AIProviderConfig).filter(AIProviderConfig.id == key_id).first()
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key 不存在"
        )
    
    # 如果删除的是当前激活的 Key，需要激活另一个 Key
    if key.is_active:
        # 查找同一提供商的其他 Key
        other_key = db.query(AIProviderConfig).filter(
            AIProviderConfig.provider_name == key.provider_name,
            AIProviderConfig.id != key_id
        ).first()
        
        if other_key:
            other_key.is_active = True
            db.commit()
    
    provider_name = key.provider_name
    key_name = key.key_name
    
    db.delete(key)
    db.commit()
    
    logger.info(f"已删除 {provider_name} 的 Key: {key_name}")
    
    return {
        "success": True,
        "message": f"已删除 {provider_name} 的 Key: {key_name}"
    }


@router.post("/keys/{key_id}/activate", status_code=status.HTTP_200_OK)
async def activate_api_key(
    key_id: str,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """激活指定的 API Key（取消激活同一提供商的其他 Key）"""
    key = db.query(AIProviderConfig).filter(AIProviderConfig.id == key_id).first()
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key 不存在"
        )
    
    # 取消激活同一提供商的其他 Key
    db.query(AIProviderConfig).filter(
        AIProviderConfig.provider_name == key.provider_name,
        AIProviderConfig.id != key_id,
        AIProviderConfig.is_active == True
    ).update({"is_active": False})
    
    # 激活当前 Key
    key.is_active = True
    db.commit()
    db.refresh(key)
    
    # 如果这是当前提供商，发送更新命令到工作节点
    config = _load_ai_provider_config(db)
    if config["current_provider"] == key.provider_name:
        command = {
            "action": "update_ai_api_key",
            "params": {
                "provider": key.provider_name,
                "api_key": key.api_key
            },
            "timestamp": datetime.now().isoformat()
        }
        
        workers = _get_all_workers()
        for node_id in workers:
            _add_command(node_id, command)
    
    logger.info(f"已激活 {key.provider_name} 的 Key: {key.key_name}")
    
    return {
        "success": True,
        "message": f"已激活 {key.provider_name} 的 Key: {key.key_name}",
        "key": {
            "id": key.id,
            "provider": key.provider_name,
            "key_name": key.key_name,
            "api_key_preview": _get_api_key_preview(key.api_key),
            "is_valid": key.is_valid,
            "is_active": key.is_active
        }
    }

