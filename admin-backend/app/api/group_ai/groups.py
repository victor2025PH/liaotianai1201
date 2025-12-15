"""
群組管理API
實現賬號自動創建群組和啟動群聊功能
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
import logging
from sqlalchemy.orm import Session

from group_ai_service.service_manager import ServiceManager
from app.api.group_ai.accounts import get_service_manager
from app.db import get_db
from app.api.deps import get_current_active_user
from app.models.user import User

logger = logging.getLogger(__name__)

# API端点已更新 - 触发重载
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


class SendTestMessageRequest(BaseModel):
    """發送測試消息請求（用於測試按劇本聊天功能）"""
    account_id: str
    group_id: int
    message: str
    wait_for_reply: bool = False
    wait_timeout: int = 10


class SendTestMessageResponse(BaseModel):
    """發送測試消息響應"""
    account_id: str
    group_id: int
    message_id: Optional[int] = None
    success: bool
    message: str
    reply_received: Optional[bool] = None
    reply_count_before: Optional[int] = None
    reply_count_after: Optional[int] = None


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
    db: Session = Depends(get_db)
):
    """
    創建新的Telegram群組（純命令模式）
    
    此函數只負責發送命令到 Worker 節點，不嘗試在服務器端加載 session 文件。
    Worker 節點負責實際的群組創建操作。
    """
    try:
        from app.models.group_ai import GroupAIAccount
        from app.api.workers import _add_command, _get_all_workers
        from datetime import datetime
        
        # 1. 檢查賬號是否存在
        db_account = db.query(GroupAIAccount).filter(
            GroupAIAccount.account_id == request.account_id
        ).first()
        
        if not db_account:
            raise HTTPException(
                status_code=404,
                detail=f"賬號 {request.account_id} 不存在"
            )
        
        # 2. 獲取賬號的 server_id
        server_id = db_account.server_id
        if not server_id:
            raise HTTPException(
                status_code=400,
                detail=f"賬號 {request.account_id} 沒有 server_id，無法確定目標 Worker 節點。請確保 Worker 節點已同步賬號信息。"
            )
        
        # 3. 檢查目標 Worker 節點是否在線
        workers = _get_all_workers()
        target_worker = workers.get(server_id)
        
        if not target_worker or target_worker.get("status") != "online":
            raise HTTPException(
                status_code=400,
                detail=f"目標 Worker 節點 {server_id} 不在線。請確保 Worker 節點正在運行並能連接到服務器。"
            )
        
        # 4. 發送創建群組命令
        command = {
            "action": "create_group",
            "params": {
                "account_id": request.account_id,
                "title": request.title,
                "description": request.description,
                "member_ids": request.member_ids or [],
                "auto_reply": request.auto_reply
            },
            "timestamp": datetime.now().isoformat()
        }
        
        _add_command(server_id, command)
        logger.info(f"發送創建群組命令到節點 {server_id} (賬號: {request.account_id}, 群組名稱: {request.title})")
        
        # 5. 返回響應（注意：實際群組 ID 需要 Worker 節點執行後上報）
        return GroupResponse(
            account_id=request.account_id,
            group_id=0,  # 暫時返回 0，實際 ID 需要 Worker 節點執行後上報
            group_title=request.title,
            success=True,
            message=f"創建群組命令已發送到 Worker 節點 {server_id}。Worker 節點將執行創建操作並上報結果。"
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"發送創建群組命令失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"發送創建群組命令失敗: {str(e)}"
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


@router.get("/{group_id}/invite-link")
async def get_group_invite_link(
    group_id: int,
    account_id: Optional[str] = Query(None, description="用于获取邀请链接的账号ID"),
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取群组邀请链接（純命令模式）
    
    此函數發送命令到 Worker 節點，Worker 節點執行後會上報結果。
    注意：此 API 只發送命令，實際結果需要通過 Worker 節點上報或輪詢獲取。
    """
    try:
        from app.models.group_ai import GroupAIAccount
        from app.api.workers import _add_command, _get_all_workers
        from datetime import datetime
        
        # 1. 如果没有提供account_id，尝试从数据库中找到第一个有该群组的账号
        if not account_id:
            db_account = db.query(GroupAIAccount).filter(
                GroupAIAccount.group_ids.contains([group_id])
            ).first()
            if db_account:
                account_id = db_account.account_id
        
        if not account_id:
            raise HTTPException(
                status_code=404,
                detail="未找到拥有该群组的账号，请提供account_id参数"
            )
        
        # 2. 获取账号信息
        db_account = db.query(GroupAIAccount).filter(
            GroupAIAccount.account_id == account_id
        ).first()
        
        if not db_account:
            raise HTTPException(
                status_code=404,
                detail=f"账号 {account_id} 不存在"
            )
        
        # 3. 获取账号的 server_id
        server_id = db_account.server_id
        if not server_id:
            raise HTTPException(
                status_code=400,
                detail=f"账号 {account_id} 没有 server_id，无法确定目标 Worker 节点"
            )
        
        # 4. 检查目标 Worker 节点是否在线
        workers = _get_all_workers()
        target_worker = workers.get(server_id)
        
        if not target_worker or target_worker.get("status") != "online":
            raise HTTPException(
                status_code=400,
                detail=f"目标 Worker 节点 {server_id} 不在线"
            )
        
        # 5. 发送获取群组链接命令
        command = {
            "action": "get_group_link",
            "params": {
                "account_id": account_id,
                "group_id": group_id
            },
            "timestamp": datetime.now().isoformat()
        }
        
        _add_command(server_id, command)
        logger.info(f"發送獲取群組鏈接命令到節點 {server_id} (賬號: {account_id}, 群組: {group_id})")
        
        # 6. 返回响应（注意：实际链接需要 Worker 节点执行后上报）
        return {
            "success": True,
            "group_id": group_id,
            "account_id": account_id,
            "server_id": server_id,
            "message": f"獲取群組鏈接命令已發送到 Worker 節點 {server_id}。Worker 節點將執行操作並上報結果。",
            "note": "實際的群組鏈接需要通過 Worker 節點上報獲取，或通過輪詢 API 查詢結果。"
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"發送獲取群組鏈接命令失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"發送獲取群組鏈接命令失敗: {str(e)}"
        )


@router.post("/send-test-message", response_model=SendTestMessageResponse)
async def send_test_message(
    request: SendTestMessageRequest,
    service_manager: ServiceManager = Depends(get_service_manager)
):
    """
    發送測試消息到群組（用於測試按劇本聊天功能）
    
    這個API端點允許通過HTTP請求發送測試消息到群組，然後觀察賬號是否按照劇本自動回復。
    這解決了之前無法直接測試按劇本聊天功能的問題。
    """
    try:
        # 獲取賬號
        account = service_manager.account_manager.accounts.get(request.account_id)
        if not account:
            raise HTTPException(status_code=404, detail=f"賬號 {request.account_id} 不存在")
        
        # 檢查賬號狀態
        if account.status.value != "online":
            raise HTTPException(
                status_code=400,
                detail=f"賬號 {request.account_id} 未在線（當前狀態: {account.status.value}）"
            )
        
        # 檢查賬號是否在監聽該群組
        if account.config.group_ids and request.group_id not in account.config.group_ids:
            raise HTTPException(
                status_code=400,
                detail=f"賬號 {request.account_id} 未監聽群組 {request.group_id}"
            )
        
        # 檢查client是否連接
        if not account.client or not account.client.is_connected:
            raise HTTPException(
                status_code=400,
                detail=f"賬號 {request.account_id} 的 Telegram 客戶端未連接"
            )
        
        # 記錄發送前的回復數
        reply_count_before = account.reply_count if hasattr(account, 'reply_count') else 0
        
        # 發送消息
        try:
            sent_message = await account.client.send_message(
                chat_id=request.group_id,
                text=request.message
            )
            message_id = sent_message.id if sent_message else None
            logger.info(f"測試消息已發送（賬號: {request.account_id}, 群組: {request.group_id}, 消息ID: {message_id}）")
        except Exception as e:
            logger.error(f"發送測試消息失敗: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"發送測試消息失敗: {str(e)}"
            )
        
        # 如果需要等待回復
        reply_received = None
        reply_count_after = reply_count_before
        if request.wait_for_reply:
            import asyncio
            logger.info(f"等待回復（超時: {request.wait_timeout}秒）...")
            
            # 等待一段時間，然後檢查回復數是否增加
            for i in range(request.wait_timeout):
                await asyncio.sleep(1)
                reply_count_after = account.reply_count if hasattr(account, 'reply_count') else 0
                if reply_count_after > reply_count_before:
                    reply_received = True
                    logger.info(f"檢測到回復（等待時間: {i+1}秒）")
                    break
            
            if reply_received is None:
                reply_received = False
                reply_count_after = account.reply_count if hasattr(account, 'reply_count') else 0
                logger.info(f"等待超時，未檢測到回復（回復數: {reply_count_before} → {reply_count_after}）")
        
        return SendTestMessageResponse(
            account_id=request.account_id,
            group_id=request.group_id,
            message_id=message_id,
            success=True,
            message="測試消息已發送" + ("，已檢測到回復" if reply_received else "，未檢測到回復" if request.wait_for_reply else ""),
            reply_received=reply_received,
            reply_count_before=reply_count_before,
            reply_count_after=reply_count_after
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"發送測試消息失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"發送測試消息失敗: {str(e)}"
        )


