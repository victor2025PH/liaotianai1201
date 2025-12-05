"""
🧧 紅包遊戲 API 完整客戶端
基於 Lucky Red API 文檔 (api.usdt2026.cc)

功能：
- 完整 API 對接
- 炸彈紅包支持
- 錯誤重試機制
- 遊戲策略引擎
"""

import asyncio
import random
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import json

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)


# ==================== 配置 ====================

@dataclass
class RedPacketAPIConfig:
    """紅包 API 配置"""
    api_url: str = "https://api.usdt2026.cc"  # 必須使用 HTTPS
    api_key: str = "test-key-2024"
    
    # 超時設置
    timeout: float = 30.0
    connect_timeout: float = 10.0
    
    # 重試設置
    max_retries: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0
    retry_exponential_base: float = 2.0
    
    # 限流設置
    rate_limit_per_minute: int = 60
    
    @classmethod
    def from_env(cls) -> "RedPacketAPIConfig":
        import os
        return cls(
            api_url=os.getenv("REDPACKET_API_URL", "https://api.usdt2026.cc"),
            api_key=os.getenv("REDPACKET_API_KEY", "test-key-2024"),
        )


# ==================== 數據模型 ====================

class Currency(Enum):
    """貨幣類型"""
    USDT = "usdt"
    TON = "ton"
    STARS = "stars"
    POINTS = "points"


class PacketType(Enum):
    """紅包類型"""
    RANDOM = "random"   # 手氣紅包
    EQUAL = "equal"     # 均分紅包


@dataclass
class UserBalance:
    """用戶餘額"""
    user_id: int
    balances: Dict[str, float] = field(default_factory=dict)
    
    def get_balance(self, currency: str = "usdt") -> float:
        return self.balances.get(currency, 0.0)


@dataclass
class RedPacketInfo:
    """紅包信息"""
    packet_id: str
    packet_uuid: str
    sender_id: int
    currency: str
    packet_type: str
    total_amount: float
    total_count: int
    claimed_count: int = 0
    claimed_amount: float = 0.0
    message: str = ""
    bomb_number: Optional[int] = None
    is_bomb: bool = False
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    @property
    def remaining_count(self) -> int:
        return self.total_count - self.claimed_count
    
    @property
    def remaining_amount(self) -> float:
        return self.total_amount - self.claimed_amount
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    @property
    def is_empty(self) -> bool:
        return self.remaining_count <= 0


@dataclass
class ClaimResult:
    """領取結果"""
    success: bool
    claimed_amount: float = 0.0
    is_bomb_hit: bool = False
    penalty_amount: float = 0.0
    error_message: str = ""
    
    @property
    def net_amount(self) -> float:
        """淨收益（領取金額 - 踩雷賠付）"""
        if self.is_bomb_hit:
            return self.claimed_amount - self.penalty_amount
        return self.claimed_amount


# ==================== 錯誤重試裝飾器 ====================

class RetryableError(Exception):
    """可重試的錯誤"""
    pass


class NonRetryableError(Exception):
    """不可重試的錯誤"""
    pass


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (RetryableError, httpx.TimeoutException, httpx.ConnectError)
):
    """
    重試裝飾器 - 指數退避策略
    
    Args:
        max_retries: 最大重試次數
        base_delay: 基礎延遲（秒）
        max_delay: 最大延遲（秒）
        exponential_base: 指數基數
        retryable_exceptions: 可重試的異常類型
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # 計算延遲（指數退避 + 隨機抖動）
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay
                        )
                        jitter = delay * random.uniform(0.1, 0.3)
                        actual_delay = delay + jitter
                        
                        logger.warning(
                            f"請求失敗 (嘗試 {attempt + 1}/{max_retries + 1}): {e}. "
                            f"等待 {actual_delay:.1f}秒 後重試..."
                        )
                        await asyncio.sleep(actual_delay)
                    else:
                        logger.error(f"請求失敗，已達最大重試次數: {e}")
                except NonRetryableError:
                    raise
            
            raise last_exception
        
        return wrapper
    return decorator


# ==================== API 客戶端 ====================

class RedPacketAPIClient:
    """紅包 API 客戶端"""
    
    # AI 帳號列表
    AI_ACCOUNTS = [
        639277358115,  # AI-1
        639543603735,  # AI-2
        639952948692,  # AI-3
        639454959591,  # AI-4
        639542360349,  # AI-5
        639950375245,  # AI-6
    ]
    
    def __init__(self, config: RedPacketAPIConfig = None):
        self.config = config or RedPacketAPIConfig.from_env()
        self._client: Optional[httpx.AsyncClient] = None
        
        # 限流追蹤
        self._request_times: List[float] = []
        
        # 統計
        self.stats = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "retries_total": 0,
            "packets_sent": 0,
            "packets_claimed": 0,
            "amount_sent": 0.0,
            "amount_claimed": 0.0,
            "bomb_hits": 0,
        }
    
    async def _ensure_client(self):
        """確保 HTTP 客戶端存在"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    self.config.timeout,
                    connect=self.config.connect_timeout
                )
            )
    
    def _get_headers(self, user_id: int) -> Dict[str, str]:
        """獲取請求頭"""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "X-Telegram-User-Id": str(user_id),
            "Content-Type": "application/json"
        }
    
    async def _check_rate_limit(self):
        """檢查限流"""
        now = time.time()
        minute_ago = now - 60
        
        # 清理舊請求記錄
        self._request_times = [t for t in self._request_times if t > minute_ago]
        
        if len(self._request_times) >= self.config.rate_limit_per_minute:
            # 需要等待
            wait_time = 60 - (now - self._request_times[0])
            if wait_time > 0:
                logger.warning(f"觸發限流，等待 {wait_time:.1f}秒")
                await asyncio.sleep(wait_time)
        
        self._request_times.append(now)
    
    def _handle_error_response(self, status_code: int, response_data: dict):
        """處理錯誤響應"""
        error_msg = response_data.get("error", {}).get("detail", "未知錯誤")
        
        if status_code == 401:
            raise NonRetryableError(f"API Key 無效: {error_msg}")
        elif status_code == 403:
            raise NonRetryableError(f"用戶被封禁: {error_msg}")
        elif status_code == 404:
            raise NonRetryableError(f"資源不存在: {error_msg}")
        elif status_code == 400:
            raise NonRetryableError(f"請求參數錯誤: {error_msg}")
        elif status_code >= 500:
            raise RetryableError(f"服務器錯誤 ({status_code}): {error_msg}")
        else:
            raise NonRetryableError(f"請求失敗 ({status_code}): {error_msg}")
    
    # ==================== API 方法 ====================
    
    async def health_check(self) -> bool:
        """健康檢查"""
        await self._ensure_client()
        
        try:
            response = await self._client.get(
                f"{self.config.api_url}/api/v2/ai/status"
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return False
    
    @with_retry()
    async def get_balance(self, user_id: int) -> UserBalance:
        """查詢餘額"""
        await self._ensure_client()
        await self._check_rate_limit()
        
        self.stats["requests_total"] += 1
        
        response = await self._client.get(
            f"{self.config.api_url}/api/v2/ai/wallet/balance",
            headers=self._get_headers(user_id)
        )
        
        if response.status_code != 200:
            self.stats["requests_failed"] += 1
            self._handle_error_response(response.status_code, response.json())
        
        self.stats["requests_success"] += 1
        data = response.json()
        
        return UserBalance(
            user_id=user_id,
            balances=data.get("data", {}).get("balances", {})
        )
    
    @with_retry()
    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """獲取用戶資料"""
        await self._ensure_client()
        await self._check_rate_limit()
        
        self.stats["requests_total"] += 1
        
        response = await self._client.get(
            f"{self.config.api_url}/api/v2/ai/user/profile",
            headers=self._get_headers(user_id)
        )
        
        if response.status_code != 200:
            self.stats["requests_failed"] += 1
            self._handle_error_response(response.status_code, response.json())
        
        self.stats["requests_success"] += 1
        return response.json().get("data", {})
    
    @with_retry()
    async def send_packet(
        self,
        sender_id: int,
        total_amount: float,
        total_count: int,
        currency: str = "usdt",
        packet_type: str = "random",
        message: str = "🧧 紅包來了",
        bomb_number: Optional[int] = None
    ) -> Optional[RedPacketInfo]:
        """
        發送紅包
        
        Args:
            sender_id: 發送者 Telegram ID
            total_amount: 總金額
            total_count: 份數 (1-100)
            currency: 貨幣類型 (usdt/ton/stars/points)
            packet_type: 紅包類型 (random/equal)
            message: 祝福語
            bomb_number: 炸彈數字 0-9 (設置後為炸彈紅包)
        
        Returns:
            紅包信息
        """
        await self._ensure_client()
        await self._check_rate_limit()
        
        self.stats["requests_total"] += 1
        
        payload = {
            "currency": currency,
            "packet_type": packet_type,
            "total_amount": total_amount,
            "total_count": total_count,
            "message": message
        }
        
        if bomb_number is not None:
            if bomb_number < 0 or bomb_number > 9:
                raise NonRetryableError("炸彈數字必須是 0-9")
            if total_count not in [5, 10]:
                raise NonRetryableError("炸彈紅包份數必須是 5 或 10")
            payload["bomb_number"] = bomb_number
        
        response = await self._client.post(
            f"{self.config.api_url}/api/v2/ai/packets/send",
            headers=self._get_headers(sender_id),
            json=payload
        )
        
        if response.status_code != 200:
            self.stats["requests_failed"] += 1
            self._handle_error_response(response.status_code, response.json())
        
        self.stats["requests_success"] += 1
        self.stats["packets_sent"] += 1
        self.stats["amount_sent"] += total_amount
        
        data = response.json().get("data", {})
        
        return RedPacketInfo(
            packet_id=data.get("packet_id", ""),
            packet_uuid=data.get("packet_id", ""),  # API 返回的是 packet_id
            sender_id=sender_id,
            currency=currency,
            packet_type=packet_type,
            total_amount=total_amount,
            total_count=total_count,
            message=message,
            bomb_number=bomb_number,
            is_bomb=bomb_number is not None,
            created_at=datetime.now()
        )
    
    @with_retry()
    async def claim_packet(
        self,
        user_id: int,
        packet_uuid: str
    ) -> ClaimResult:
        """
        領取紅包
        
        Args:
            user_id: 領取者 Telegram ID
            packet_uuid: 紅包 UUID
        
        Returns:
            領取結果
        """
        await self._ensure_client()
        await self._check_rate_limit()
        
        self.stats["requests_total"] += 1
        
        response = await self._client.post(
            f"{self.config.api_url}/api/v2/ai/packets/claim",
            headers=self._get_headers(user_id),
            json={"packet_uuid": packet_uuid}
        )
        
        data = response.json()
        
        if response.status_code != 200:
            self.stats["requests_failed"] += 1
            error_detail = data.get("error", {}).get("detail", "")
            
            # 某些錯誤不需要重試
            if "已領取" in error_detail or "already" in error_detail.lower():
                return ClaimResult(success=False, error_message="已經領取過")
            if "已搶完" in error_detail or "empty" in error_detail.lower():
                return ClaimResult(success=False, error_message="紅包已搶完")
            if "已過期" in error_detail or "expired" in error_detail.lower():
                return ClaimResult(success=False, error_message="紅包已過期")
            
            self._handle_error_response(response.status_code, data)
        
        self.stats["requests_success"] += 1
        self.stats["packets_claimed"] += 1
        
        result_data = data.get("data", {})
        claimed_amount = result_data.get("claimed_amount", 0)
        is_bomb_hit = result_data.get("is_bomb_hit", False)
        penalty_amount = result_data.get("penalty_amount", 0)
        
        self.stats["amount_claimed"] += claimed_amount
        if is_bomb_hit:
            self.stats["bomb_hits"] += 1
        
        return ClaimResult(
            success=True,
            claimed_amount=claimed_amount,
            is_bomb_hit=is_bomb_hit,
            penalty_amount=penalty_amount
        )
    
    @with_retry()
    async def get_packet_info(
        self,
        user_id: int,
        packet_uuid: str
    ) -> Optional[RedPacketInfo]:
        """獲取紅包詳情"""
        await self._ensure_client()
        await self._check_rate_limit()
        
        self.stats["requests_total"] += 1
        
        response = await self._client.get(
            f"{self.config.api_url}/api/v2/ai/packets/{packet_uuid}",
            headers=self._get_headers(user_id)
        )
        
        if response.status_code != 200:
            self.stats["requests_failed"] += 1
            return None
        
        self.stats["requests_success"] += 1
        data = response.json().get("data", {})
        
        return RedPacketInfo(
            packet_id=data.get("packet_id", ""),
            packet_uuid=packet_uuid,
            sender_id=data.get("sender_id", 0),
            currency=data.get("currency", "usdt"),
            packet_type=data.get("packet_type", "random"),
            total_amount=data.get("total_amount", 0),
            total_count=data.get("total_count", 0),
            claimed_count=data.get("claimed_count", 0),
            claimed_amount=data.get("claimed_amount", 0),
            message=data.get("message", ""),
            bomb_number=data.get("bomb_number"),
            is_bomb=data.get("bomb_number") is not None
        )
    
    @with_retry()
    async def transfer(
        self,
        from_user_id: int,
        to_user_id: int,
        amount: float,
        currency: str = "usdt",
        note: str = ""
    ) -> bool:
        """內部轉帳"""
        await self._ensure_client()
        await self._check_rate_limit()
        
        self.stats["requests_total"] += 1
        
        response = await self._client.post(
            f"{self.config.api_url}/api/v2/ai/wallet/transfer",
            headers=self._get_headers(from_user_id),
            json={
                "to_user_id": to_user_id,
                "currency": currency,
                "amount": amount,
                "note": note
            }
        )
        
        if response.status_code != 200:
            self.stats["requests_failed"] += 1
            self._handle_error_response(response.status_code, response.json())
        
        self.stats["requests_success"] += 1
        return True
    
    async def close(self):
        """關閉客戶端"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return self.stats.copy()


# ==================== 遊戲策略引擎 ====================

class GameStrategy(Enum):
    """遊戲策略"""
    CONSERVATIVE = "conservative"    # 保守策略
    BALANCED = "balanced"            # 平衡策略
    AGGRESSIVE = "aggressive"        # 激進策略
    SMART = "smart"                  # 智能策略


@dataclass
class StrategyConfig:
    """策略配置"""
    # 發紅包設置
    send_probability: float = 0.1        # 發紅包概率
    send_amount_min: float = 1.0         # 最小金額
    send_amount_max: float = 5.0         # 最大金額
    send_count_min: int = 3              # 最小份數
    send_count_max: int = 5              # 最大份數
    
    # 搶紅包設置
    grab_probability: float = 0.9        # 搶紅包概率
    grab_delay_min: float = 0.5          # 最小延遲
    grab_delay_max: float = 3.0          # 最大延遲
    
    # 炸彈紅包設置
    bomb_enabled: bool = False           # 是否發炸彈紅包
    bomb_probability: float = 0.1        # 發炸彈紅包概率
    bomb_claim_probability: float = 0.5  # 搶炸彈紅包概率
    
    # 餘額管理
    min_balance: float = 10.0            # 最低餘額閾值
    
    @classmethod
    def from_strategy(cls, strategy: GameStrategy) -> "StrategyConfig":
        """根據策略創建配置"""
        if strategy == GameStrategy.CONSERVATIVE:
            return cls(
                send_probability=0.05,
                send_amount_min=0.5,
                send_amount_max=2.0,
                grab_probability=0.95,
                grab_delay_min=1.0,
                grab_delay_max=5.0,
                bomb_enabled=False,
                bomb_claim_probability=0.3
            )
        elif strategy == GameStrategy.AGGRESSIVE:
            return cls(
                send_probability=0.2,
                send_amount_min=2.0,
                send_amount_max=10.0,
                grab_probability=0.99,
                grab_delay_min=0.3,
                grab_delay_max=1.5,
                bomb_enabled=True,
                bomb_probability=0.2,
                bomb_claim_probability=0.8
            )
        elif strategy == GameStrategy.SMART:
            return cls(
                send_probability=0.1,
                send_amount_min=1.0,
                send_amount_max=5.0,
                grab_probability=0.9,
                grab_delay_min=0.5,
                grab_delay_max=2.0,
                bomb_enabled=True,
                bomb_probability=0.1,
                bomb_claim_probability=0.6
            )
        else:  # BALANCED
            return cls()


class RedPacketGameEngine:
    """紅包遊戲引擎"""
    
    def __init__(
        self,
        api_client: RedPacketAPIClient,
        strategy: GameStrategy = GameStrategy.BALANCED
    ):
        self.client = api_client
        self.strategy_config = StrategyConfig.from_strategy(strategy)
        
        # AI 餘額緩存
        self.balance_cache: Dict[int, float] = {}
        self._cache_time: Dict[int, datetime] = {}
        self._cache_ttl = timedelta(minutes=5)
        
        # 已領取紅包追蹤
        self.claimed_packets: Dict[int, set] = {}  # user_id -> {packet_uuids}
        
        # 統計
        self.game_stats = {
            "rounds_played": 0,
            "packets_sent": 0,
            "packets_claimed": 0,
            "bombs_sent": 0,
            "bombs_hit": 0,
            "total_profit": 0.0,
            "total_loss": 0.0
        }
    
    async def get_cached_balance(self, user_id: int) -> float:
        """獲取緩存的餘額"""
        now = datetime.now()
        cache_time = self._cache_time.get(user_id)
        
        if cache_time and (now - cache_time) < self._cache_ttl:
            return self.balance_cache.get(user_id, 0)
        
        # 刷新緩存
        try:
            balance = await self.client.get_balance(user_id)
            self.balance_cache[user_id] = balance.get_balance("usdt")
            self._cache_time[user_id] = now
            return self.balance_cache[user_id]
        except Exception as e:
            logger.error(f"獲取餘額失敗: {e}")
            return self.balance_cache.get(user_id, 0)
    
    def should_send_packet(self, user_id: int) -> Tuple[bool, dict]:
        """
        判斷是否應該發紅包
        
        Returns:
            (是否發送, 紅包參數)
        """
        balance = self.balance_cache.get(user_id, 0)
        
        # 餘額不足
        if balance < self.strategy_config.min_balance:
            return False, {}
        
        # 概率判斷
        if random.random() > self.strategy_config.send_probability:
            return False, {}
        
        # 生成紅包參數
        amount = random.uniform(
            self.strategy_config.send_amount_min,
            min(self.strategy_config.send_amount_max, balance * 0.5)
        )
        count = random.randint(
            self.strategy_config.send_count_min,
            self.strategy_config.send_count_max
        )
        
        params = {
            "total_amount": round(amount, 2),
            "total_count": count,
            "packet_type": "random"
        }
        
        # 炸彈紅包判斷
        if self.strategy_config.bomb_enabled:
            if random.random() < self.strategy_config.bomb_probability:
                params["bomb_number"] = random.randint(0, 9)
                params["total_count"] = random.choice([5, 10])
        
        return True, params
    
    def should_claim_packet(
        self,
        user_id: int,
        packet_info: RedPacketInfo
    ) -> bool:
        """判斷是否應該搶紅包"""
        # 已經領取過
        if user_id in self.claimed_packets:
            if packet_info.packet_uuid in self.claimed_packets[user_id]:
                return False
        
        # 是自己發的
        if packet_info.sender_id == user_id:
            return False
        
        # 已搶完
        if packet_info.is_empty:
            return False
        
        # 炸彈紅包特殊處理
        if packet_info.is_bomb:
            if random.random() > self.strategy_config.bomb_claim_probability:
                logger.info(f"[{user_id}] 跳過炸彈紅包")
                return False
        
        # 概率判斷
        return random.random() < self.strategy_config.grab_probability
    
    async def send_packet(
        self,
        sender_id: int,
        **kwargs
    ) -> Optional[RedPacketInfo]:
        """發送紅包"""
        try:
            packet = await self.client.send_packet(sender_id, **kwargs)
            
            if packet:
                self.game_stats["packets_sent"] += 1
                self.game_stats["total_loss"] += kwargs.get("total_amount", 0)
                
                if kwargs.get("bomb_number") is not None:
                    self.game_stats["bombs_sent"] += 1
                
                # 更新餘額緩存
                balance = self.balance_cache.get(sender_id, 0)
                self.balance_cache[sender_id] = balance - kwargs.get("total_amount", 0)
                
                logger.info(
                    f"[{sender_id}] 發送紅包成功: {packet.packet_uuid}, "
                    f"{kwargs.get('total_amount')} USDT, {kwargs.get('total_count')}份"
                    + (f" (炸彈:{kwargs.get('bomb_number')})" if kwargs.get('bomb_number') is not None else "")
                )
            
            return packet
            
        except Exception as e:
            logger.error(f"發送紅包失敗: {e}")
            return None
    
    async def claim_packet(
        self,
        user_id: int,
        packet_uuid: str
    ) -> ClaimResult:
        """領取紅包"""
        # 添加隨機延遲
        delay = random.uniform(
            self.strategy_config.grab_delay_min,
            self.strategy_config.grab_delay_max
        )
        await asyncio.sleep(delay)
        
        try:
            result = await self.client.claim_packet(user_id, packet_uuid)
            
            if result.success:
                # 記錄已領取
                if user_id not in self.claimed_packets:
                    self.claimed_packets[user_id] = set()
                self.claimed_packets[user_id].add(packet_uuid)
                
                # 更新統計
                self.game_stats["packets_claimed"] += 1
                self.game_stats["total_profit"] += result.claimed_amount
                
                if result.is_bomb_hit:
                    self.game_stats["bombs_hit"] += 1
                    self.game_stats["total_loss"] += result.penalty_amount
                    
                    logger.warning(
                        f"[{user_id}] 踩雷! 領取 {result.claimed_amount} USDT, "
                        f"賠付 {result.penalty_amount} USDT"
                    )
                else:
                    logger.info(
                        f"[{user_id}] 領取紅包成功: {result.claimed_amount} USDT"
                    )
                
                # 更新餘額緩存
                balance = self.balance_cache.get(user_id, 0)
                self.balance_cache[user_id] = balance + result.net_amount
            
            return result
            
        except NonRetryableError as e:
            logger.warning(f"[{user_id}] 領取失敗: {e}")
            return ClaimResult(success=False, error_message=str(e))
        except Exception as e:
            logger.error(f"領取紅包異常: {e}")
            return ClaimResult(success=False, error_message=str(e))
    
    def get_game_stats(self) -> Dict[str, Any]:
        """獲取遊戲統計"""
        stats = self.game_stats.copy()
        stats["net_profit"] = stats["total_profit"] - stats["total_loss"]
        stats["win_rate"] = (
            stats["packets_claimed"] / stats["rounds_played"] * 100
            if stats["rounds_played"] > 0 else 0
        )
        return stats
    
    def update_strategy(self, strategy: GameStrategy):
        """更新策略"""
        self.strategy_config = StrategyConfig.from_strategy(strategy)
        logger.info(f"策略已更新為: {strategy.value}")


# 導出
__all__ = [
    "RedPacketAPIConfig",
    "Currency",
    "PacketType",
    "UserBalance",
    "RedPacketInfo",
    "ClaimResult",
    "RedPacketAPIClient",
    "GameStrategy",
    "StrategyConfig",
    "RedPacketGameEngine",
    "RetryableError",
    "NonRetryableError",
    "with_retry"
]
