"""
前端配置 API
提供统一的 AI KEY 和配置信息给前端应用
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.config import get_settings

router = APIRouter(prefix="/frontend-config", tags=["frontend-config"])


class FrontendConfigResponse(BaseModel):
    """前端配置响应"""
    openai_api_key: str
    gemini_api_key: str = ""
    default_language: str = "zh-CN"
    ai_model: str = "gpt-4o-mini"


@router.get("/ai-keys", response_model=FrontendConfigResponse)
async def get_ai_keys():
    """
    获取 AI API Keys（用于前端直接调用 OpenAI/Gemini）
    注意：此端点返回的 KEY 会暴露给前端，请确保服务器安全
    """
    try:
        settings = get_settings()
        
        # 从环境变量读取 API Keys
        openai_key = settings.openai_api_key or ""
        gemini_key = settings.gemini_api_key or ""
        
        # 如果环境变量中没有，尝试从 os.environ 直接读取（兼容性处理）
        if not openai_key:
            import os
            openai_key = os.getenv("OPENAI_API_KEY", "")
        if not gemini_key:
            import os
            gemini_key = os.getenv("GEMINI_API_KEY", "")
        
        return FrontendConfigResponse(
            openai_api_key=openai_key,
            gemini_api_key=gemini_key,
            default_language="zh-CN",
            ai_model=settings.openai_model or "gpt-4o-mini"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")
