"""
紅包處理器 - 檢測和處理 Telegram 群組紅包
"""
import logging
import random
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime, timedelta
from dataclasses import dataclass

from pyrogram.types import Message

from group_ai_service.models.account import AccountConfig

if TYPE_CHECKING:
    from group_ai_service.dialogue_manager import DialogueContext

logger = logging.getLogger(__name__)


@dataclass
class RedpacketInfo:
    """紅包信息"""
    redpacket_id: str
    group_id: int
    sender_id: int
    amount: Optional[float] = None
    count: Optional[int] = None
    message_id: int = 0
    timestamp: datetime = None
    redpacket_type: str = "unknown"  # normal, random, etc.
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RedpacketResult:
    """紅包參與結果"""
    redpacket_id: str
    account_id: str
    success: bool
    amount: Optional[float] = None
    timestamp: datetime = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class RedpacketStrategy:
    """紅包參與策略基類"""
    
    def evaluate(
        self,
        redpacket: RedpacketInfo,
        account_config: AccountConfig,
        context: "DialogueContext"
    ) -> float:
        """評估參與概率 (0-1)"""
        raise NotImplementedError


class RandomStrategy(RedpacketStrategy):
    """隨機策略"""
    
    def __init__(self, base_probability: float = 0.5):
        self.base_probability = base_probability
    
    def evaluate(
        self,
        redpacket: RedpacketInfo,
        account_config: AccountConfig,
        context: "DialogueContext"
    ) -> float:
        """返回基礎概率"""
        return self.base_probability


class TimeBasedStrategy(RedpacketStrategy):
    """基於時間的策略"""
    
    def __init__(
        self,
        peak_hours: List[int] = None,
        peak_probability: float = 0.8,
        off_peak_probability: float = 0.3
    ):
        self.peak_hours = peak_hours or [18, 19, 20, 21]
        self.peak_probability = peak_probability
        self.off_peak_probability = off_peak_probability
    
    def evaluate(
        self,
        redpacket: RedpacketInfo,
        account_config: AccountConfig,
        context: "DialogueContext"
    ) -> float:
        """根據時間返回概率"""
        current_hour = datetime.now().hour
        if current_hour in self.peak_hours:
            return self.peak_probability
        return self.off_peak_probability


class FrequencyStrategy(RedpacketStrategy):
    """基於頻率的策略"""
    
    def __init__(
        self,
        max_per_hour: int = 5,
        cooldown_seconds: int = 300
    ):
        self.max_per_hour = max_per_hour
        self.cooldown_seconds = cooldown_seconds
    
    def evaluate(
        self,
        redpacket: RedpacketInfo,
        account_config: AccountConfig,
        context: "DialogueContext",
        handler: Optional["RedpacketHandler"] = None
    ) -> float:
        """根據頻率返回概率"""
        # 檢查冷卻時間
        if context.last_reply_time:
            elapsed = (datetime.now() - context.last_reply_time).total_seconds()
            if elapsed < self.cooldown_seconds:
                return 0.0
        
        # 檢查每小時上限（精確實現）
        if handler:
            # 獲取當前賬號ID（從context中獲取）
            account_id = context.account_id if hasattr(context, 'account_id') else None
            if account_id:
                # 獲取當前小時的參與次數
                current_hour_count = handler.get_hourly_participation_count(
                    account_id=account_id,
                    max_per_hour=self.max_per_hour
                )
                
                # 如果已達到每小時上限，返回0
                if current_hour_count >= self.max_per_hour:
                    logger.debug(
                        f"賬號 {account_id} 已達到每小時參與上限 "
                        f"({current_hour_count}/{self.max_per_hour})"
                    )
                    return 0.0
                
                # 根據剩餘配額計算概率（剩餘配額越多，概率越高）
                remaining_quota = self.max_per_hour - current_hour_count
                base_probability = 0.7
                # 如果剩餘配額少於2次，降低概率
                if remaining_quota <= 1:
                    return 0.3
                elif remaining_quota <= 2:
                    return 0.5
                else:
                    return base_probability
        
        # 如果沒有handler，使用默認概率
        return 0.7


class AmountBasedStrategy(RedpacketStrategy):
    """基於金額的策略"""
    
    def __init__(
        self,
        min_amount: float = 0.01,
        max_amount: float = 100.0,
        high_amount_probability: float = 0.9,
        low_amount_probability: float = 0.3
    ):
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.high_amount_probability = high_amount_probability
        self.low_amount_probability = low_amount_probability
    
    def evaluate(
        self,
        redpacket: RedpacketInfo,
        account_config: AccountConfig,
        context: "DialogueContext"
    ) -> float:
        """根據金額返回概率"""
        if not redpacket.amount:
            return 0.5  # 未知金額，使用默認概率
        
        # 金額越高，參與概率越高
        if redpacket.amount >= self.max_amount * 0.5:
            return self.high_amount_probability
        elif redpacket.amount >= self.min_amount:
            return self.low_amount_probability
        else:
            return 0.1  # 金額太低，低概率參與


class CompositeStrategy(RedpacketStrategy):
    """組合策略（多個策略的加權平均）"""
    
    def __init__(self, strategies: List[tuple[RedpacketStrategy, float]] = None):
        """
        Args:
            strategies: [(strategy, weight), ...]
        """
        self.strategies = strategies or []
    
    def evaluate(
        self,
        redpacket: RedpacketInfo,
        account_config: AccountConfig,
        context: "DialogueContext"
    ) -> float:
        """返回加權平均概率"""
        if not self.strategies:
            return 0.5  # 默認概率
        
        total_weight = sum(weight for _, weight in self.strategies)
        if total_weight == 0:
            return 0.5
        
        weighted_sum = sum(
            strategy.evaluate(redpacket, account_config, context) * weight
            for strategy, weight in self.strategies
        )
        
        return weighted_sum / total_weight


class RedpacketHandler:
    """紅包處理器"""
    
    def __init__(self, game_api_client=None):
        """
        初始化紅包處理器
        
        Args:
            game_api_client: 遊戲系統 API 客戶端（可選）
        """
        self.strategies: Dict[str, RedpacketStrategy] = {}
        self.participation_log: List[RedpacketResult] = []
        self.detected_redpackets: Dict[str, RedpacketInfo] = {}  # 去重用
        self._default_strategy: Optional[RedpacketStrategy] = None
        self._game_api_client = game_api_client  # 遊戲系統 API 客戶端
        
        # 重複點擊檢測：記錄每個賬號對每個紅包的點擊次數和最佳手氣提示狀態
        self._click_tracking: Dict[str, Dict[str, Any]] = {}  # key: f"{account_id}:{redpacket_id}"
        self._best_luck_announced: Dict[str, bool] = {}  # key: f"{account_id}:{redpacket_id}"，記錄是否已提示最佳手氣
        
        # 搶紅包通知：記錄每個紅包的搶包情況，用於通知發包人
        self._redpacket_notifications: Dict[str, Dict[str, Any]] = {}  # key: redpacket_id
        
        # 每小時參與計數：記錄每個賬號在每個小時的參與次數
        # key: f"{account_id}:{hour_key}"，value: 參與次數
        # hour_key 格式: "YYYY-MM-DD-HH" (例如: "2025-01-15-14")
        self._hourly_participation: Dict[str, int] = {}
        
        # 定期清理舊數據（避免內存泄漏）
        self._cleanup_interval = 3600  # 1小時清理一次
        self._last_cleanup = datetime.now()
        
        logger.info("RedpacketHandler 初始化完成")
    
    def set_game_api_client(self, game_api_client):
        """設置遊戲系統 API 客戶端"""
        self._game_api_client = game_api_client
        logger.info("已設置遊戲系統 API 客戶端")
    
    def set_default_strategy(self, strategy: RedpacketStrategy):
        """設置默認策略"""
        self._default_strategy = strategy
        logger.info(f"設置默認紅包策略: {strategy.__class__.__name__}")
    
    def register_strategy(self, name: str, strategy: RedpacketStrategy):
        """註冊策略"""
        self.strategies[name] = strategy
        logger.info(f"註冊紅包策略: {name}")
    
    async def detect_redpacket(self, message: Message) -> Optional[RedpacketInfo]:
        """
        檢測紅包消息
        
        檢測方法：
        1. 通過 Telegram API 檢查消息類型（按鈕、遊戲等）
        2. 通過遊戲系統 API 查詢群組狀態，獲取活躍紅包
        3. 不再使用關鍵詞檢測
        """
        group_id = message.chat.id if message.chat else 0
        if not group_id:
            return None
        
        # 方法 1: 檢查 Telegram 消息類型
        # 檢查是否為按鈕消息（紅包通常使用 Inline Keyboard）
        if hasattr(message, 'reply_markup') and message.reply_markup:
            # 檢查按鈕回調數據是否包含紅包相關信息
            if hasattr(message.reply_markup, 'inline_keyboard'):
                for row in message.reply_markup.inline_keyboard:
                    for button in row:
                        callback_data = getattr(button, 'callback_data', '') or ''
                        if any(keyword in callback_data.lower() for keyword in ['redpacket', 'red_packet', 'grab', 'claim']):
                            # 可能是紅包按鈕，需要進一步驗證
                            logger.debug(f"檢測到可能的紅包按鈕消息: {message.id}")
                            # 繼續檢查遊戲系統 API
        
        # 方法 2: 檢查消息是否為遊戲類型
        if hasattr(message, 'game') and message.game:
            # Telegram 遊戲消息，可能是紅包遊戲
            logger.debug(f"檢測到遊戲消息: {message.id}")
            # 繼續檢查遊戲系統 API
        
        # 方法 3: 通過 Telegram 消息按鈕檢測（主要方法）
        # 檢查消息是否包含紅包按鈕（callback_data 格式：hb:grab:{envelope_id}）
        if hasattr(message, 'reply_markup') and message.reply_markup:
            if hasattr(message.reply_markup, 'inline_keyboard'):
                for row in message.reply_markup.inline_keyboard:
                    for button in row:
                        callback_data = getattr(button, 'callback_data', '') or ''
                        # 檢查是否為紅包按鈕：hb:grab:{envelope_id}
                        import re
                        match = re.match(r'^hb:grab:(\d+)$', callback_data)
                        if match:
                            envelope_id = match.group(1)
                            redpacket_id = f"{group_id}_{envelope_id}"
                            
                            # 檢查是否已處理過
                            if redpacket_id in self.detected_redpackets:
                                existing = self.detected_redpackets[redpacket_id]
                                time_diff = (datetime.now() - existing.timestamp).total_seconds()
                                if time_diff < 300:  # 5分鐘內
                                    continue
                            
                            # 通過遊戲系統 API 獲取紅包詳情
                            amount = None
                            count = None
                            if hasattr(self, '_game_api_client') and self._game_api_client:
                                try:
                                    game_status = await self._game_api_client.get_game_status(group_id)
                                    for rp_info in game_status.active_redpackets:
                                        if rp_info.redpacket_id == envelope_id:
                                            amount = rp_info.amount
                                            count = rp_info.count
                                            break
                                except Exception as e:
                                    logger.warning(f"查詢紅包詳情失敗: {e}")
                            
                            # 創建紅包信息
                            redpacket = RedpacketInfo(
                                redpacket_id=redpacket_id,
                                group_id=group_id,
                                sender_id=message.from_user.id if message.from_user else 0,
                                message_id=message.id,
                                amount=amount,
                                count=count,
                                timestamp=message.date or datetime.now(),
                                redpacket_type="normal",
                                metadata={
                                    "envelope_id": envelope_id,
                                    "callback_data": callback_data,
                                    "detected_from": "telegram_button"
                                }
                            )
                            
                            # 記錄檢測到的紅包
                            self.detected_redpackets[redpacket.redpacket_id] = redpacket
                            
                            logger.info(
                                f"通過 Telegram 按鈕檢測到紅包: {redpacket.redpacket_id} "
                                f"(群組: {redpacket.group_id}, envelope_id: {envelope_id})"
                            )
                            return redpacket
        
        # 方法 4: 通過遊戲系統 API 查詢（備用方法）
        # 如果配置了遊戲系統 API，查詢活躍紅包列表
        if hasattr(self, '_game_api_client') and self._game_api_client:
            try:
                game_status = await self._game_api_client.get_game_status(group_id)
                
                # 檢查是否有活躍的紅包
                for redpacket_info in game_status.active_redpackets:
                    # 檢查紅包是否與當前消息相關
                    # 可以通過 message_id、時間戳等匹配
                    if redpacket_info.group_id == group_id:
                        # 檢查是否已處理過
                        if redpacket_info.redpacket_id in self.detected_redpackets:
                            existing = self.detected_redpackets[redpacket_info.redpacket_id]
                            time_diff = (datetime.now() - existing.timestamp).total_seconds()
                            if time_diff < 300:  # 5分鐘內
                                continue
                        
                        # 轉換為 RedpacketInfo
                        redpacket = RedpacketInfo(
                            redpacket_id=redpacket_info.redpacket_id,
                            group_id=redpacket_info.group_id,
                            sender_id=message.from_user.id if message.from_user else 0,
                            message_id=message.id,
                            amount=redpacket_info.amount,
                            count=redpacket_info.count,
                            timestamp=message.date or datetime.now(),
                            redpacket_type=redpacket_info.game_type,
                            metadata={
                                "game_id": redpacket_info.game_id,
                                "claimed_count": redpacket_info.claimed_count,
                                "remaining_count": redpacket_info.remaining_count,
                                "expires_at": redpacket_info.expires_at.isoformat() if redpacket_info.expires_at else None,
                                "detected_from": "game_api"
                            }
                        )
                        
                        # 記錄檢測到的紅包
                        self.detected_redpackets[redpacket.redpacket_id] = redpacket
                        
                        logger.info(
                            f"通過遊戲系統 API 檢測到紅包: {redpacket.redpacket_id} "
                            f"(群組: {redpacket.group_id}, 金額: {redpacket.amount})"
                        )
                        return redpacket
                        
            except Exception as e:
                logger.warning(f"查詢遊戲系統 API 失敗: {e}，將嘗試 Telegram API 檢測")
        
        return None
    
    async def should_participate(
        self,
        account_id: str,
        redpacket: RedpacketInfo,
        account_config: AccountConfig,
        context: "DialogueContext"
    ) -> bool:
        """決定是否參與紅包"""
        # 檢查賬號是否啟用紅包功能
        if not account_config.redpacket_enabled:
            logger.debug(f"賬號 {account_id} 未啟用紅包功能")
            return False
        
        # 使用策略評估參與概率
        strategy = self._default_strategy
        if not strategy:
            # 使用默認策略
            strategy = RandomStrategy(base_probability=account_config.redpacket_probability)
        
        # 將handler傳遞給策略（用於FrequencyStrategy的每小時計數）
        if hasattr(strategy, 'evaluate'):
            # 檢查策略是否需要handler參數
            import inspect
            sig = inspect.signature(strategy.evaluate)
            if 'handler' in sig.parameters:
                probability = strategy.evaluate(redpacket, account_config, context, handler=self)
            else:
                probability = strategy.evaluate(redpacket, account_config, context)
        else:
            probability = 0.0
        
        # 隨機決定
        should_participate = random.random() < probability
        
        logger.debug(
            f"紅包參與評估 (賬號: {account_id}, 概率: {probability:.2f}, 決定: {should_participate})"
        )
        
        return should_participate
    
    async def participate(
        self,
        account_id: str,
        redpacket: RedpacketInfo,
        client,
        sender_name: Optional[str] = None,
        participant_name: Optional[str] = None
    ) -> RedpacketResult:
        """
        參與紅包（執行搶紅包操作）
        
        執行方法：
        1. 優先通過遊戲系統 API 參與
        2. 如果 API 不可用，通過 Telegram API 點擊按鈕或發送命令
        3. 記錄參與結果並上報
        
        Args:
            account_id: 賬號 ID
            redpacket: 紅包信息
            client: Telegram Client
            sender_name: 發包人姓名（可選，用於最佳手氣提示）
            participant_name: 參與者姓名（可選，用於搶包通知）
        """
        # 驗證金額（防止 amountTo 太小）
        try:
            from group_ai_service.config import get_group_ai_config
            config = get_group_ai_config()
            min_amount = config.redpacket_min_amount
        except Exception:
            min_amount = 0.01  # 默認值
        
        if redpacket.amount and redpacket.amount < min_amount:
            logger.warning(f"紅包金額太小: {redpacket.amount}，最小金額: {min_amount}")
            return RedpacketResult(
                redpacket_id=redpacket.redpacket_id,
                account_id=account_id,
                success=False,
                error=f"紅包金額太小，最小金額為 {min_amount}"
            )
        
        # 檢查重複點擊
        click_key = f"{account_id}:{redpacket.redpacket_id}"
        if click_key in self._click_tracking:
            click_info = self._click_tracking[click_key]
            click_count = click_info.get("count", 0)
            
            # 如果已經點擊過，檢查是否已提示最佳手氣
            best_luck_key = f"{account_id}:{redpacket.redpacket_id}"
            if best_luck_key in self._best_luck_announced and self._best_luck_announced[best_luck_key]:
                # 已經提示過最佳手氣，後續點擊顯示警示
                logger.warning(f"賬號 {account_id} 重複點擊紅包 {redpacket.redpacket_id}，已提示過最佳手氣")
                return RedpacketResult(
                    redpacket_id=redpacket.redpacket_id,
                    account_id=account_id,
                    success=False,
                    error="重複點擊：您已經搶過此紅包，請勿重複操作"
                )
            
            # 更新點擊次數
            click_info["count"] = click_count + 1
        else:
            # 首次點擊
            self._click_tracking[click_key] = {
                "count": 1,
                "first_click_time": datetime.now()
            }
        
        try:
            # 方法 1: 通過遊戲系統 API 參與（優先）
            if self._game_api_client:
                try:
                    api_result = await self._game_api_client.participate_redpacket(
                        account_id=account_id,
                        redpacket_id=redpacket.redpacket_id,
                        group_id=redpacket.group_id
                    )
                    
                    # 解析 API 返回結果
                    success = api_result.get("success", False)
                    amount = api_result.get("amount")
                    error = api_result.get("error")
                    
                    result = RedpacketResult(
                        redpacket_id=redpacket.redpacket_id,
                        account_id=account_id,
                        success=success,
                        amount=amount,
                        timestamp=datetime.now(),
                        error=error
                    )
                    
                    # 記錄結果
                    self.participation_log.append(result)
                    
                    # 只保留最近 1000 條記錄
                    if len(self.participation_log) > 1000:
                        self.participation_log = self.participation_log[-1000:]
                    
                    # 更新每小時參與計數
                    if result.success:
                        self._increment_hourly_participation(account_id)
                    
                    # 處理最佳手氣提示和搶包通知
                    if success and amount:
                        await self._handle_redpacket_result(
                            account_id=account_id,
                            redpacket=redpacket,
                            result=result,
                            client=client,
                            sender_name=sender_name,
                            participant_name=participant_name
                        )
                    
                    logger.info(
                        f"通過遊戲系統 API 參與紅包完成 (賬號: {account_id}, "
                        f"紅包: {redpacket.redpacket_id}, 成功: {success}, 金額: {amount})"
                    )
                    
                    return result
                    
                except Exception as api_error:
                    logger.warning(f"遊戲系統 API 參與失敗: {api_error}，嘗試 Telegram API")
            
            # 方法 2: 通過 Telegram API 點擊按鈕參與（主要方法）
            # 從 metadata 中獲取 envelope_id 和 callback_data
            envelope_id = redpacket.metadata.get("envelope_id")
            callback_data = redpacket.metadata.get("callback_data")
            
            if not callback_data and envelope_id:
                # 構造 callback_data
                callback_data = f"hb:grab:{envelope_id}"
            
            if callback_data and client:
                try:
                    # 使用 Pyrogram 發送 CallbackQuery
                    # 注意：Pyrogram 需要先獲取消息，然後發送 callback query
                    # 這裡我們需要找到包含該按鈕的消息
                    
                    # 方法：通過 message_id 獲取消息，然後發送 callback
                    try:
                        # 嘗試直接發送 callback query（如果 Pyrogram 支持）
                        # 注意：Pyrogram 的 Client 沒有直接的 request_callback_answer 方法
                        # 需要使用 aiogram 的 Bot 或者通過其他方式
                        
                        # 臨時方案：記錄需要的信息，讓外部處理
                        logger.info(
                            f"需要點擊按鈕參與紅包: callback_data={callback_data}, "
                            f"message_id={redpacket.message_id}, chat_id={redpacket.group_id}"
                        )
                        
                        # 如果配置了遊戲系統 API，通過 API 參與
                        if self._game_api_client:
                            api_result = await self._game_api_client.participate_redpacket(
                                account_id=account_id,
                                redpacket_id=envelope_id or redpacket.redpacket_id,
                                group_id=redpacket.group_id,
                                client=client
                            )
                            
                            if api_result.get("success"):
                                success = True
                                amount = api_result.get("amount")
                            else:
                                success = False
                                amount = None
                        else:
                            # 沒有 API 客戶端，標記為需要手動處理
                            success = False
                            amount = None
                            logger.warning("無法參與紅包：未配置遊戲系統 API 客戶端")
                            
                    except Exception as e:
                        logger.error(f"Telegram API 參與失敗: {e}")
                        success = False
                        amount = None
                except Exception as e:
                    logger.error(f"處理按鈕點擊失敗: {e}")
                    success = False
                    amount = None
            else:
                # 沒有 callback_data 或 client，嘗試其他方法
                if self._game_api_client:
                    try:
                        api_result = await self._game_api_client.participate_redpacket(
                            account_id=account_id,
                            redpacket_id=envelope_id or redpacket.redpacket_id,
                            group_id=redpacket.group_id,
                            client=client
                        )
                        success = api_result.get("success", False)
                        amount = api_result.get("amount")
                    except Exception as e:
                        logger.error(f"遊戲系統 API 參與失敗: {e}")
                        success = False
                        amount = None
                else:
                    success = False
                    amount = None
                    logger.warning("無法參與紅包：缺少必要信息")
            
            result = RedpacketResult(
                redpacket_id=redpacket.redpacket_id,
                account_id=account_id,
                success=success,
                amount=amount,
                timestamp=datetime.now(),
                error=None if success else "參與方法不可用"
            )
            
            # 記錄結果
            self.participation_log.append(result)
            
            # 只保留最近 1000 條記錄
            if len(self.participation_log) > 1000:
                self.participation_log = self.participation_log[-1000:]
            
            # 更新每小時參與計數
            if result.success:
                self._increment_hourly_participation(account_id)
            
            # 處理最佳手氣提示和搶包通知
            if success and amount:
                await self._handle_redpacket_result(
                    account_id=account_id,
                    redpacket=redpacket,
                    result=result,
                    client=client,
                    sender_name=sender_name,
                    participant_name=participant_name
                )
            
            # 上報結果到遊戲系統（如果可用）
            if self._game_api_client and success:
                try:
                    await self._game_api_client.report_participation_result(
                        account_id=account_id,
                        redpacket_id=redpacket.redpacket_id,
                        group_id=redpacket.group_id,
                        success=success,
                        amount=amount
                    )
                except Exception as e:
                    logger.warning(f"上報參與結果失敗: {e}")
            
            logger.info(
                f"紅包參與完成 (賬號: {account_id}, 紅包: {redpacket.redpacket_id}, "
                f"成功: {success}, 金額: {amount})"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"參與紅包失敗: {e}", exc_info=True)
            return RedpacketResult(
                redpacket_id=redpacket.redpacket_id,
                account_id=account_id,
                success=False,
                error=str(e)
            )
    
    def get_participation_stats(
        self,
        account_id: Optional[str] = None,
        time_range: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """獲取參與統計"""
        results = self.participation_log
        
        # 按賬號過濾
        if account_id:
            results = [r for r in results if r.account_id == account_id]
        
        # 按時間範圍過濾
        if time_range:
            cutoff = datetime.now() - time_range
            results = [r for r in results if r.timestamp >= cutoff]
        
        total = len(results)
        successful = sum(1 for r in results if r.success)
        total_amount = sum(r.amount or 0 for r in results if r.success)
        
        return {
            "total_participations": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "total_amount": total_amount,
            "average_amount": total_amount / successful if successful > 0 else 0.0
        }
    
    async def _handle_redpacket_result(
        self,
        account_id: str,
        redpacket: RedpacketInfo,
        result: RedpacketResult,
        client,
        sender_name: Optional[str] = None,
        participant_name: Optional[str] = None
    ):
        """
        處理紅包參與結果：
        1. 檢查是否為最佳手氣（金額最高）
        2. 如果是最佳手氣且未提示過，發送提示（包含發包人信息）
        3. 通知發包人誰搶了紅包和剩餘數量
        """
        try:
            # 獲取該紅包的所有參與記錄
            redpacket_participations = [
                r for r in self.participation_log
                if r.redpacket_id == redpacket.redpacket_id and r.success and r.amount
            ]
            
            # 找出最高金額（最佳手氣）
            if redpacket_participations:
                max_amount = max(r.amount for r in redpacket_participations)
                is_best_luck = result.amount == max_amount
                
                # 檢查是否已提示過最佳手氣
                best_luck_key = f"{account_id}:{redpacket.redpacket_id}"
                already_announced = self._best_luck_announced.get(best_luck_key, False)
                
                # 如果是最佳手氣且未提示過，發送提示
                if is_best_luck and not already_announced:
                    # 檢查是否啟用最佳手氣提示
                    try:
                        from group_ai_service.config import get_group_ai_config
                        config = get_group_ai_config()
                        announcement_enabled = config.redpacket_best_luck_announcement_enabled
                    except Exception:
                        announcement_enabled = True  # 默認啟用
                    
                    if announcement_enabled:
                        # 標記為已提示
                        self._best_luck_announced[best_luck_key] = True
                        
                        # 構建提示消息（包含發包人信息）
                        sender_info = f"來自 {sender_name} 的紅包" if sender_name else "這個紅包"
                        best_luck_message = f"🎉 恭喜！您搶到了 {sender_info} 的最佳手氣！金額：{result.amount:.2f}"
                        
                        try:
                            from pyrogram.errors import FloodWait
                            await client.send_message(
                                chat_id=redpacket.group_id,
                                text=best_luck_message
                            )
                            logger.info(f"已發送最佳手氣提示: {account_id}, 金額: {result.amount}")
                        except FloodWait as e:
                            logger.warning(f"發送最佳手氣提示觸發 FloodWait，等待 {e.value} 秒")
                            # 可以選擇等待後重試，或記錄到隊列稍後發送
                            # 這裡暫時跳過，避免阻塞
                        except Exception as e:
                            logger.error(f"發送最佳手氣提示失敗: {e}")
                    else:
                        # 即使不發送提示，也標記為已提示，避免重複檢測
                        self._best_luck_announced[best_luck_key] = True
            
            # 通知發包人（記錄搶包信息）
            if redpacket.redpacket_id not in self._redpacket_notifications:
                self._redpacket_notifications[redpacket.redpacket_id] = {
                    "sender_id": redpacket.sender_id,
                    "group_id": redpacket.group_id,
                    "total_count": redpacket.count or 0,
                    "participants": []
                }
            
            notification_info = self._redpacket_notifications[redpacket.redpacket_id]
            
            # 添加參與者信息
            participant_info = {
                "account_id": account_id,
                "amount": result.amount,
                "timestamp": result.timestamp
            }
            notification_info["participants"].append(participant_info)
            
            # 計算剩餘數量
            claimed_count = len(notification_info["participants"])
            remaining_count = max(0, notification_info["total_count"] - claimed_count)
            
            # 發送通知給發包人
            try:
                # 檢查是否啟用搶包通知
                try:
                    from group_ai_service.config import get_group_ai_config
                    config = get_group_ai_config()
                    notification_enabled = config.redpacket_notification_enabled
                except Exception:
                    notification_enabled = True  # 默認啟用
                
                if not notification_enabled:
                    logger.debug("搶包通知已禁用，跳過發送")
                    return
                
                # 獲取參與者信息
                if not participant_name:
                    # 嘗試從 client 獲取當前用戶信息
                    try:
                        if client and hasattr(client, 'get_me'):
                            me = await client.get_me()
                            if me:
                                participant_name = me.first_name or me.username or f"用戶 {account_id}"
                            else:
                                participant_name = f"用戶 {account_id}"
                        else:
                            participant_name = f"用戶 {account_id}"
                    except Exception as e:
                        logger.debug(f"獲取參與者名稱失敗: {e}")
                        participant_name = f"用戶 {account_id}"
                
                notification_message = (
                    f"📢 {participant_name} 搶到了您的紅包，金額：{result.amount:.2f}\n"
                    f"剩餘紅包數量：{remaining_count}"
                )
                
                # 發送通知給發包人
                # 方法1: 通過 AccountManager 查找發包人的賬號並發送通知
                try:
                    from group_ai_service.account_manager import AccountManager
                    account_manager = AccountManager()
                    
                    # 查找發包人的賬號（通過 sender_id）
                    sender_account = None
                    for acc_id, acc in account_manager.accounts.items():
                        try:
                            # 獲取當前登錄用戶的 ID
                            if acc.client and acc.client.is_connected:
                                me = await acc.client.get_me()
                                if me and me.id == redpacket.sender_id:
                                    sender_account = acc
                                    break
                        except Exception as e:
                            logger.debug(f"獲取賬號 {acc_id} 的用戶 ID 失敗: {e}")
                            continue
                    
                    # 如果找到發包人的賬號，發送通知
                    if sender_account and sender_account.client:
                        try:
                            from pyrogram.errors import FloodWait
                            await sender_account.client.send_message(
                                chat_id=redpacket.group_id,
                                text=notification_message
                            )
                            logger.info(f"已發送搶包通知給發包人: {redpacket.sender_id}")
                        except FloodWait as e:
                            logger.warning(f"發送通知觸發 FloodWait，等待 {e.value} 秒")
                            # 可以選擇等待後重試，或記錄到隊列稍後發送
                            # 這裡暫時跳過，避免阻塞
                        except Exception as e:
                            logger.warning(f"發送通知給發包人失敗: {e}，將嘗試通過遊戲系統 API")
                    
                    # 方法2: 如果找不到發包人賬號，通過遊戲系統 API 發送通知
                    if not sender_account and self._game_api_client:
                        try:
                            await self._game_api_client.report_participation_result(
                                account_id=str(redpacket.sender_id),
                                redpacket_id=redpacket.redpacket_id,
                                group_id=redpacket.group_id,
                                success=True,
                                amount=result.amount,
                                notification=notification_message
                            )
                            logger.info(f"已通過遊戲系統 API 發送搶包通知")
                        except Exception as e:
                            logger.warning(f"通過遊戲系統 API 發送通知失敗: {e}")
                    
                    # 如果都失敗，記錄日誌
                    if not sender_account and not self._game_api_client:
                        logger.info(f"搶包通知（無法發送）: {notification_message}")
                        
                except ImportError:
                    logger.warning("無法導入 AccountManager，跳過發送通知")
                except Exception as e:
                    logger.error(f"發送搶包通知失敗: {e}", exc_info=True)
                
            except Exception as e:
                logger.error(f"處理搶包通知失敗: {e}", exc_info=True)
                
        except Exception as e:
            logger.error(f"處理紅包結果失敗: {e}", exc_info=True)
        
        # 定期清理舊數據
        await self._cleanup_old_data()
    
    async def _cleanup_old_data(self):
        """清理舊的跟踪數據，避免內存泄漏"""
        try:
            now = datetime.now()
            # 每小時清理一次
            if (now - self._last_cleanup).total_seconds() < self._cleanup_interval:
                return
            
            self._last_cleanup = now
            
            # 清理超過24小時的點擊記錄
            expired_keys = []
            for key, info in self._click_tracking.items():
                first_click_time = info.get("first_click_time")
                if first_click_time and (now - first_click_time).total_seconds() > 86400:  # 24小時
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._click_tracking[key]
            
            # 清理超過24小時的最佳手氣提示記錄
            # 注意：這裡我們保留所有記錄，因為需要防止重複提示
            # 如果內存壓力大，可以考慮只保留最近7天的記錄
            
            # 清理超過7天的紅包通知記錄
            expired_redpacket_ids = []
            for redpacket_id, notification_info in self._redpacket_notifications.items():
                participants = notification_info.get("participants", [])
                if participants:
                    # participants 是字典列表，每個字典包含 timestamp
                    timestamps = [p.get("timestamp") for p in participants if isinstance(p, dict) and p.get("timestamp")]
                    if timestamps:
                        last_participant_time = max(timestamps)
                        if isinstance(last_participant_time, datetime) and (now - last_participant_time).total_seconds() > 604800:  # 7天
                            expired_redpacket_ids.append(redpacket_id)
            
            for redpacket_id in expired_redpacket_ids:
                del self._redpacket_notifications[redpacket_id]
            
            # 清理超過24小時的每小時參與計數
            expired_hourly_keys = []
            for key in self._hourly_participation.keys():
                # key 格式: "account_id:YYYY-MM-DD-HH"
                parts = key.split(":")
                if len(parts) >= 4:
                    try:
                        hour_key = "-".join(parts[1:4])  # "YYYY-MM-DD-HH"
                        hour_time = datetime.strptime(hour_key, "%Y-%m-%d-%H")
                        if (now - hour_time).total_seconds() > 86400:  # 24小時
                            expired_hourly_keys.append(key)
                    except (ValueError, IndexError):
                        # 格式錯誤，清理
                        expired_hourly_keys.append(key)
            
            for key in expired_hourly_keys:
                del self._hourly_participation[key]
            
            if expired_keys or expired_redpacket_ids or expired_hourly_keys:
                logger.debug(
                    f"清理了 {len(expired_keys)} 個點擊記錄、"
                    f"{len(expired_redpacket_ids)} 個紅包通知記錄和"
                    f"{len(expired_hourly_keys)} 個每小時計數記錄"
                )
                
        except Exception as e:
            logger.warning(f"清理舊數據失敗: {e}")
    
    def _increment_hourly_participation(self, account_id: str):
        """增加指定賬號的當前小時參與計數"""
        now = datetime.now()
        hour_key = now.strftime("%Y-%m-%d-%H")
        key = f"{account_id}:{hour_key}"
        
        if key not in self._hourly_participation:
            self._hourly_participation[key] = 0
        
        self._hourly_participation[key] += 1
        logger.debug(f"賬號 {account_id} 當前小時 ({hour_key}) 參與次數: {self._hourly_participation[key]}")
    
    def get_hourly_participation_count(
        self,
        account_id: str,
        max_per_hour: Optional[int] = None
    ) -> int:
        """
        獲取指定賬號在當前小時的參與次數
        
        Args:
            account_id: 賬號ID
            max_per_hour: 每小時最大參與次數（可選，用於日誌）
        
        Returns:
            當前小時的參與次數
        """
        now = datetime.now()
        hour_key = now.strftime("%Y-%m-%d-%H")
        key = f"{account_id}:{hour_key}"
        
        count = self._hourly_participation.get(key, 0)
        
        if max_per_hour:
            logger.debug(
                f"賬號 {account_id} 當前小時 ({hour_key}) 參與次數: {count}/{max_per_hour}"
            )
        
        return count
    

