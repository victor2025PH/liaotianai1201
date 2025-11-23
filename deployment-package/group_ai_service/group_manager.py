"""
群組管理服務
實現賬號自動創建群組和啟動群聊功能
"""
import logging
import asyncio
from typing import List, Optional, Dict
from pyrogram import Client
from pyrogram.types import Chat, ChatMember
from pyrogram.errors import FloodWait, ChatAdminRequired, UserNotParticipant

logger = logging.getLogger(__name__)


class GroupManager:
    """群組管理器 - 處理群組創建、加入和管理"""
    
    def __init__(self, account_manager):
        self.account_manager = account_manager
        logger.info("GroupManager 初始化完成")
    
    async def create_group(
        self,
        account_id: str,
        title: str,
        description: Optional[str] = None,
        member_ids: Optional[List[int]] = None
    ) -> Optional[int]:
        """
        創建新的Telegram群組
        
        Args:
            account_id: 賬號ID
            title: 群組標題
            description: 群組描述（可選）
            member_ids: 初始成員ID列表（可選）
        
        Returns:
            群組ID（成功）或None（失敗）
        """
        try:
            account = self.account_manager.accounts.get(account_id)
            if not account:
                logger.error(f"賬號 {account_id} 不存在")
                return None
            
            if not account.client.is_connected:
                logger.warning(f"賬號 {account_id} 未連接，嘗試啟動...")
                await account.client.start()
            
            # 創建群組
            if member_ids:
                # 創建群組並添加成員
                chat = await account.client.create_group(
                    title=title,
                    users=member_ids
                )
            else:
                # 創建空群組
                chat = await account.client.create_group(
                    title=title,
                    users=[]  # 創建空群組
                )
            
            group_id = chat.id
            logger.info(f"賬號 {account_id} 成功創建群組: {title} (ID: {group_id})")
            
            # 設置群組描述（如果提供）
            if description:
                try:
                    await account.client.set_chat_description(group_id, description)
                except Exception as e:
                    logger.warning(f"設置群組描述失敗: {e}")
            
            # 更新賬號配置，將新群組添加到監聽列表
            if group_id not in account.config.group_ids:
                account.config.group_ids.append(group_id)
                logger.info(f"已將群組 {group_id} 添加到賬號 {account_id} 的監聽列表")
            
            return group_id
            
        except FloodWait as e:
            logger.warning(f"創建群組觸發FloodWait，等待 {e.value} 秒")
            await asyncio.sleep(e.value)
            # 重試一次
            return await self.create_group(account_id, title, description, member_ids)
        except Exception as e:
            logger.error(f"創建群組失敗: {e}")
            return None
    
    async def join_group(
        self,
        account_id: str,
        group_username: Optional[str] = None,
        group_id: Optional[int] = None,
        invite_link: Optional[str] = None
    ) -> bool:
        """
        加入Telegram群組
        
        Args:
            account_id: 賬號ID
            group_username: 群組用戶名（例如：@groupname）
            group_id: 群組ID（例如：-1001234567890）
            invite_link: 邀請鏈接
        
        Returns:
            是否成功加入
        """
        try:
            account = self.account_manager.accounts.get(account_id)
            if not account:
                logger.error(f"賬號 {account_id} 不存在")
                return False
            
            if not account.client.is_connected:
                logger.warning(f"賬號 {account_id} 未連接，嘗試啟動...")
                await account.client.start()
            
            # 根據提供的參數加入群組
            if invite_link:
                # 通過邀請鏈接加入
                chat = await account.client.join_chat(invite_link)
            elif group_username:
                # 通過用戶名加入
                chat = await account.client.join_chat(group_username)
            elif group_id:
                # 通過ID加入（需要先獲取群組信息）
                chat = await account.client.get_chat(group_id)
                if chat.type.name == "PRIVATE":
                    logger.error(f"無法加入私人群組: {group_id}")
                    return False
            else:
                logger.error("必須提供 group_username、group_id 或 invite_link 之一")
                return False
            
            group_id = chat.id
            logger.info(f"賬號 {account_id} 成功加入群組: {chat.title} (ID: {group_id})")
            
            # 更新賬號配置，將群組添加到監聽列表
            if group_id not in account.config.group_ids:
                account.config.group_ids.append(group_id)
                logger.info(f"已將群組 {group_id} 添加到賬號 {account_id} 的監聽列表")
            
            return True
            
        except FloodWait as e:
            logger.warning(f"加入群組觸發FloodWait，等待 {e.value} 秒")
            await asyncio.sleep(e.value)
            # 重試一次
            return await self.join_group(account_id, group_username, group_id, invite_link)
        except UserNotParticipant:
            logger.error(f"賬號 {account_id} 無法加入群組（未參與）")
            return False
        except Exception as e:
            logger.error(f"加入群組失敗: {e}")
            return False
    
    async def start_group_chat(
        self,
        account_id: str,
        group_id: int,
        auto_reply: bool = True
    ) -> bool:
        """
        啟動群組聊天（開始監聽和自動回復）
        
        Args:
            account_id: 賬號ID
            group_id: 群組ID
            auto_reply: 是否啟用自動回復
        
        Returns:
            是否成功啟動
        """
        try:
            account = self.account_manager.accounts.get(account_id)
            if not account:
                logger.error(f"賬號 {account_id} 不存在")
                return False
            
            # 確保群組在監聽列表中
            if group_id not in account.config.group_ids:
                account.config.group_ids.append(group_id)
                logger.info(f"已將群組 {group_id} 添加到賬號 {account_id} 的監聽列表")
            
            # 如果賬號未啟動，先啟動
            if account.status.value != "online":
                logger.info(f"賬號 {account_id} 未啟動，正在啟動...")
                from group_ai_service.service_manager import ServiceManager
                service_manager = ServiceManager.get_instance()
                success = await service_manager.start_account(account_id)
                if not success:
                    logger.error(f"啟動賬號 {account_id} 失敗")
                    return False
            
            # 確保賬號已連接
            if not account.client.is_connected:
                await account.client.start()
            
            # 驗證群組存在且賬號是成員
            try:
                chat = await account.client.get_chat(group_id)
                logger.info(f"賬號 {account_id} 已準備好在群組 {chat.title} (ID: {group_id}) 中開始聊天")
            except Exception as e:
                logger.error(f"無法訪問群組 {group_id}: {e}")
                return False
            
            # 如果啟用了自動回復，確保會話池已啟動
            if auto_reply:
                try:
                    from group_ai_service.service_manager import ServiceManager
                    service_manager = ServiceManager.get_instance()
                    if not service_manager.session_pool:
                        # 嘗試初始化會話池
                        if hasattr(service_manager, '_init_session_pool'):
                            service_manager.session_pool = service_manager._init_session_pool()
                        else:
                            # 如果沒有_init_session_pool方法，嘗試直接創建
                            from group_ai_service.session_pool import ExtendedSessionPool
                            service_manager.session_pool = ExtendedSessionPool(service_manager.account_manager)
                    
                    if service_manager.session_pool:
                        # 確保賬號在會話池中監聽
                        if hasattr(service_manager.session_pool, 'start_monitoring_account'):
                            await service_manager.session_pool.start_monitoring_account(account_id)
                            logger.info(f"賬號 {account_id} 已開始監聽群組 {group_id} 的消息")
                        else:
                            logger.warning(f"會話池不支持 start_monitoring_account 方法")
                except Exception as e:
                    logger.warning(f"啟動會話池時出錯: {e}，群組聊天可能無法自動回復")
            
            logger.info(f"賬號 {account_id} 已成功啟動群組聊天 (群組ID: {group_id})")
            return True
            
        except Exception as e:
            logger.error(f"啟動群組聊天失敗: {e}")
            return False
    
    async def create_and_start_group(
        self,
        account_id: str,
        title: str,
        description: Optional[str] = None,
        member_ids: Optional[List[int]] = None,
        auto_reply: bool = True
    ) -> Optional[int]:
        """
        創建群組並立即啟動群聊（一站式功能）
        
        Args:
            account_id: 賬號ID
            title: 群組標題
            description: 群組描述（可選）
            member_ids: 初始成員ID列表（可選）
            auto_reply: 是否啟用自動回復
        
        Returns:
            群組ID（成功）或None（失敗）
        """
        # 1. 創建群組
        group_id = await self.create_group(account_id, title, description, member_ids)
        
        if not group_id:
            return None
        
        # 2. 啟動群聊
        success = await self.start_group_chat(account_id, group_id, auto_reply)
        
        if success:
            logger.info(f"賬號 {account_id} 已成功創建並啟動群組: {title} (ID: {group_id})")
            return group_id
        else:
            logger.warning(f"群組 {group_id} 創建成功，但啟動群聊失敗")
            return group_id  # 仍然返回群組ID，因為群組已創建

