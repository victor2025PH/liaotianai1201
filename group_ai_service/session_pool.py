"""
擴展會話池 - 支持多賬號並行運行
基於現有的 session_service/session_pool.py 擴展
"""
import asyncio
import logging
from typing import Dict, List, Optional, Callable, Awaitable
from pathlib import Path

from pyrogram import Client
from pyrogram.types import Message

from group_ai_service.account_manager import AccountManager, AccountInstance
from group_ai_service.models.account import AccountConfig
from group_ai_service.dialogue_manager import DialogueManager

logger = logging.getLogger(__name__)


class ExtendedSessionPool:
    """擴展的會話池，支持多賬號並行管理"""
    
    def __init__(self, account_manager: AccountManager, dialogue_manager: Optional[DialogueManager] = None):
        self.account_manager = account_manager
        self.dialogue_manager = dialogue_manager
        self._message_handlers: Dict[str, List[Callable]] = {}
        self._running = False
        self._tasks: List[asyncio.Task] = []
        logger.info("ExtendedSessionPool 初始化完成")
    
    async def start(self):
        """啟動會話池"""
        if self._running:
            logger.warning("會話池已在運行")
            return
        
        self._running = True
        logger.info("啟動會話池...")
        
        # 為每個賬號啟動消息監聽任務
        accounts = self.account_manager.list_accounts()
        for account_info in accounts:
            if account_info.status.value == "online":
                await self.start_monitoring_account(account_info.account_id)
        
        logger.info(f"會話池已啟動，監聽 {len(self._tasks)} 個賬號")
    
    async def start_monitoring_account(self, account_id: str):
        """為指定賬號啟動消息監聽"""
        # 檢查是否已經在監聽
        for task in self._tasks:
            if task.get_name() == f"monitor-{account_id}":
                if not task.done():
                    logger.debug(f"賬號 {account_id} 已在監聽中")
                    return
        
        # 檢查賬號是否在線
        account = self.account_manager.accounts.get(account_id)
        if not account or account.status.value != "online":
            logger.warning(f"賬號 {account_id} 不在線，無法啟動監聽")
            return
        
        # 啟動監聽任務
        task = asyncio.create_task(
            self._monitor_account(account_id),
            name=f"monitor-{account_id}"
        )
        self._tasks.append(task)
        logger.info(f"已為賬號 {account_id} 啟動消息監聽")
    
    async def stop(self):
        """停止會話池"""
        if not self._running:
            return
        
        self._running = False
        logger.info("停止會話池...")
        
        # 取消所有任務
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
        logger.info("會話池已停止")
    
    def register_message_handler(
        self,
        account_id: Optional[str],
        handler: Callable[[AccountInstance, Message], Awaitable[None]]
    ):
        """註冊消息處理器
        
        Args:
            account_id: 賬號 ID，None 表示所有賬號
            handler: 消息處理函數
        """
        if account_id not in self._message_handlers:
            self._message_handlers[account_id] = []
        self._message_handlers[account_id].append(handler)
        logger.info(f"註冊消息處理器: account_id={account_id}")
    
    async def _monitor_account(self, account_id: str):
        """監聽指定賬號的消息"""
        account = self.account_manager.accounts.get(account_id)
        if not account or not account.client:
            logger.error(f"賬號 {account_id} 不存在或未初始化")
            return
        
        client = account.client
        
        @client.on_message()
        async def handle_message(client: Client, message: Message):
            """處理接收到的消息"""
            await self._handle_message(account, message, account_id)
        
        # 處理 callback query（用於處理紅包按鈕點擊）
        @client.on_callback_query()
        async def handle_callback_query(client: Client, callback_query):
            """處理回調查詢（按鈕點擊）"""
            await self._handle_callback_query(account, client, callback_query, account_id)
        
        # 保持連接
        try:
            await client.idle()
        except asyncio.CancelledError:
            logger.info(f"賬號 {account_id} 監聽任務已取消")
        except Exception as e:
            logger.exception(f"賬號 {account_id} 監聽任務異常: {e}")
    
    async def _handle_message(self, account: AccountInstance, message: Message, account_id: str):
        """處理接收到的消息（提取的邏輯，便於測試）"""
        try:
            # 只處理群組消息
            if not message.chat or message.chat.type.name != "GROUP":
                return
            
            # 檢查是否在監聽的群組列表中
            if account.config.group_ids and message.chat.id not in account.config.group_ids:
                return
            
            # 更新賬號活動時間
            from datetime import datetime
            account.last_activity = datetime.now()
            account.message_count += 1
            
            # 如果有對話管理器，優先使用對話管理器處理
            if self.dialogue_manager:
                try:
                    reply = await self.dialogue_manager.process_message(
                        account_id=account.account_id,
                        group_id=message.chat.id,
                        message=message,
                        account_config=account.config
                    )
                    if reply:
                        await message.reply_text(reply)
                        account.reply_count += 1
                        logger.info(f"已發送回復（賬號: {account.account_id}, 群組: {message.chat.id}）")
                except Exception as e:
                    logger.exception(f"對話管理器處理失敗: {e}")
                    account.error_count += 1
            
            # 調用註冊的處理器（作為備用）
            await self._dispatch_message(account, message)
            
        except Exception as e:
            logger.exception(f"處理消息失敗 (account={account_id}): {e}")
            account.error_count += 1
    
    async def _handle_callback_query(
        self,
        account: AccountInstance,
        client: Client,
        callback_query,
        account_id: str
    ):
        """處理回調查詢（按鈕點擊）（提取的邏輯，便於測試）"""
        try:
            # 只處理群組中的回調
            if not callback_query.message or not callback_query.message.chat:
                return
            
            if callback_query.message.chat.type.name != "GROUP":
                return
            
            # 檢查是否在監聽的群組列表中
            if account.config.group_ids and callback_query.message.chat.id not in account.config.group_ids:
                return
            
            # 更新賬號活動時間
            from datetime import datetime
            account.last_activity = datetime.now()
            
            # 處理紅包按鈕點擊
            callback_data = callback_query.data or ""
            if callback_data.startswith("hb:grab:"):
                # 這是紅包按鈕
                envelope_id = callback_data.split(":")[-1]
                logger.info(f"檢測到紅包按鈕點擊: envelope_id={envelope_id}, account={account.account_id}")
                
                # 如果有對話管理器，處理紅包參與
                if self.dialogue_manager and self.dialogue_manager.redpacket_handler:
                    try:
                        # 創建一個模擬的 Message 對象用於檢測
                        message = callback_query.message
                        
                        # 檢測紅包
                        redpacket = await self.dialogue_manager.redpacket_handler.detect_redpacket(message)
                        if redpacket:
                            # 獲取對話上下文（通過 DialogueManager）
                            context_key = f"{account.account_id}:{callback_query.message.chat.id}"
                            context = self.dialogue_manager.contexts.get(context_key)
                            
                            # 檢查是否應該參與
                            should_participate = await self.dialogue_manager.redpacket_handler.should_participate(
                                account_id=account.account_id,
                                redpacket=redpacket,
                                account_config=account.config,
                                context=context
                            )
                            
                            if should_participate:
                                # 獲取發包人信息（從消息中）
                                sender_name = None
                                if message.from_user:
                                    sender_name = getattr(message.from_user, 'first_name', None) or getattr(message.from_user, 'username', None)
                                
                                # 獲取參與者信息（當前賬號的用戶名）
                                participant_name = None
                                try:
                                    me = await client.get_me()
                                    if me:
                                        participant_name = me.first_name or me.username
                                except Exception as e:
                                    logger.debug(f"獲取參與者名稱失敗: {e}")
                                
                                # 參與紅包
                                result = await self.dialogue_manager.redpacket_handler.participate(
                                    account_id=account.account_id,
                                    redpacket=redpacket,
                                    client=client,
                                    sender_name=sender_name,
                                    participant_name=participant_name
                                )
                                
                                if result.success:
                                    logger.info(f"成功參與紅包: {redpacket.redpacket_id}, 金額: {result.amount}")
                                else:
                                    logger.warning(f"參與紅包失敗: {result.error}")
                    except Exception as e:
                        logger.exception(f"處理紅包按鈕點擊失敗: {e}")
                        account.error_count += 1
            
        except Exception as e:
            logger.exception(f"處理回調查詢失敗 (account={account_id}): {e}")
            account.error_count += 1
    
    async def _dispatch_message(self, account: AccountInstance, message: Message):
        """分發消息到註冊的處理器"""
        # 調用賬號特定的處理器
        if account.account_id in self._message_handlers:
            for handler in self._message_handlers[account.account_id]:
                try:
                    await handler(account, message)
                except Exception as e:
                    logger.exception(f"處理器執行失敗: {e}")
        
        # 調用全局處理器（account_id=None）
        if None in self._message_handlers:
            for handler in self._message_handlers[None]:
                try:
                    await handler(account, message)
                except Exception as e:
                    logger.exception(f"全局處理器執行失敗: {e}")
    
    def get_client(self, account_id: str) -> Optional[Client]:
        """獲取指定賬號的 Client"""
        account = self.account_manager.accounts.get(account_id)
        return account.client if account else None
    
    def get_account_by_group(self, group_id: int) -> List[AccountInstance]:
        """根據群組 ID 獲取監聽該群組的所有賬號"""
        result = []
        for account in self.account_manager.accounts.values():
            if not account.config.group_ids or group_id in account.config.group_ids:
                result.append(account)
        return result
    
    @property
    def active_accounts(self) -> List[str]:
        """獲取所有活躍賬號 ID"""
        return [
            account_id
            for account_id, account in self.account_manager.accounts.items()
            if account.status.value == "online"
        ]

