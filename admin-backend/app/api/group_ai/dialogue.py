"""
會話服務 HTTP API
"""
import logging
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from group_ai_service import DialogueManager, ServiceManager
from group_ai_service.models.account import AccountConfig
from app.db import get_db

# 導入緩存功能
from app.core.cache import cached, invalidate_cache

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Group AI Dialogue"])


class DialogueContextResponse(BaseModel):
    """對話上下文響應"""
    account_id: str
    group_id: int
    history_count: int
    last_reply_time: Optional[str] = None
    reply_count_today: int
    current_topic: Optional[str] = None
    mentioned_users: List[int] = []


class DialogueHistoryItem(BaseModel):
    """對話歷史項"""
    role: str  # user, assistant
    content: str
    timestamp: str
    message_id: Optional[int] = None
    user_id: Optional[int] = None


class DialogueHistoryResponse(BaseModel):
    """對話歷史響應"""
    account_id: str
    group_id: int
    history: List[DialogueHistoryItem]
    total_count: int


class ManualReplyRequest(BaseModel):
    """手動觸發回復請求"""
    account_id: str
    group_id: int
    message_text: str
    force_reply: bool = False  # 是否強制回復（忽略回復率限制）


class ManualReplyResponse(BaseModel):
    """手動觸發回復響應"""
    success: bool
    reply_text: Optional[str] = None
    error: Optional[str] = None


def get_service_manager() -> ServiceManager:
    """獲取服務管理器實例"""
    return ServiceManager.get_instance()


@router.get("/contexts", response_model=List[DialogueContextResponse])
@cached(prefix="dialogue_contexts", ttl=30)  # 緩存 30 秒
async def get_dialogue_contexts(
    account_id: Optional[str] = Query(None, description="賬號ID（可選，過濾）"),
    group_id: Optional[int] = Query(None, description="群組ID（可選，過濾）"),
    manager: ServiceManager = Depends(get_service_manager),
    db: Session = Depends(get_db)
):
    """
    獲取對話上下文列表
    
    返回所有或指定賬號/群組的對話上下文
    """
    try:
        dialogue_manager = manager.dialogue_manager
        if not dialogue_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="對話管理器未初始化"
            )
        
        contexts = []
        
        # 遍歷所有上下文
        for context_key, context in dialogue_manager.contexts.items():
            # 解析 context_key: "account_id:group_id"
            parts = context_key.split(":")
            if len(parts) != 2:
                continue
            
            ctx_account_id = parts[0]
            ctx_group_id = int(parts[1])
            
            # 過濾
            if account_id and ctx_account_id != account_id:
                continue
            if group_id and ctx_group_id != group_id:
                continue
            
            contexts.append(DialogueContextResponse(
                account_id=ctx_account_id,
                group_id=ctx_group_id,
                history_count=len(context.history),
                last_reply_time=context.last_reply_time.isoformat() if context.last_reply_time else None,
                reply_count_today=context.reply_count_today,
                current_topic=context.current_topic,
                mentioned_users=list(context.mentioned_users)
            ))
        
        return contexts
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取對話上下文失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取對話上下文失敗: {str(e)}"
        )


@router.get("/contexts/{account_id}/{group_id}", response_model=DialogueContextResponse)
@cached(prefix="dialogue_context", ttl=15)  # 緩存 15 秒
async def get_dialogue_context(
    account_id: str,
    group_id: int,
    manager: ServiceManager = Depends(get_service_manager),
    db: Session = Depends(get_db)
):
    """
    獲取指定賬號和群組的對話上下文
    """
    try:
        dialogue_manager = manager.dialogue_manager
        if not dialogue_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="對話管理器未初始化"
            )
        
        context = dialogue_manager.get_context(account_id, group_id)
        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到對話上下文 (賬號: {account_id}, 群組: {group_id})"
            )
        
        return DialogueContextResponse(
            account_id=context.account_id,
            group_id=context.group_id,
            history_count=len(context.history),
            last_reply_time=context.last_reply_time.isoformat() if context.last_reply_time else None,
            reply_count_today=context.reply_count_today,
            current_topic=context.current_topic,
            mentioned_users=list(context.mentioned_users)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取對話上下文失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取對話上下文失敗: {str(e)}"
        )


@router.get("/history", response_model=DialogueHistoryResponse)
@cached(prefix="dialogue_history", ttl=20)  # 緩存 20 秒
async def get_dialogue_history(
    account_id: str = Query(..., description="賬號ID"),
    group_id: int = Query(..., description="群組ID"),
    limit: int = Query(50, ge=1, le=200, description="返回數量"),
    manager: ServiceManager = Depends(get_service_manager),
    db: Session = Depends(get_db)
):
    """
    獲取對話歷史
    
    返回指定賬號和群組的對話歷史記錄
    """
    try:
        dialogue_manager = manager.dialogue_manager
        if not dialogue_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="對話管理器未初始化"
            )
        
        context = dialogue_manager.get_context(account_id, group_id)
        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到對話上下文 (賬號: {account_id}, 群組: {group_id})"
            )
        
        # 獲取最近的歷史記錄
        recent_history = context.get_recent_history(max_messages=limit)
        
        history_items = []
        for item in recent_history:
            history_items.append(DialogueHistoryItem(
                role=item.get("role", "user"),
                content=item.get("content", ""),
                timestamp=item.get("timestamp", datetime.now()).isoformat() if isinstance(item.get("timestamp"), datetime) else str(item.get("timestamp", "")),
                message_id=item.get("message_id"),
                user_id=item.get("user_id")
            ))
        
        return DialogueHistoryResponse(
            account_id=account_id,
            group_id=group_id,
            history=history_items,
            total_count=len(context.history)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取對話歷史失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取對話歷史失敗: {str(e)}"
        )


@router.post("/reply", response_model=ManualReplyResponse)
async def manual_reply(
    request: ManualReplyRequest,
    manager: ServiceManager = Depends(get_service_manager),
    db: Session = Depends(get_db)
):
    """
    手動觸發回復
    
    手動觸發指定賬號和群組的消息回復（用於測試或手動干預）
    """
    try:
        dialogue_manager = manager.dialogue_manager
        if not dialogue_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="對話管理器未初始化"
            )
        
        # 檢查賬號是否存在
        account_manager = manager.account_manager
        if request.account_id not in account_manager.accounts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"賬號不存在: {request.account_id}"
            )
        
        account = account_manager.accounts[request.account_id]
        account_config = account.config
        
        # 如果強制回復，臨時設置回復率為 1.0
        original_reply_rate = account_config.reply_rate
        if request.force_reply:
            account_config.reply_rate = 1.0
        
        try:
            # 創建模擬消息
            from unittest.mock import Mock
            from pyrogram.types import Message, User, Chat
            
            mock_user = Mock(spec=User)
            mock_user.id = 999999999
            mock_user.first_name = "手動觸發"
            mock_user.is_self = False
            
            chat_type = Mock()
            chat_type.name = "GROUP"
            
            mock_chat = Mock(spec=Chat)
            mock_chat.id = request.group_id
            mock_chat.type = chat_type
            
            mock_message = Mock(spec=Message)
            mock_message.text = request.message_text
            mock_message.from_user = mock_user
            mock_message.chat = mock_chat
            mock_message.id = int(datetime.now().timestamp())
            mock_message.date = datetime.now()
            
            # 處理消息
            reply_text = await dialogue_manager.process_message(
                account_id=request.account_id,
                group_id=request.group_id,
                message=mock_message,
                account_config=account_config
            )
            
            if reply_text:
                # 清除相關緩存
                invalidate_cache("dialogue_contexts")
                invalidate_cache("dialogue_context")
                invalidate_cache("dialogue_history")
                
                return ManualReplyResponse(
                    success=True,
                    reply_text=reply_text
                )
            else:
                return ManualReplyResponse(
                    success=False,
                    error="未生成回復（可能因為回復率限制或其他原因）"
                )
        
        finally:
            # 恢復原始回復率
            if request.force_reply:
                account_config.reply_rate = original_reply_rate
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"手動觸發回復失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"手動觸發回復失敗: {str(e)}"
        )

