"""
對話管理器 - 處理群組消息，生成智能回復
"""
import logging
import asyncio
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import deque, OrderedDict

from pyrogram.types import Message

from group_ai_service.script_engine import ScriptEngine
from group_ai_service.models.account import AccountConfig
from group_ai_service.redpacket_handler import RedpacketHandler
from group_ai_service.monitor_service import MonitorService

logger = logging.getLogger(__name__)


class LRUCache:
    """LRU 緩存實現"""
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}
    
    def get(self, key: str):
        """獲取緩存"""
        if key not in self.cache:
            return None
        
        # 檢查過期
        if time.time() - self.timestamps[key] > self.ttl:
            self.delete(key)
            return None
        
        # 移動到末尾（最近使用）
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def set(self, key: str, value: Any):
        """設置緩存"""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                # 刪除最舊的
                oldest_key = next(iter(self.cache))
                self.delete(oldest_key)
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def delete(self, key: str):
        """刪除緩存"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    def clear(self):
        """清空緩存"""
        self.cache.clear()
        self.timestamps.clear()


class DialogueContext:
    """對話上下文"""
    
    def __init__(self, account_id: str, group_id: int):
        self.account_id = account_id
        self.group_id = group_id
        self.history: deque = deque(maxlen=30)  # 最近 30 條消息（優化：從50減少到30）
        self.last_reply_time: Optional[datetime] = None
        self.reply_count_today: int = 0
        self.last_reset_date: datetime = datetime.now().date()
        self.current_topic: Optional[str] = None
        self.mentioned_users: set = set()
        self.last_activity: float = time.time()  # 最後活動時間（用於清理）
    
    def add_message(self, message: Message, reply: Optional[str] = None):
        """添加消息到歷史"""
        self.last_activity = time.time()  # 更新活動時間
        
        self.history.append({
            "role": "user",
            "content": message.text or "",
            "timestamp": datetime.now(),
            "message_id": message.id,
            "user_id": message.from_user.id if message.from_user else None
        })
        
        if reply:
            self.history.append({
                "role": "assistant",
                "content": reply,
                "timestamp": datetime.now()
            })
    
    def get_recent_history(self, max_messages: int = 10) -> List[Dict[str, Any]]:
        """獲取最近的歷史消息"""
        return list(self.history)[-max_messages:]
    
    def reset_daily_count(self):
        """重置每日計數"""
        today = datetime.now().date()
        if today > self.last_reset_date:
            self.reply_count_today = 0
            self.last_reset_date = today


class DialogueManager:
    """對話管理器"""
    
    def __init__(self, max_contexts: int = 200, context_ttl: int = 3600, redpacket_handler=None):
        """
        初始化對話管理器
        
        Args:
            max_contexts: 最大上下文數量
            context_ttl: 上下文 TTL（秒）
            redpacket_handler: 紅包處理器（可選，如果提供則使用，否則創建新的）
        """
        self.contexts: Dict[str, DialogueContext] = {}  # key: f"{account_id}:{group_id}"
        self.context_cache = LRUCache(max_size=max_contexts, ttl=context_ttl)  # LRU 緩存
        self.script_engines: Dict[str, ScriptEngine] = {}  # key: account_id
        self.max_contexts = max_contexts
        self.context_ttl = context_ttl
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # 初始化服務（使用 try-except 避免初始化失敗）
        try:
            if redpacket_handler:
                self.redpacket_handler = redpacket_handler
                logger.info("使用提供的 RedpacketHandler")
            else:
                self.redpacket_handler = RedpacketHandler()
                logger.info("創建新的 RedpacketHandler")
            self.monitor_service = MonitorService()
        except Exception as e:
            logger.warning(f"初始化 DialogueManager 服務時出現警告: {e}，將使用默認值")
            # 如果初始化失敗，設置為 None，稍後再初始化
            self.redpacket_handler = None
            self.monitor_service = None
        
        logger.info("DialogueManager 初始化完成（帶 LRU 緩存）")
        
        # 不立即啟動清理任務，延遲到第一次使用時
        # self._start_cleanup_task()
    
    def initialize_account(
        self,
        account_id: str,
        script_engine: ScriptEngine,
        group_ids: List[int]
    ):
        """初始化賬號的對話管理器"""
        self.script_engines[account_id] = script_engine
        
        # 為每個群組創建上下文
        for group_id in group_ids:
            context_key = f"{account_id}:{group_id}"
            self.contexts[context_key] = DialogueContext(account_id, group_id)
        
        logger.info(f"賬號 {account_id} 對話管理器已初始化（{len(group_ids)} 個群組）")
    
    async def process_message(
        self,
        account_id: str,
        group_id: int,
        message: Message,
        account_config: AccountConfig
    ) -> Optional[str]:
        """處理消息，返回回復"""
        # 確保清理任務已啟動（延遲啟動）
        if self._cleanup_task is None:
            self._ensure_cleanup_task()
        
        # 使用帶緩存的 get_context 方法
        context = self.get_context(account_id, group_id)
        context_key = f"{account_id}:{group_id}"
        
        # 如果是新創建的上下文，記錄日誌
        if context_key not in self.contexts:
            logger.info(f"為群組 {group_id} 創建新上下文")
        
        # 重置每日計數（如果需要）
        context.reset_daily_count()
        
        # 檢查是否應該回復
        if not self._should_reply(message, context, account_config):
            logger.debug(f"跳過回復（賬號: {account_id}, 群組: {group_id}）")
            return None
        
        # 獲取劇本引擎
        script_engine = self.script_engines.get(account_id)
        if not script_engine:
            logger.warning(f"賬號 {account_id} 沒有初始化劇本引擎")
            return None
        
        # 檢查紅包（異步）
        is_redpacket = await self._check_redpacket(message)
        
        # 如果檢測到紅包，處理紅包邏輯
        if is_redpacket and account_config.redpacket_enabled:
            redpacket = await self.redpacket_handler.detect_redpacket(message)
            if redpacket:
                should_participate = await self.redpacket_handler.should_participate(
                    account_id=account_id,
                    redpacket=redpacket,
                    account_config=account_config,
                    context=context
                )
                
                if should_participate:
                    # 獲取賬號的 client（從 AccountManager 獲取）
                    try:
                        from group_ai_service.account_manager import AccountManager
                        account_manager = AccountManager()
                        if account_id in account_manager.accounts:
                            account = account_manager.accounts[account_id]
                            client = account.client if hasattr(account, 'client') else None
                            
                            if client:
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
                                
                                result = await self.redpacket_handler.participate(
                                    account_id=account_id,
                                    redpacket=redpacket,
                                    client=client,
                                    sender_name=sender_name,
                                    participant_name=participant_name
                                )
                                
                                # 記錄紅包事件
                                self.monitor_service.record_redpacket(
                                    account_id=account_id,
                                    success=result.success,
                                    amount=result.amount or 0
                                )
                                
                                logger.info(
                                    f"紅包參與完成（賬號: {account_id}, 紅包: {redpacket.redpacket_id}, "
                                    f"成功: {result.success}, 金額: {result.amount}）"
                                )
                            else:
                                logger.warning(f"賬號 {account_id} 的 client 不可用，無法參與紅包")
                        else:
                            logger.warning(f"賬號 {account_id} 不存在，無法參與紅包")
                    except Exception as e:
                        logger.error(f"參與紅包時發生錯誤: {e}", exc_info=True)
        
        # 構建上下文信息
        context_info = {
            "history": context.get_recent_history(account_config.max_replies_per_hour // 5),
            "group_id": group_id,
            "account_id": account_id,
            "is_new_member": self._check_new_member(message, context),
            "is_redpacket": is_redpacket,
        }
        
        # 處理消息（使用劇本引擎）
        try:
            reply = await script_engine.process_message(
                account_id=account_id,
                message=message,
                context=context_info
            )
            
            if reply:
                # 更新上下文
                context.add_message(message, reply)
                context.last_reply_time = datetime.now()
                context.reply_count_today += 1
                
                # 記錄監控指標
                self.monitor_service.record_reply(
                    account_id=account_id,
                    reply_time=0.0,  # TODO: 計算實際回復時間
                    success=True
                )
                self.monitor_service.record_message(
                    account_id=account_id,
                    message_type="reply",
                    success=True
                )
                
                logger.info(f"生成回復（賬號: {account_id}, 群組: {group_id}）: {reply[:50]}...")
                return reply
            else:
                logger.debug(f"劇本引擎未生成回復")
                return None
        
        except Exception as e:
            logger.error(f"處理消息失敗: {e}", exc_info=True)
            # 記錄錯誤
            self.monitor_service.record_message(
                account_id=account_id,
                message_type="error",
                success=False
            )
            return None
    
    def _should_reply(
        self,
        message: Message,
        context: DialogueContext,
        config: AccountConfig
    ) -> bool:
        """判斷是否應該回復"""
        # 檢查賬號是否激活
        if not config.active:
            return False
        
        # 檢查回復頻率
        if context.reply_count_today >= config.max_replies_per_hour:
            logger.debug(f"達到每日回復上限: {context.reply_count_today}/{config.max_replies_per_hour}")
            return False
        
        # 檢查最小回復間隔
        if context.last_reply_time:
            elapsed = (datetime.now() - context.last_reply_time).total_seconds()
            if elapsed < config.min_reply_interval:
                logger.debug(f"回復間隔太短: {elapsed:.1f}s < {config.min_reply_interval}s")
                return False
        
        # 檢查回復概率
        import random
        if random.random() > config.reply_rate:
            logger.debug(f"隨機跳過回復（回復率: {config.reply_rate}）")
            return False
        
        # 檢查消息是否為空
        if not message.text or len(message.text.strip()) == 0:
            return False
        
        return True
    
    def _check_new_member(self, message: Message, context: DialogueContext) -> bool:
        """檢查是否為新成員加入消息"""
        # 方法1: 檢查消息的 new_chat_members 屬性（Pyrogram 標準方式）
        if hasattr(message, 'new_chat_members') and message.new_chat_members:
            return True
        
        # 方法2: 檢查消息的 service 類型（某些情況下新成員加入是服務消息）
        if hasattr(message, 'service') and message.service:
            # 檢查是否為成員加入相關的服務消息
            service_type = getattr(message.service, 'type', None)
            if service_type in ['new_members', 'new_chat_members']:
                return True
        
        # 方法3: 檢查消息文本是否包含新成員相關關鍵詞（備用檢測）
        if message.text:
            text_lower = message.text.lower()
            new_member_keywords = [
                "joined", "加入", "歡迎", "welcome", "新人", "new member",
                "new user", "新成員", "新用戶"
            ]
            if any(keyword in text_lower for keyword in new_member_keywords):
                # 進一步檢查：確認是系統消息而非普通聊天
                if hasattr(message, 'from_user') and message.from_user:
                    # 如果是系統用戶（id為0或None），更可能是新成員消息
                    if message.from_user.id == 0 or message.from_user.id is None:
                        return True
                    # 或者檢查是否為群組管理員發送的歡迎消息
                    if hasattr(message.chat, 'members_count'):
                        return True
        
        return False
    
    async def _check_redpacket(self, message: Message) -> bool:
        """檢查是否為紅包消息"""
        # 使用 RedpacketHandler 檢測
        redpacket = await self.redpacket_handler.detect_redpacket(message)
        return redpacket is not None
    
    def _start_cleanup_task(self):
        """啟動定期清理任務（延遲啟動，避免初始化時的事件循環問題）"""
        # 不在初始化時啟動，而是在第一次使用時啟動
        # 這樣可以避免在沒有事件循環的環境中出錯
        pass
    
    def _ensure_cleanup_task(self):
        """確保清理任務已啟動"""
        if self._cleanup_task is not None and not self._cleanup_task.done():
            return
        
        async def periodic_cleanup():
            """定期清理非活動上下文"""
            while True:
                try:
                    await asyncio.sleep(3600)  # 每小時清理一次
                    self.cleanup_inactive_contexts()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"清理任務異常: {e}")
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._cleanup_task = asyncio.create_task(periodic_cleanup())
                logger.debug("清理任務已啟動")
        except RuntimeError:
            # 沒有事件循環，稍後再試
            logger.debug("無法啟動清理任務：沒有事件循環")
        except Exception as e:
            logger.warning(f"啟動清理任務失敗: {e}")
    
    def cleanup_inactive_contexts(self):
        """清理非活動上下文"""
        current_time = time.time()
        inactive_threshold = 86400  # 24 小時
        
        keys_to_remove = []
        for key, context in self.contexts.items():
            if current_time - context.last_activity > inactive_threshold:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self.contexts.pop(key, None)
            self.context_cache.delete(key)
        
        if keys_to_remove:
            logger.info(f"清理了 {len(keys_to_remove)} 個非活動上下文")
        
        # 如果上下文數量超過限制，清理最舊的
        if len(self.contexts) > self.max_contexts:
            # 按最後活動時間排序
            sorted_contexts = sorted(
                self.contexts.items(),
                key=lambda x: x[1].last_activity
            )
            # 刪除最舊的 20%
            remove_count = int(self.max_contexts * 0.2)
            for key, _ in sorted_contexts[:remove_count]:
                self.contexts.pop(key, None)
                self.context_cache.delete(key)
            logger.info(f"清理了 {remove_count} 個最舊的上下文（超過限制）")
    
    def get_context(self, account_id: str, group_id: int) -> DialogueContext:
        """獲取上下文（帶緩存）"""
        context_key = f"{account_id}:{group_id}"
        
        # 嘗試從緩存獲取
        cached_context = self.context_cache.get(context_key)
        if cached_context:
            cached_context.last_activity = time.time()
            return cached_context
        
        # 從內存獲取或創建
        context = self.contexts.get(context_key)
        if not context:
            context = DialogueContext(account_id, group_id)
            self.contexts[context_key] = context
        
        # 更新活動時間
        context.last_activity = time.time()
        
        # 更新緩存
        self.context_cache.set(context_key, context)
        return context
    
    def remove_account(self, account_id: str):
        """移除賬號的所有上下文"""
        keys_to_remove = [
            key for key in self.contexts.keys()
            if key.startswith(f"{account_id}:")
        ]
        for key in keys_to_remove:
            self.contexts.pop(key, None)
            self.context_cache.delete(key)  # 同時清除緩存
        
        if account_id in self.script_engines:
            del self.script_engines[account_id]
        
        logger.info(f"賬號 {account_id} 的對話上下文已移除（{len(keys_to_remove)} 個上下文）")

