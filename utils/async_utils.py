import asyncio
import inspect
import random
import time
from collections import deque
from typing import Any, Awaitable, Callable, Optional


class AsyncRateLimiter:
    """
    簡易異步節流器：限制在指定期間內的最大請求數量。
    """

    def __init__(self, max_calls: int, period: float) -> None:
        if max_calls <= 0 or period <= 0:
            raise ValueError("max_calls 與 period 需為正數")
        self._max_calls = max_calls
        self._period = period
        self._timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            loop = asyncio.get_running_loop()
            now = loop.time()
            while self._timestamps and now - self._timestamps[0] >= self._period:
                self._timestamps.popleft()
            if len(self._timestamps) >= self._max_calls:
                wait_time = self._period - (now - self._timestamps[0])
                await asyncio.sleep(wait_time)
                now = loop.time()
                while self._timestamps and now - self._timestamps[0] >= self._period:
                    self._timestamps.popleft()
            self._timestamps.append(loop.time())


async def maybe_await(callable_obj: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """
    同時兼容同步與異步可調用對象，返回結果時自動 await coroutine。
    """
    result = callable_obj(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


async def run_in_thread(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """
    使用 asyncio.to_thread 將阻塞函式丟到背景執行。
    """
    return await asyncio.to_thread(func, *args, **kwargs)


async def async_sleep_with_jitter(min_delay: float, max_delay: float) -> None:
    """
    在異步上下文中以隨機延遲進行睡眠，避免規律化請求。
    """
    if min_delay < 0 or max_delay < 0:
        raise ValueError("延遲時間需為正數")
    if max_delay < min_delay:
        min_delay, max_delay = max_delay, min_delay
    delay = random.uniform(min_delay, max_delay)
    await asyncio.sleep(delay)

