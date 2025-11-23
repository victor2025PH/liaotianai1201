import asyncio
import logging
import random
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.types import Message

from tools.session_manager.account_db import AccountRecord

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    max_per_minute: int
    burst: int


@dataclass
class DispatchStrategyConfig:
    mode: str = "round_robin"  # round_robin, weighted, host_priority
    weights: Dict[str, int] = field(default_factory=dict)  # phone -> weight
    host_phones: Sequence[str] = field(default_factory=list)


@dataclass
class ThrottleState:
    timestamps: deque = field(default_factory=deque)
    burst_counter: int = 0
    reset_at: datetime = field(default_factory=lambda: datetime.utcnow())


class RateLimiter:
    def __init__(self, config: RateLimitConfig) -> None:
        self.config = config
        self.state = ThrottleState()

    async def acquire(self) -> None:
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=1)
        while self.state.timestamps and self.state.timestamps[0] < window_start:
            self.state.timestamps.popleft()
        if len(self.state.timestamps) >= self.config.max_per_minute:
            delay = (self.state.timestamps[0] + timedelta(minutes=1) - now).total_seconds()
            logger.debug("RateLimiter: 达到每分钟上限，休眠 %.2fs", delay)
            await asyncio.sleep(max(0, delay))
        if self.state.burst_counter >= self.config.burst:
            delay = (self.state.reset_at - now).total_seconds()
            if delay > 0:
                logger.debug("RateLimiter: Burst 已滿，休眠 %.2fs", delay)
                await asyncio.sleep(delay)
            self.state.burst_counter = 0
            self.state.reset_at = datetime.utcnow() + timedelta(seconds=10)
        self.state.timestamps.append(datetime.utcnow())
        self.state.burst_counter += 1


class DispatchManager:
    def __init__(
        self,
        accounts: Iterable[AccountRecord],
        per_account_limit: RateLimitConfig,
        per_group_limit: RateLimitConfig,
        strategy_config: DispatchStrategyConfig,
    ) -> None:
        account_list = list(accounts)
        self.accounts: Dict[str, AccountRecord] = {acc.phone: acc for acc in account_list}
        self.per_account_limiters: Dict[str, RateLimiter] = {
            acc.phone: RateLimiter(per_account_limit) for acc in account_list
        }
        self.per_group_limiters: Dict[int, RateLimiter] = {}
        self.per_group_limit_config = per_group_limit
        self.strategy_config = strategy_config
        self._rr_index = 0

    def _get_group_limiter(self, group_id: int) -> RateLimiter:
        if group_id not in self.per_group_limiters:
            self.per_group_limiters[group_id] = RateLimiter(self.per_group_limit_config)
        return self.per_group_limiters[group_id]

    def select_account(self, group_id: int) -> Optional[AccountRecord]:
        candidates = list(self.accounts.values())
        if not candidates:
            return None
        mode = self.strategy_config.mode
        if mode == "host_priority":
            for phone in self.strategy_config.host_phones:
                if phone in self.accounts:
                    return self.accounts[phone]
        if mode == "weighted" and self.strategy_config.weights:
            weights = [self.strategy_config.weights.get(acc.phone, 1) for acc in candidates]
            return random.choices(candidates, weights=weights, k=1)[0]
        if mode == "round_robin":
            account = candidates[self._rr_index % len(candidates)]
            self._rr_index = (self._rr_index + 1) % len(candidates)
            return account
        return random.choice(candidates)

    async def dispatch_send_message(
        self,
        client_map: Dict[str, Client],
        group_id: int,
        text: str,
        reply_to_message_id: Optional[int] = None,
    ) -> Optional[Message]:
        account = self.select_account(group_id)
        if not account:
            logger.warning("無可用帳號發送訊息")
            return None
        limiter = self.per_account_limiters.get(account.phone)
        if limiter:
            await limiter.acquire()
        group_limiter = self._get_group_limiter(group_id)
        await group_limiter.acquire()
        client = client_map.get(account.phone)
        if not client:
            logger.warning("帳號 %s 尚未初始化客戶端", account.phone)
            return None
        for attempt in range(3):
            try:
                return await client.send_message(
                    chat_id=group_id,
                    text=text,
                    reply_to_message_id=reply_to_message_id,
                )
            except FloodWait as exc:
                logger.warning("帳號 %s 遭遇 FloodWait：%s 秒", account.phone, exc.value)
                await asyncio.sleep(exc.value)
            except Exception as exc:
                logger.exception("帳號 %s 發送訊息失敗：%s (第 %d 次)", account.phone, exc, attempt + 1)
                await asyncio.sleep(1)
        return None

