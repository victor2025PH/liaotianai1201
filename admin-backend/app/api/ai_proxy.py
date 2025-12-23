"""
AI 代理 API
提供安全的 AI 服务代理，避免在前端直接暴露 API Keys
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, AsyncGenerator
from app.core.config import get_settings
from app.api.deps import get_db_session
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import Request
import logging
import json
import asyncio
from app.crud.ai_usage import create_usage_log, calculate_cost

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-proxy", tags=["ai-proxy"])


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    """聊天请求"""
    messages: List[ChatMessage]
    model: Optional[str] = "gemini-2.5-flash-latest"  # 或 "gpt-4o-mini"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False  # 流式响应
    session_id: Optional[str] = None  # 会话 ID


class ChatResponse(BaseModel):
    """聊天响应"""
    content: str
    model: str
    usage: Optional[Dict] = None
    suggestions: Optional[List[str]] = None


class UsageStats(BaseModel):
    """使用统计"""
    total_requests: int
    total_tokens: int
    requests_by_model: Dict[str, int]
    last_request_time: Optional[datetime]


@router.post("/chat")
async def chat_proxy(
    request: ChatRequest,
    http_request: Request,
    db: Session = Depends(get_db_session)
):
    """
    代理 AI 聊天请求
    后端调用 AI 服务，避免在前端暴露 API Keys
    支持流式响应（stream=True）和普通响应
    """
    # 如果请求流式响应，返回 StreamingResponse
    if request.stream:
        return StreamingResponse(
            _stream_chat_response(request, http_request, db),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            }
        )
    
    # 普通响应（原有逻辑）
    try:
        settings = get_settings()
        
        # 获取会话 ID
        session_id = request.session_id or http_request.headers.get("X-Session-Id")
        
        # 确定使用的模型和 API Key
        use_gemini = request.model.startswith("gemini") or request.model == "gemini-2.5-flash-latest"
        use_openai = request.model.startswith("gpt") or request.model == "gpt-4o-mini"
        
        gemini_key = settings.gemini_api_key or ""
        openai_key = settings.openai_api_key or ""
        
        # 优先使用 Gemini
        if use_gemini and gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                
                # 构建消息内容
                system_prompt = ""
                user_messages = []
                
                for msg in request.messages:
                    if msg.role == "system":
                        system_prompt = msg.content
                    elif msg.role == "user":
                        user_messages.append(msg.content)
                    elif msg.role == "assistant":
                        user_messages.append(f"AI: {msg.content}")
                
                prompt = f"{system_prompt}\n\n" if system_prompt else ""
                prompt += "\n".join(user_messages)
                
                # 调用 Gemini API
                model = genai.GenerativeModel('gemini-2.5-flash-latest')
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": request.temperature,
                        "max_output_tokens": request.max_tokens,
                    }
                )
                
                content = response.text
                
                # 解析建议（如果存在）
                suggestions = None
                if "|||" in content:
                    parts = content.split("|||")
                    content = parts[0].strip()
                    if len(parts) > 1:
                        suggestions = [s.strip() for s in parts[1].split("|") if s.strip()]
                
                # 估算 token 使用（Gemini API 不直接返回 token 数）
                estimated_tokens = len(prompt.split()) * 1.3 + len(content.split()) * 1.3
                estimated_prompt_tokens = int(len(prompt.split()) * 1.3)
                estimated_completion_tokens = int(len(content.split()) * 1.3)
                estimated_cost = calculate_cost("gemini", "gemini-2.5-flash-latest", estimated_prompt_tokens, estimated_completion_tokens)
                
                # 记录使用统计
                create_usage_log(
                    db=db,
                    provider="gemini",
                    model="gemini-2.5-flash-latest",
                    prompt_tokens=estimated_prompt_tokens,
                    completion_tokens=estimated_completion_tokens,
                    total_tokens=int(estimated_tokens),
                    estimated_cost=estimated_cost,
                    status="success",
                    user_ip=http_request.client.host if http_request.client else None,
                    user_agent=http_request.headers.get("user-agent"),
                    site_domain=http_request.headers.get("referer"),
                    session_id=session_id,
                )
                
                return ChatResponse(
                    content=content,
                    model="gemini-2.5-flash-latest",
                    suggestions=suggestions
                )
                
            except Exception as gemini_error:
                logger.warning(f"Gemini API 调用失败: {gemini_error}")
                
                # 记录错误日志
                create_usage_log(
                    db=db,
                    provider="gemini",
                    model="gemini-2.5-flash-latest",
                    status="error",
                    error_message=str(gemini_error)[:500],
                    user_ip=http_request.client.host if http_request.client else None,
                    user_agent=http_request.headers.get("user-agent"),
                    site_domain=http_request.headers.get("referer"),
                    session_id=session_id,
                )
                
                # 如果 Gemini 失败，尝试 OpenAI
                if use_openai and openai_key:
                    pass  # 继续到 OpenAI 处理
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Gemini API 调用失败: {str(gemini_error)}"
                    )
        
        # 使用 OpenAI
        if use_openai and openai_key:
            try:
                import openai
                client = openai.OpenAI(api_key=openai_key)
                
                # 转换消息格式
                messages = []
                for msg in request.messages:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
                
                # 调用 OpenAI API
                completion = client.chat.completions.create(
                    model=request.model or "gpt-4o-mini",
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                )
                
                content = completion.choices[0].message.content
                
                # 解析建议（如果存在）
                suggestions = None
                if "|||" in content:
                    parts = content.split("|||")
                    content = parts[0].strip()
                    if len(parts) > 1:
                        suggestions = [s.strip() for s in parts[1].split("|") if s.strip()]
                
                # 计算成本
                estimated_cost = calculate_cost(
                    "openai",
                    request.model or "gpt-4o-mini",
                    completion.usage.prompt_tokens,
                    completion.usage.completion_tokens
                )
                
                # 记录使用统计
                create_usage_log(
                    db=db,
                    provider="openai",
                    model=request.model or "gpt-4o-mini",
                    prompt_tokens=completion.usage.prompt_tokens,
                    completion_tokens=completion.usage.completion_tokens,
                    total_tokens=completion.usage.total_tokens,
                    estimated_cost=estimated_cost,
                    status="success",
                    user_ip=http_request.client.host if http_request.client else None,
                    user_agent=http_request.headers.get("user-agent"),
                    site_domain=http_request.headers.get("referer"),
                    session_id=session_id,
                )
                
                return ChatResponse(
                    content=content,
                    model=request.model or "gpt-4o-mini",
                    usage={
                        "prompt_tokens": completion.usage.prompt_tokens,
                        "completion_tokens": completion.usage.completion_tokens,
                        "total_tokens": completion.usage.total_tokens,
                    },
                    suggestions=suggestions
                )
                
            except Exception as openai_error:
                logger.error(f"OpenAI API 调用失败: {openai_error}")
                
                # 记录错误日志
                create_usage_log(
                    db=db,
                    provider="openai",
                    model=request.model or "gpt-4o-mini",
                    status="error",
                    error_message=str(openai_error)[:500],
                    user_ip=http_request.client.host if http_request.client else None,
                    user_agent=http_request.headers.get("user-agent"),
                    site_domain=http_request.headers.get("referer"),
                    session_id=session_id,
                )
                
                raise HTTPException(
                    status_code=500,
                    detail=f"OpenAI API 调用失败: {str(openai_error)}"
                )
        
        # 如果都没有配置
        raise HTTPException(
            status_code=503,
            detail="AI 服务未配置。请配置 GEMINI_API_KEY 或 OPENAI_API_KEY"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 代理请求失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"AI 代理请求失败: {str(e)}"
        )


async def _stream_chat_response(
    request: ChatRequest,
    http_request: Request,
    db: Session
) -> AsyncGenerator[str, None]:
    """
    流式响应生成器
    使用 Server-Sent Events (SSE) 格式
    """
    try:
        settings = get_settings()
        use_gemini = request.model.startswith("gemini") or request.model == "gemini-2.5-flash-latest"
        use_openai = request.model.startswith("gpt") or request.model == "gpt-4o-mini"
        
        gemini_key = settings.gemini_api_key or ""
        openai_key = settings.openai_api_key or ""
        
        # 构建消息
        messages = []
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 优先使用 Gemini
        if use_gemini and gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                
                model = genai.GenerativeModel('gemini-2.5-flash-latest')
                
                # Gemini 流式响应
                response = model.generate_content(
                    "\n".join([f"{m['role']}: {m['content']}" for m in messages]),
                    generation_config={
                        "temperature": request.temperature,
                        "max_output_tokens": request.max_tokens,
                    },
                    stream=True
                )
                
                full_content = ""
                for chunk in response:
                    if chunk.text:
                        full_content += chunk.text
                        # 发送 SSE 格式的数据
                        yield f"data: {json.dumps({'content': chunk.text, 'done': False})}\n\n"
                
                # 发送完成信号
                yield f"data: {json.dumps({'content': '', 'done': True, 'full_content': full_content})}\n\n"
                
                # 记录使用统计
                estimated_tokens = len(full_content.split()) * 1.3
                estimated_cost = calculate_cost("gemini", "gemini-2.5-flash-latest", int(estimated_tokens * 0.5), int(estimated_tokens * 0.5))
                create_usage_log(
                    db=db,
                    provider="gemini",
                    model="gemini-2.5-flash-latest",
                    prompt_tokens=int(estimated_tokens * 0.5),
                    completion_tokens=int(estimated_tokens * 0.5),
                    total_tokens=int(estimated_tokens),
                    estimated_cost=estimated_cost,
                    status="success",
                    user_ip=http_request.client.host if http_request.client else None,
                    user_agent=http_request.headers.get("user-agent"),
                    site_domain=http_request.headers.get("referer"),
                    session_id=session_id,
                )
                return
                
            except Exception as gemini_error:
                logger.warning(f"Gemini 流式响应失败: {gemini_error}")
                if use_openai and openai_key:
                    pass  # 继续到 OpenAI
                else:
                    yield f"data: {json.dumps({'error': str(gemini_error), 'done': True})}\n\n"
                    return
        
        # 使用 OpenAI 流式响应
        if use_openai and openai_key:
            try:
                import openai
                client = openai.OpenAI(api_key=openai_key)
                
                stream = client.chat.completions.create(
                    model=request.model or "gpt-4o-mini",
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    stream=True,
                )
                
                full_content = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_content += content
                        yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
                
                # 发送完成信号
                yield f"data: {json.dumps({'content': '', 'done': True, 'full_content': full_content})}\n\n"
                
                # 记录使用统计
                estimated_tokens = len(full_content.split()) * 1.3
                estimated_cost = calculate_cost("openai", request.model or "gpt-4o-mini", int(estimated_tokens * 0.5), int(estimated_tokens * 0.5))
                create_usage_log(
                    db=db,
                    provider="openai",
                    model=request.model or "gpt-4o-mini",
                    prompt_tokens=int(estimated_tokens * 0.5),
                    completion_tokens=int(estimated_tokens * 0.5),
                    total_tokens=int(estimated_tokens),
                    estimated_cost=estimated_cost,
                    status="success",
                    user_ip=http_request.client.host if http_request.client else None,
                    user_agent=http_request.headers.get("user-agent"),
                    site_domain=http_request.headers.get("referer"),
                    session_id=session_id,
                )
                return
                
            except Exception as openai_error:
                logger.error(f"OpenAI 流式响应失败: {openai_error}")
                yield f"data: {json.dumps({'error': str(openai_error), 'done': True})}\n\n"
                return
        
        # 如果都没有配置
        yield f"data: {json.dumps({'error': 'AI 服务未配置', 'done': True})}\n\n"
        
    except Exception as e:
        logger.error(f"流式响应失败: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"


@router.get("/stats", response_model=UsageStats)
async def get_usage_stats(
    db: Session = Depends(get_db_session)
):
    """
    获取 AI 使用统计
    TODO: 实现数据库记录和统计
    """
    # 临时返回模拟数据
    return UsageStats(
        total_requests=0,
        total_tokens=0,
        requests_by_model={},
        last_request_time=None
    )

