"""
統一消息處理中心
整合所有消息處理邏輯，消除重複代碼
"""
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict

from pyrogram.types import Message, Chat, Channel

from group_ai_service.models.account import AccountConfig
from group_ai_service.redpacket_handler import RedpacketHandler, RedpacketInfo, RedpacketResult
from group_ai_service.dialogue_manager import DialogueManager, DialogueContext

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息類型"""
    GROUP_MESSAGE = "group_message"
    PRIVATE_MESSAGE = "private_message"
    SYSTEM_MESSAGE = "system_message"
    CHANNEL_MESSAGE = "channel_message"


class ProcessingPriority(Enum):
    """處理優先級"""
    REDPACKET = 1      # 紅包處理（最高優先級）
    KEYWORD_TRIGGER = 2  # 關鍵詞觸發
    SCHEDULED_MESSAGE = 3  # 定時消息
    DIALOGUE = 4      # 對話處理
    OTHER = 5         # 其他處理


@dataclass
class MessageContext:
    """消息上下文"""
    account_id: str
    group_id: Optional[int] = None
    message: Optional[Message] = None
    chat: Optional[Chat] = None
    message_type: MessageType = MessageType.GROUP_MESSAGE
    account_config: Optional[AccountConfig] = None
    dialogue_context: Optional[DialogueContext] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProcessingResult:
    """處理結果"""
    success: bool
    action_taken: bool  # 是否執行了動作
    action_type: Optional[str] = None  # 動作類型（send_message, grab_redpacket等）
    result_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    skip_further_processing: bool = False  # 是否跳過後續處理


class MessageRouter:
    """消息路由器 - 分類和過濾消息"""
    
    def __init__(self, rate_limiter=None):
        """
        初始化消息路由器
        
        Args:
            rate_limiter: MessageRateLimiter 實例（可選）
        """
        self.logger = logging.getLogger(__name__)
        self.blacklist_users: set = set()  # 黑名單用戶
        self.blacklist_groups: set = set()  # 黑名單群組
        
        # 初始化頻率限制器（如果未提供，創建默認實例）
        if rate_limiter is None:
            from group_ai_service.rate_limiter import MessageRateLimiter
            self.rate_limiter = MessageRateLimiter()
        else:
            self.rate_limiter = rate_limiter
        
    def classify_message(self, message: Message, chat: Chat, account_id: str) -> Optional[MessageContext]:
        """
        分類消息
        
        Returns:
            MessageContext 或 None（如果消息應該被過濾）
        """
        # 檢查是否是自己的消息
        if message.from_user and message.from_user.id == account_id:
            return None
        
        # 檢查黑名單
        if message.from_user and message.from_user.id in self.blacklist_users:
            self.logger.debug(f"消息來自黑名單用戶: {message.from_user.id}")
            return None
        
        # 判斷消息類型
        if isinstance(chat, Channel):
            message_type = MessageType.CHANNEL_MESSAGE
        elif isinstance(chat, Chat):
            if chat.type.name == "PRIVATE":
                message_type = MessageType.PRIVATE_MESSAGE
            else:
                message_type = MessageType.GROUP_MESSAGE
        else:
            message_type = MessageType.SYSTEM_MESSAGE
        
        # 檢查群組黑名單
        if message_type == MessageType.GROUP_MESSAGE and chat.id in self.blacklist_groups:
            self.logger.debug(f"消息來自黑名單群組: {chat.id}")
            return None
        
        return MessageContext(
            account_id=account_id,
            group_id=chat.id if message_type in [MessageType.GROUP_MESSAGE, MessageType.CHANNEL_MESSAGE] else None,
            message=message,
            chat=chat,
            message_type=message_type
        )
    
    def should_process(self, context: MessageContext, account_config: AccountConfig) -> bool:
        """判斷是否應該處理消息"""
        # 檢查賬號是否啟用
        if not account_config.active:
            return False
        
        # 檢查頻率限制
        if self.rate_limiter:
            allowed, error_msg = self.rate_limiter.check_rate_limit(
                account_id=context.account_id,
                group_id=context.group_id
            )
            
            if not allowed:
                self.logger.debug(
                    f"消息處理被頻率限制阻止: {error_msg} "
                    f"(賬號: {context.account_id}, 群組: {context.group_id})"
                )
                return False
            
            # 記錄消息處理（在實際處理前記錄，避免重複記錄）
            # 注意：這裡只檢查，實際記錄在 handle_message 中進行
        
        return True


class RedpacketProcessor:
    """紅包處理器 - 統一紅包檢測和處理邏輯"""
    
    def __init__(self, redpacket_handler: Optional[RedpacketHandler] = None):
        self.logger = logging.getLogger(__name__)
        self.redpacket_handler = redpacket_handler
        
        # 統一的紅包關鍵詞列表（消除重複）
        self.redpacket_keywords = [
            "紅包", "红包", "🧧", "💰", "發紅包", "发红包",
            "搶紅包", "抢红包", "紅包來了", "红包来了",
            "lucky", "packet", "hongbao", "startapp=p_"
        ]
        
        # 統一的紅包 UUID 提取模式
        self.uuid_patterns = [
            r'startapp=p_([a-f0-9-]{36})',
            r'packet[s]?/([a-f0-9-]{36})',
            r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',
        ]
    
    def is_redpacket_message(self, message: Message) -> bool:
        """
        統一檢測是否是紅包消息
        
        替代所有重複的 is_redpacket_message() 方法
        """
        text = message.text or ""
        text_lower = text.lower()
        
        # 檢查關鍵詞
        if any(keyword.lower() in text_lower for keyword in self.redpacket_keywords):
            return True
        
        # 檢查是否包含 UUID 模式
        import re
        for pattern in self.uuid_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # 檢查消息按鈕（紅包按鈕）
        if hasattr(message, 'reply_markup') and message.reply_markup:
            if hasattr(message.reply_markup, 'inline_keyboard'):
                for row in message.reply_markup.inline_keyboard:
                    for button in row:
                        callback_data = getattr(button, 'callback_data', '') or ''
                        if 'grab' in callback_data.lower() or 'redpacket' in callback_data.lower():
                            return True
        
        # 檢查遊戲消息
        if hasattr(message, 'game') and message.game:
            return True
        
        return False
    
    def extract_packet_uuid(self, message: Message) -> Optional[str]:
        """
        統一提取紅包 UUID
        
        替代所有重複的 extract_packet_uuid() 方法
        """
        text = message.text or ""
        import re
        
        for pattern in self.uuid_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # 從按鈕 callback_data 提取
        if hasattr(message, 'reply_markup') and message.reply_markup:
            if hasattr(message.reply_markup, 'inline_keyboard'):
                for row in message.reply_markup.inline_keyboard:
                    for button in row:
                        callback_data = getattr(button, 'callback_data', '') or ''
                        # 檢查格式：hb:grab:{envelope_id}
                        match = re.match(r'^hb:grab:(\d+)$', callback_data)
                        if match:
                            return match.group(1)
        
        return None
    
    async def process_redpacket(
        self,
        context: MessageContext,
        account_config: AccountConfig
    ) -> Optional[ProcessingResult]:
        """
        處理紅包消息
        
        Returns:
            ProcessingResult 或 None（如果不是紅包消息）
        """
        if not self.is_redpacket_message(context.message):
            return None
        
        # 檢查是否啟用自動搶紅包
        if not account_config.redpacket_enabled:
            self.logger.debug(f"賬號 {context.account_id} 未啟用紅包功能")
            return ProcessingResult(
                success=True,
                action_taken=False,
                skip_further_processing=False
            )
        
        # 提取紅包信息
        packet_uuid = self.extract_packet_uuid(context.message)
        if not packet_uuid:
            self.logger.debug(f"無法提取紅包 UUID: {context.message.id}")
            return ProcessingResult(
                success=True,
                action_taken=False,
                skip_further_processing=False
            )
        
        # 使用 RedpacketHandler 處理
        if self.redpacket_handler:
            try:
                redpacket_info = RedpacketInfo(
                    redpacket_id=packet_uuid,
                    group_id=context.group_id or 0,
                    sender_id=context.message.from_user.id if context.message.from_user else 0,
                    message_id=context.message.id,
                    timestamp=datetime.now()
                )
                
                # 評估是否應該搶奪（使用 should_participate 方法）
                should_grab = await self.redpacket_handler.should_participate(
                    account_id=context.account_id,
                    redpacket=redpacket_info,
                    account_config=account_config,
                    context=context.dialogue_context
                )
                
                if should_grab:
                    # 獲取賬號的 client（從 account_manager 獲取）
                    client = None
                    if self.action_executor.account_manager:
                        account = self.action_executor.account_manager.accounts.get(context.account_id)
                        if account and hasattr(account, 'client'):
                            client = account.client
                    
                    if client:
                        # 執行搶奪（使用 participate 方法）
                        result = await self.redpacket_handler.participate(
                            account_id=context.account_id,
                            redpacket=redpacket_info,
                            client=client
                        )
                    else:
                        self.logger.warning(f"無法獲取賬號 {context.account_id} 的 client，跳過搶紅包")
                        result = None
                    
                    # 轉換 RedpacketResult 為 ProcessingResult
                    if result:
                        return ProcessingResult(
                            success=result.success,
                            action_taken=True,
                            action_type="grab_redpacket",
                            result_data={
                                "redpacket_id": packet_uuid,
                                "amount": result.amount,
                                "error": result.error
                            },
                            skip_further_processing=False  # 搶紅包後仍可繼續處理其他邏輯
                        )
                    else:
                        return ProcessingResult(
                            success=False,
                            action_taken=False,
                            error="無法獲取 client",
                            skip_further_processing=False
                        )
                else:
                    self.logger.debug(f"策略決定不搶奪紅包: {packet_uuid}")
                    return ProcessingResult(
                        success=True,
                        action_taken=False,
                        skip_further_processing=False
                    )
                    
            except Exception as e:
                self.logger.error(f"處理紅包失敗: {e}", exc_info=True)
                return ProcessingResult(
                    success=False,
                    action_taken=False,
                    error=str(e),
                    skip_further_processing=False
                )
        
        return ProcessingResult(
            success=True,
            action_taken=False,
            skip_further_processing=False
        )


class KeywordTriggerProcessor:
    """關鍵詞觸發處理器"""
    
    def __init__(self, keyword_trigger_service=None):
        """
        初始化關鍵詞觸發處理器
        
        Args:
            keyword_trigger_service: KeywordTriggerProcessor 實例（從 keyword_trigger_processor.py）
        """
        self.logger = logging.getLogger(__name__)
        self.keyword_trigger_service = keyword_trigger_service
        
    async def process_keyword_trigger(
        self,
        context: MessageContext,
        account_config: AccountConfig
    ) -> Optional[ProcessingResult]:
        """
        處理關鍵詞觸發
        
        Returns:
            ProcessingResult 或 None（如果沒有匹配的關鍵詞）
        """
        if not self.keyword_trigger_service:
            return None
        
        try:
            # 使用 keyword_trigger_processor 處理
            from group_ai_service.keyword_trigger_processor import KeywordTriggerProcessor as KTP
            if isinstance(self.keyword_trigger_service, KTP):
                result = await self.keyword_trigger_service.process_message(
                    account_id=context.account_id,
                    group_id=context.group_id or 0,
                    message=context.message
                )
                
                if result:
                    # 返回處理結果
                    return ProcessingResult(
                        success=True,
                        action_taken=True,
                        action_type="keyword_trigger",
                        result_data={
                            "rule_id": result.get("rule_id"),
                            "rule_name": result.get("rule_name"),
                            "actions": result.get("actions", []),
                        },
                        skip_further_processing=False  # 關鍵詞觸發後仍可繼續處理其他邏輯
                    )
        except Exception as e:
            self.logger.error(f"處理關鍵詞觸發失敗: {e}", exc_info=True)
        
        return None


class ScheduledMessageProcessor:
    """定時消息處理器（在統一消息處理中心中的包裝）"""
    
    def __init__(self, scheduled_message_service=None):
        """
        初始化定時消息處理器
        
        Args:
            scheduled_message_service: ScheduledMessageProcessor 實例（從 scheduled_message_processor.py）
        """
        self.logger = logging.getLogger(__name__)
        self.scheduled_message_service = scheduled_message_service
        
    async def process_scheduled_message(
        self,
        context: MessageContext,
        account_config: AccountConfig
    ) -> Optional[ProcessingResult]:
        """
        處理定時消息
        
        注意：定時消息通常由後台任務調度器處理，此處主要用於檢查是否有立即需要發送的消息
        
        Returns:
            ProcessingResult 或 None（如果沒有定時消息需要發送）
        """
        # 定時消息通常由後台任務調度器處理，不在消息處理流程中處理
        # 此方法保留用於未來可能的即時觸發場景
        return None


class DialogueProcessor:
    """對話處理器 - 整合劇本引擎和 LLM"""
    
    def __init__(self, dialogue_manager: Optional[DialogueManager] = None):
        self.logger = logging.getLogger(__name__)
        self.dialogue_manager = dialogue_manager
        
    async def process_dialogue(
        self,
        context: MessageContext,
        account_config: AccountConfig
    ) -> Optional[ProcessingResult]:
        """
        處理對話，生成回復
        
        Returns:
            ProcessingResult 或 None（如果不應該回復）
        """
        if not self.dialogue_manager:
            return None
        
        try:
            # 使用 DialogueManager 處理消息
            reply_text = await self.dialogue_manager.process_message(
                account_id=context.account_id,
                group_id=context.group_id or 0,
                message=context.message,
                account_config=account_config
            )
            
            if reply_text:
                return ProcessingResult(
                    success=True,
                    action_taken=True,
                    action_type="send_message",
                    result_data={
                        "message": reply_text,
                        "group_id": context.group_id
                    },
                    skip_further_processing=False
                )
            else:
                return ProcessingResult(
                    success=True,
                    action_taken=False,
                    skip_further_processing=False
                )
                
        except Exception as e:
            self.logger.error(f"處理對話失敗: {e}", exc_info=True)
            return ProcessingResult(
                success=False,
                action_taken=False,
                error=str(e),
                skip_further_processing=False
            )


class ActionExecutor:
    """動作執行器 - 統一執行各種動作"""
    
    def __init__(self, account_manager=None):
        """
        初始化動作執行器
        
        Args:
            account_manager: AccountManager 實例，用於獲取 Telegram Client
        """
        self.logger = logging.getLogger(__name__)
        self.account_manager = account_manager
        
    async def execute_action(
        self,
        action_type: str,
        context: MessageContext,
        action_data: Dict[str, Any],
        account_manager=None
    ) -> bool:
        """
        執行動作
        
        Args:
            action_type: 動作類型（send_message, join_group, leave_group等）
            context: 消息上下文
            action_data: 動作數據
            account_manager: AccountManager 實例（可選，如果未在初始化時提供）
            
        Returns:
            是否執行成功
        """
        # 使用傳入的 account_manager 或初始化時的
        manager = account_manager or self.account_manager
        
        try:
            if action_type == "send_message":
                return await self._send_message(context, action_data, manager)
            elif action_type == "join_group":
                return await self._join_group(context, action_data, manager)
            elif action_type == "leave_group":
                return await self._leave_group(context, action_data, manager)
            elif action_type == "forward_message":
                return await self._forward_message(context, action_data, manager)
            elif action_type == "delete_message":
                return await self._delete_message(context, action_data, manager)
            elif action_type == "grab_redpacket":
                # 紅包搶奪已在 RedpacketProcessor 中處理
                return True
            else:
                self.logger.warning(f"未知的動作類型: {action_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"執行動作失敗: {action_type}: {e}", exc_info=True)
            return False
    
    async def _send_message(
        self,
        context: MessageContext,
        action_data: Dict[str, Any],
        account_manager
    ) -> bool:
        """發送消息"""
        message = action_data.get("message")
        group_id = action_data.get("group_id") or context.group_id
        account_id = action_data.get("account_id") or context.account_id
        
        if not message or not group_id or not account_id:
            self.logger.warning(f"發送消息參數不完整: message={bool(message)}, group_id={group_id}, account_id={account_id}")
            return False
        
        # 從 account_manager 獲取 client
        if not account_manager:
            self.logger.error("AccountManager 未提供，無法發送消息")
            return False
        
        try:
            account = account_manager.accounts.get(account_id)
            if not account or not account.client:
                self.logger.error(f"賬號 {account_id} 不存在或未初始化")
                return False
            
            # 添加延遲（如果指定）
            delay = action_data.get("delay", 0)
            if delay > 0:
                import random
                if isinstance(delay, (list, tuple)) and len(delay) == 2:
                    delay = random.uniform(delay[0], delay[1])
                await asyncio.sleep(delay)
            
            # 發送消息
            try:
                await account.client.send_message(group_id, message)
                self.logger.info(f"已發送消息到群組 {group_id} (賬號: {account_id}): {message[:50]}...")
                return True
            except Exception as send_error:
                self.logger.error(f"發送消息到群組 {group_id} 失敗: {send_error}", exc_info=True)
                return False
            
        except Exception as e:
            self.logger.error(f"發送消息失敗: {e}", exc_info=True)
            return False
    
    async def _join_group(
        self,
        context: MessageContext,
        action_data: Dict[str, Any],
        account_manager
    ) -> bool:
        """加入群組"""
        group_id = action_data.get("group_id")
        invite_link = action_data.get("invite_link")
        username = action_data.get("username")
        account_id = action_data.get("account_id") or context.account_id
        
        if not account_id:
            return False
        
        if not account_manager:
            self.logger.error("AccountManager 未提供，無法加入群組")
            return False
        
        try:
            account = account_manager.accounts.get(account_id)
            if not account or not account.client:
                self.logger.error(f"賬號 {account_id} 不存在或未初始化")
                return False
            
            client = account.client
            
            # 根據提供的信息加入群組
            if invite_link:
                # 通過邀請鏈接加入
                await client.join_chat(invite_link)
                self.logger.info(f"賬號 {account_id} 已通過邀請鏈接加入群組: {invite_link}")
            elif username:
                # 通過用戶名加入
                await client.join_chat(username)
                self.logger.info(f"賬號 {account_id} 已通過用戶名加入群組: {username}")
            elif group_id:
                # 通過群組 ID 加入（需要先獲取群組信息）
                # TODO: 實現通過群組 ID 加入
                self.logger.warning("通過群組 ID 加入尚未實現")
                return False
            else:
                self.logger.warning("加入群組參數不完整")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"加入群組失敗: {e}", exc_info=True)
            return False
    
    async def _leave_group(
        self,
        context: MessageContext,
        action_data: Dict[str, Any],
        account_manager
    ) -> bool:
        """離開群組"""
        group_id = action_data.get("group_id") or context.group_id
        account_id = action_data.get("account_id") or context.account_id
        
        if not group_id or not account_id:
            return False
        
        if not account_manager:
            self.logger.error("AccountManager 未提供，無法離開群組")
            return False
        
        try:
            account = account_manager.accounts.get(account_id)
            if not account or not account.client:
                self.logger.error(f"賬號 {account_id} 不存在或未初始化")
                return False
            
            await account.client.leave_chat(group_id)
            self.logger.info(f"賬號 {account_id} 已離開群組: {group_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"離開群組失敗: {e}", exc_info=True)
            return False
    
    async def _forward_message(
        self,
        context: MessageContext,
        action_data: Dict[str, Any],
        account_manager
    ) -> bool:
        """轉發消息"""
        target_group_id = action_data.get("target_group_id")
        target_account_id = action_data.get("target_account_id")
        message_id = action_data.get("message_id") or (context.message.id if context.message else None)
        
        if not message_id:
            return False
        
        # 轉發到群組
        if target_group_id:
            account_id = action_data.get("account_id") or context.account_id
            if not account_manager:
                return False
            
            try:
                account = account_manager.accounts.get(account_id)
                if not account or not account.client:
                    return False
                
                await account.client.forward_messages(
                    target_group_id,
                    context.group_id or 0,
                    message_id
                )
                self.logger.info(f"已轉發消息 {message_id} 到群組 {target_group_id}")
                return True
            except Exception as e:
                self.logger.error(f"轉發消息失敗: {e}", exc_info=True)
                return False
        
        # 轉發到私聊
        elif target_account_id:
            # target_account_id 可以是用戶 ID（整數）或用戶名（字符串）
            account_id = action_data.get("account_id") or context.account_id
            if not account_manager:
                return False
            
            try:
                account = account_manager.accounts.get(account_id)
                if not account or not account.client:
                    return False
                
                # 判斷 target_account_id 是整數（用戶 ID）還是字符串（用戶名）
                try:
                    user_id = int(target_account_id)
                    # 是整數，直接使用作為用戶 ID
                    target_chat_id = user_id
                except (ValueError, TypeError):
                    # 不是整數，可能是用戶名，需要先獲取用戶信息
                    try:
                        user = await account.client.get_chat(target_account_id)
                        target_chat_id = user.id
                    except Exception as e:
                        self.logger.error(f"無法獲取用戶 {target_account_id} 的信息: {e}")
                        return False
                
                # 獲取源消息的 chat_id 和 message_id
                source_chat_id = context.group_id or (context.message.chat.id if context.message and context.message.chat else None)
                if not source_chat_id:
                    self.logger.error("無法確定源消息的群組 ID")
                    return False
                
                # 轉發消息到私聊
                await account.client.forward_messages(
                    chat_id=target_chat_id,
                    from_chat_id=source_chat_id,
                    message_ids=message_id
                )
                self.logger.info(f"已轉發消息 {message_id} 到私聊用戶 {target_chat_id}")
                return True
            except Exception as e:
                self.logger.error(f"轉發消息到私聊失敗: {e}", exc_info=True)
                return False
        
        return False
    
    async def _delete_message(
        self,
        context: MessageContext,
        action_data: Dict[str, Any],
        account_manager
    ) -> bool:
        """刪除消息"""
        message_id = action_data.get("message_id") or (context.message.id if context.message else None)
        group_id = action_data.get("group_id") or context.group_id
        account_id = action_data.get("account_id") or context.account_id
        
        if not message_id or not group_id or not account_id:
            return False
        
        if not account_manager:
            return False
        
        try:
            account = account_manager.accounts.get(account_id)
            if not account or not account.client:
                return False
            
            await account.client.delete_messages(group_id, message_id)
            self.logger.info(f"已刪除消息 {message_id} (群組: {group_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"刪除消息失敗: {e}", exc_info=True)
            return False


class UnifiedMessageHandler:
    """統一消息處理中心 - 整合所有消息處理邏輯"""
    
    def __init__(
        self,
        redpacket_handler: Optional[RedpacketHandler] = None,
        dialogue_manager: Optional[DialogueManager] = None,
        account_manager=None,
        keyword_trigger_service=None,
        scheduled_message_service=None
    ):
        """
        初始化統一消息處理中心
        
        Args:
            redpacket_handler: RedpacketHandler 實例
            dialogue_manager: DialogueManager 實例
            account_manager: AccountManager 實例（用於 ActionExecutor）
            keyword_trigger_service: KeywordTriggerProcessor 實例（從 keyword_trigger_processor.py）
            scheduled_message_service: ScheduledMessageProcessor 實例（從 scheduled_message_processor.py）
        """
        self.logger = logging.getLogger(__name__)
        
        # 初始化各個處理器
        self.router = MessageRouter()
        self.redpacket_processor = RedpacketProcessor(redpacket_handler)
        self.keyword_trigger_processor = KeywordTriggerProcessor(keyword_trigger_service)
        self.scheduled_message_processor = ScheduledMessageProcessor()
        self.dialogue_processor = DialogueProcessor(dialogue_manager)
        self.action_executor = ActionExecutor(account_manager=account_manager)
        
        # 如果提供了 scheduled_message_service，使用它
        if scheduled_message_service:
            self.scheduled_message_processor = scheduled_message_service
        
        self.logger.info("UnifiedMessageHandler 初始化完成")
        
        # 性能優化：預初始化常用對象
        self._message_cache: Dict[str, datetime] = {}  # 消息去重緩存
        self._cache_ttl = 300  # 5 分鐘 TTL
    
    async def handle_message(
        self,
        account_id: str,
        message: Message,
        chat: Chat,
        account_config: AccountConfig,
        dialogue_context: Optional[DialogueContext] = None
    ) -> ProcessingResult:
        """
        統一處理消息入口（帶緩存和去重）
        
        Args:
            account_id: 賬號 ID
            message: Telegram 消息對象
            chat: 聊天對象
            account_config: 賬號配置
            dialogue_context: 對話上下文（可選）
            
        Returns:
            ProcessingResult
        """
        try:
            # 消息去重（避免重複處理）
            message_key = f"{account_id}:{chat.id}:{message.id}"
            if message_key in self._message_cache:
                cache_time = self._message_cache[message_key]
                elapsed = (datetime.now() - cache_time).total_seconds()
                if elapsed < 60:  # 1 分鐘內的重複消息跳過
                    self.logger.debug(f"跳過重複消息: {message_key}")
                    return ProcessingResult(
                        success=True,
                        action_taken=False,
                        skip_further_processing=True
                    )
            
            # 記錄消息處理時間
            self._message_cache[message_key] = datetime.now()
            
            # 清理過期緩存
            if len(self._message_cache) > 1000:
                current_time = datetime.now()
                expired_keys = [
                    key for key, time in self._message_cache.items()
                    if (current_time - time).total_seconds() > self._cache_ttl
                ]
                for key in expired_keys:
                    del self._message_cache[key]
            
            # 1. 路由和分類消息
            context = self.router.classify_message(message, chat, account_id)
            if not context:
                return ProcessingResult(
                    success=True,
                    action_taken=False,
                    skip_further_processing=True
                )
            
            # 設置上下文
            context.account_config = account_config
            context.dialogue_context = dialogue_context
            
            # 2. 檢查是否應該處理
            if not self.router.should_process(context, account_config):
                return ProcessingResult(
                    success=True,
                    action_taken=False,
                    skip_further_processing=True
                )
            
            # 記錄消息處理（頻率限制器）
            if self.router.rate_limiter:
                self.router.rate_limiter.record_message(
                    account_id=context.account_id,
                    group_id=context.group_id
                )
            
            # 3. 按優先級順序處理
            results: List[ProcessingResult] = []
            
            # 優先級 1: 紅包處理
            redpacket_result = await self.redpacket_processor.process_redpacket(context, account_config)
            if redpacket_result:
                results.append(redpacket_result)
                # 如果搶紅包成功，可以執行感謝消息等後續動作
                if redpacket_result.action_taken and redpacket_result.success:
                    # TODO: 可以觸發感謝消息等
                    pass
            
            # 優先級 2: 關鍵詞觸發
            keyword_result = await self.keyword_trigger_processor.process_keyword_trigger(context, account_config)
            if keyword_result and keyword_result.action_taken:
                results.append(keyword_result)
                # 執行關鍵詞觸發的動作
                if keyword_result.result_data and keyword_result.result_data.get("actions"):
                    for action in keyword_result.result_data["actions"]:
                        action_type = action.get("type", "send_message")
                        action_params = action.get("params", {})
                        
                        # 構建動作數據
                        action_data = {
                            **action_params,
                            "account_id": context.account_id,
                            "group_id": context.group_id,
                        }
                        
                        # 添加延遲
                        if action.get("delay_min") or action.get("delay_max"):
                            action_data["delay"] = [
                                action.get("delay_min", 0),
                                action.get("delay_max", 0)
                            ]
                        
                        await self.action_executor.execute_action(
                            action_type,
                            context,
                            action_data,
                            self.action_executor.account_manager
                        )
            
            # 優先級 3: 定時消息（通常不在此處處理，由定時任務調度器處理）
            # scheduled_result = await self.scheduled_message_processor.process_scheduled_message(context, account_config)
            
            # 優先級 4: 對話處理（如果前面的處理沒有跳過）
            if not any(r.skip_further_processing for r in results):
                dialogue_result = await self.dialogue_processor.process_dialogue(context, account_config)
                if dialogue_result and dialogue_result.action_taken:
                    results.append(dialogue_result)
                    # 執行對話回復動作
                    if dialogue_result.result_data:
                        await self.action_executor.execute_action(
                            "send_message",
                            context,
                            dialogue_result.result_data
                        )
            
            # 4. 返回最終結果
            if results:
                # 返回最後一個結果（或合併所有結果）
                final_result = results[-1]
                return final_result
            else:
                return ProcessingResult(
                    success=True,
                    action_taken=False,
                    skip_further_processing=False
                )
                
        except Exception as e:
            self.logger.error(f"處理消息失敗: {e}", exc_info=True)
            return ProcessingResult(
                success=False,
                action_taken=False,
                error=str(e),
                skip_further_processing=True
            )
    
    def set_blacklist(self, users: List[int] = None, groups: List[int] = None):
        """設置黑名單"""
        if users:
            self.router.blacklist_users.update(users)
        if groups:
            self.router.blacklist_groups.update(groups)
    
    def remove_blacklist(self, users: List[int] = None, groups: List[int] = None):
        """移除黑名單"""
        if users:
            self.router.blacklist_users.difference_update(users)
        if groups:
            self.router.blacklist_groups.difference_update(groups)
