"""
群組管理API
實現賬號自動創建群組和啟動群聊功能
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging

from group_ai_service.service_manager import ServiceManager
from app.api.group_ai.accounts import get_service_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["groups"])


class CreateGroupRequest(BaseModel):
    """創建群組請求"""
    account_id: str
    title: str
    description: Optional[str] = None
    member_ids: Optional[List[int]] = None
    auto_reply: bool = True


class JoinGroupRequest(BaseModel):
    """加入群組請求"""
    account_id: str
    group_username: Optional[str] = None
    group_id: Optional[int] = None
    invite_link: Optional[str] = None
    auto_reply: bool = True


class StartGroupChatRequest(BaseModel):
    """啟動群組聊天請求"""
    account_id: str
    group_id: int
    auto_reply: bool = True


class GroupResponse(BaseModel):
    """群組響應"""
    account_id: str
    group_id: int
    group_title: Optional[str] = None
    success: bool
    message: str


@router.post("/create", response_model=GroupResponse)
async def create_group(
    request: CreateGroupRequest,
    service_manager: ServiceManager = Depends(get_service_manager)
):
    """創建新的Telegram群組並啟動群聊"""
    try:
        from group_ai_service.group_manager import GroupManager
        
        group_manager = GroupManager(service_manager.account_manager)
        
        # 創建群組並啟動群聊
        group_id = await group_manager.create_and_start_group(
            account_id=request.account_id,
            title=request.title,
            description=request.description,
            member_ids=request.member_ids,
            auto_reply=request.auto_reply
        )
        
        if group_id:
            # 獲取群組信息
            account = service_manager.account_manager.accounts.get(request.account_id)
            group_title = request.title
            if account and account.client.is_connected:
                try:
                    chat = await account.client.get_chat(group_id)
                    group_title = chat.title
                except:
                    pass
            
            return GroupResponse(
                account_id=request.account_id,
                group_id=group_id,
                group_title=group_title,
                success=True,
                message=f"群組創建成功並已啟動群聊"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="創建群組失敗"
            )
            
    except Exception as e:
        logger.exception(f"創建群組失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"創建群組失敗: {str(e)}"
        )


@router.post("/join", response_model=GroupResponse)
async def join_group(
    request: JoinGroupRequest,
    service_manager: ServiceManager = Depends(get_service_manager)
):
    """加入Telegram群組並啟動群聊"""
    try:
        try:
            from group_ai_service.group_manager import GroupManager
        except ImportError as e:
            logger.error(f"導入 GroupManager 失敗: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"群組管理模塊導入失敗: {str(e)}"
            )
        
        group_manager = GroupManager(service_manager.account_manager)
        
        # 加入群組
        success = await group_manager.join_group(
            account_id=request.account_id,
            group_username=request.group_username,
            group_id=request.group_id,
            invite_link=request.invite_link
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="加入群組失敗"
            )
        
        # 獲取群組ID
        account = service_manager.account_manager.accounts.get(request.account_id)
        if not account:
            raise HTTPException(status_code=404, detail="賬號不存在")
        
        # 從配置中獲取最後添加的群組ID
        group_id = request.group_id
        if not group_id and account.config.group_ids:
            group_id = account.config.group_ids[-1]
        
        if not group_id:
            raise HTTPException(status_code=400, detail="無法確定群組ID")
        
        # 啟動群聊
        if request.auto_reply:
            chat_success = await group_manager.start_group_chat(
                account_id=request.account_id,
                group_id=group_id,
                auto_reply=True
            )
            if not chat_success:
                logger.warning(f"加入群組成功，但啟動群聊失敗")
        
        # 獲取群組信息
        group_title = None
        if account.client.is_connected:
            try:
                chat = await account.client.get_chat(group_id)
                group_title = chat.title
            except:
                pass
        
        return GroupResponse(
            account_id=request.account_id,
            group_id=group_id,
            group_title=group_title,
            success=True,
            message="加入群組成功並已啟動群聊" if request.auto_reply else "加入群組成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"加入群組失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"加入群組失敗: {str(e)}"
        )


@router.post("/start-chat", response_model=GroupResponse)
async def start_group_chat(
    request: StartGroupChatRequest,
    service_manager: ServiceManager = Depends(get_service_manager)
):
    """啟動群組聊天（開始監聽和自動回復）"""
    try:
        try:
            from group_ai_service.group_manager import GroupManager
        except ImportError as e:
            logger.error(f"導入 GroupManager 失敗: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"群組管理模塊導入失敗: {str(e)}"
            )
        
        group_manager = GroupManager(service_manager.account_manager)
        
        success = await group_manager.start_group_chat(
            account_id=request.account_id,
            group_id=request.group_id,
            auto_reply=request.auto_reply
        )
        
        if success:
            # 獲取群組信息
            account = service_manager.account_manager.accounts.get(request.account_id)
            group_title = None
            if account and account.client.is_connected:
                try:
                    chat = await account.client.get_chat(request.group_id)
                    group_title = chat.title
                except:
                    pass
            
            return GroupResponse(
                account_id=request.account_id,
                group_id=request.group_id,
                group_title=group_title,
                success=True,
                message="群組聊天已啟動"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="啟動群組聊天失敗"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"啟動群組聊天失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"啟動群組聊天失敗: {str(e)}"
        )


