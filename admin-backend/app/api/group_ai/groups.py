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
    service_manager: ServiceManager = Depends(get_service_manager),
    db: Session = Depends(get_db)
):
    """創建新的Telegram群組並啟動群聊"""
    try:
        from group_ai_service.group_manager import GroupManager
        from app.models.group_ai import GroupAIAccount
        from group_ai_service.models.account import AccountConfig
        from pathlib import Path
        
        # 檢查賬號是否在 AccountManager 中
        account = service_manager.account_manager.accounts.get(request.account_id)
        
        # 如果賬號不在 AccountManager 中，嘗試從數據庫加載
        if not account:
            logger.info(f"賬號 {request.account_id} 不在 AccountManager 中，嘗試從數據庫加載")
            db_account = db.query(GroupAIAccount).filter(
                GroupAIAccount.account_id == request.account_id
            ).first()
            
            if not db_account:
                raise HTTPException(
                    status_code=404,
                    detail=f"賬號 {request.account_id} 不存在"
                )
            
            # 如果賬號在服務器上，需要先加載到本地 AccountManager
            # 注意：這會創建一個本地連接，但實際運行在服務器上
            # 這是一個臨時解決方案，理想情況下應該通過SSH在服務器上執行建群操作
            if db_account.server_id:
                logger.info(f"賬號 {request.account_id} 在服務器 {db_account.server_id} 上，嘗試加載到本地 AccountManager")
                
                # 解析 session 文件路徑
                session_file = db_account.session_file
                session_path = Path(session_file)
                
                # 如果是相對路徑，嘗試從項目根目錄解析
                if not session_path.is_absolute():
                    from group_ai_service.config import get_group_ai_config
                    config_obj = get_group_ai_config()
                    api_file_path = Path(__file__).resolve()
                    project_root = api_file_path.parent.parent.parent.parent.parent
                    sessions_dir = project_root / config_obj.session_files_directory
                    session_path = sessions_dir / Path(session_file).name
                    if session_path.exists():
                        session_file = str(session_path)
                    elif Path(session_file).exists():
                        session_file = str(Path(session_file).resolve())
                
                # 創建配置
                account_config = AccountConfig(
                    account_id=db_account.account_id,
                    session_file=session_file,
                    script_id=db_account.script_id or "default",
                    group_ids=db_account.group_ids or [],
                    active=db_account.active if db_account.active is not None else True,
                    reply_rate=db_account.reply_rate or 0.3,
                    redpacket_enabled=db_account.redpacket_enabled if db_account.redpacket_enabled is not None else True,
                    redpacket_probability=db_account.redpacket_probability or 0.5,
                    max_replies_per_hour=db_account.max_replies_per_hour or 50,
                    min_reply_interval=db_account.min_reply_interval or 3
                )
                
                # 添加到 AccountManager
                try:
                    account = await service_manager.account_manager.add_account(
                        account_id=db_account.account_id,
                        session_file=session_file,
                        config=account_config
                    )
                    logger.info(f"成功從數據庫加載賬號 {request.account_id} 到 AccountManager")
                except Exception as e:
                    logger.error(f"從數據庫加載賬號 {request.account_id} 失敗: {e}", exc_info=True)
                    raise HTTPException(
                        status_code=500,
                        detail=f"從數據庫加載賬號失敗: {str(e)}。請檢查 session 文件是否存在。"
                    )
        
        # 確保賬號在線
        if not account or account.status.value != "online":
            logger.warning(f"賬號 {request.account_id} 未在線，嘗試啟動...")
            # 嘗試啟動賬號
            success = await service_manager.start_account(request.account_id)
            if not success:
                raise HTTPException(
                    status_code=400,
                    detail=f"賬號 {request.account_id} 未在線且啟動失敗。請確保賬號已啟動。"
                )
            # 重新獲取賬號
            account = service_manager.account_manager.accounts.get(request.account_id)
        
        if not account:
            raise HTTPException(
                status_code=404,
                detail=f"賬號 {request.account_id} 不存在或無法加載"
            )
        
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
            
    except HTTPException:
        raise
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


@router.get("/{group_id}/invite-link")
async def get_group_invite_link(
    group_id: int,
    account_id: Optional[str] = Query(None, description="用于获取邀请链接的账号ID"),
    current_user: Optional[User] = Depends(get_current_active_user),
    service_manager: ServiceManager = Depends(get_service_manager),
    db: Session = Depends(get_db)
):
    """
    获取群组邀请链接或用户名
    如果本地没有登录Telegram，返回网页链接
    """
    try:
        from app.models.group_ai import GroupAIAccount
        
        # 如果没有提供account_id，尝试从数据库中找到第一个有该群组的账号
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
        
        # 检查账号是否在AccountManager中
        account = service_manager.account_manager.accounts.get(account_id)
        
        if not account or not account.client or not account.client.is_connected:
            # 账号不在线，返回网页链接（如果知道群组用户名）
            # 或者提示需要登录
            return {
                "success": False,
                "message": "账号未在线，无法获取邀请链接",
                "web_link": None,
                "requires_auth": True,
                "suggestion": "请先启动账号，或使用群组用户名直接访问"
            }
        
        try:
            # 获取群组信息
            chat = await account.client.get_entity(group_id)
            
            # 尝试获取邀请链接
            invite_link = None
            username = None
            
            if hasattr(chat, 'username') and chat.username:
                username = chat.username
                invite_link = f"https://t.me/{username}"
            else:
                # 尝试导出邀请链接
                try:
                    from telethon.tl.functions.messages import ExportChatInviteRequest
                    exported = await account.client(ExportChatInviteRequest(chat))
                    if hasattr(exported, 'link'):
                        invite_link = exported.link
                except Exception as e:
                    logger.warning(f"无法导出邀请链接: {e}")
            
            return {
                "success": True,
                "group_id": group_id,
                "group_title": chat.title if hasattr(chat, 'title') else None,
                "username": username,
                "invite_link": invite_link,
                "web_link": invite_link or (f"https://t.me/c/{str(group_id)[4:]}/{group_id}" if str(group_id).startswith('-100') else None),
                "telegram_link": f"tg://resolve?domain={username}" if username else None,
                "requires_auth": False
            }
        except Exception as e:
            logger.error(f"获取群组信息失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"获取群组信息失败: {str(e)}",
                "web_link": None,
                "requires_auth": True
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取群组邀请链接失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取邀请链接失败: {str(e)}"
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


