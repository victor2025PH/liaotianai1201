"""
通用重试机制模块
提供装饰器和工具函数，用于自动重试失败的操作
"""
import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Type, Tuple, Optional, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class RetryableError(Exception):
    """可重试的错误基类"""
    pass


class NetworkError(RetryableError):
    """网络错误（可重试）"""
    pass


class TimeoutError(RetryableError):
    """超时错误（可重试）"""
    pass


class SessionError(RetryableError):
    """Session 错误（可重试）"""
    pass


class NonRetryableError(Exception):
    """不可重试的错误"""
    pass


class RetryStrategy(str, Enum):
    """重试策略"""
    FIXED = "fixed"  # 固定间隔
    EXPONENTIAL = "exponential"  # 指数退避
    LINEAR = "linear"  # 线性增长


class RetryConfig:
    """重试配置"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        on_failure: Optional[Callable[[Exception], None]] = None
    ):
        """
        初始化重试配置
        
        Args:
            max_attempts: 最大重试次数
            initial_delay: 初始延迟（秒）
            max_delay: 最大延迟（秒）
            strategy: 重试策略
            retryable_exceptions: 可重试的异常类型
            on_retry: 重试回调函数 (attempt, exception) -> None
            on_failure: 失败回调函数 (exception) -> None
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.retryable_exceptions = retryable_exceptions or (Exception,)
        self.on_retry = on_retry
        self.on_failure = on_failure
    
    def calculate_delay(self, attempt: int) -> float:
        """
        计算重试延迟
        
        Args:
            attempt: 当前尝试次数（从 0 开始）
        
        Returns:
            延迟时间（秒）
        """
        if self.strategy == RetryStrategy.FIXED:
            delay = self.initial_delay
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.initial_delay * (2 ** attempt)
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay * (attempt + 1)
        else:
            delay = self.initial_delay
        
        return min(delay, self.max_delay)


def is_retryable_error(exception: Exception, retryable_types: Tuple[Type[Exception], ...]) -> bool:
    """
    判断错误是否可重试
    
    Args:
        exception: 异常对象
        retryable_types: 可重试的异常类型
    
    Returns:
        是否可重试
    """
    # 检查异常类型
    if isinstance(exception, NonRetryableError):
        return False
    
    if isinstance(exception, RetryableError):
        return True
    
    # 检查是否在可重试类型列表中
    for retryable_type in retryable_types:
        if isinstance(exception, retryable_type):
            return True
    
    # 检查常见的网络错误
    error_str = str(exception).lower()
    network_keywords = [
        "connection", "timeout", "network", "unreachable",
        "reset", "refused", "broken pipe", "temporary failure"
    ]
    if any(keyword in error_str for keyword in network_keywords):
        return True
    
    return False


async def retry_async(
    func: Callable,
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> Any:
    """
    异步函数重试装饰器实现
    
    Args:
        func: 要重试的异步函数
        config: 重试配置
        *args: 函数位置参数
        **kwargs: 函数关键字参数
    
    Returns:
        函数返回值
    
    Raises:
        最后一次尝试的异常
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            # 检查是否可重试
            if not is_retryable_error(e, config.retryable_exceptions):
                if config.on_failure:
                    config.on_failure(e)
                raise
            
            # 如果是最后一次尝试，不再重试
            if attempt >= config.max_attempts - 1:
                if config.on_failure:
                    config.on_failure(e)
                raise
            
            # 计算延迟时间
            delay = config.calculate_delay(attempt)
            
            # 调用重试回调
            if config.on_retry:
                try:
                    config.on_retry(attempt + 1, e)
                except Exception:
                    pass
            
            logger.warning(
                f"操作失败，{delay:.2f}秒后重试 (尝试 {attempt + 1}/{config.max_attempts}): {e}"
            )
            
            await asyncio.sleep(delay)
    
    # 如果所有重试都失败，抛出最后一次异常
    if config.on_failure:
        config.on_failure(last_exception)
    raise last_exception


def retry_sync(
    func: Callable,
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> Any:
    """
    同步函数重试装饰器实现
    
    Args:
        func: 要重试的同步函数
        config: 重试配置
        *args: 函数位置参数
        **kwargs: 函数关键字参数
    
    Returns:
        函数返回值
    
    Raises:
        最后一次尝试的异常
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            # 检查是否可重试
            if not is_retryable_error(e, config.retryable_exceptions):
                if config.on_failure:
                    config.on_failure(e)
                raise
            
            # 如果是最后一次尝试，不再重试
            if attempt >= config.max_attempts - 1:
                if config.on_failure:
                    config.on_failure(e)
                raise
            
            # 计算延迟时间
            delay = config.calculate_delay(attempt)
            
            # 调用重试回调
            if config.on_retry:
                try:
                    config.on_retry(attempt + 1, e)
                except Exception:
                    pass
            
            logger.warning(
                f"操作失败，{delay:.2f}秒后重试 (尝试 {attempt + 1}/{config.max_attempts}): {e}"
            )
            
            time.sleep(delay)
    
    # 如果所有重试都失败，抛出最后一次异常
    if config.on_failure:
        config.on_failure(last_exception)
    raise last_exception


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    on_failure: Optional[Callable[[Exception], None]] = None
):
    """
    重试装饰器（用于异步函数）
    
    Usage:
        @with_retry(max_attempts=3, initial_delay=1.0)
        async def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                max_delay=max_delay,
                strategy=strategy,
                retryable_exceptions=retryable_exceptions,
                on_retry=on_retry,
                on_failure=on_failure
            )
            return await retry_async(func, config, *args, **kwargs)
        return wrapper
    return decorator


def with_retry_sync(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    on_failure: Optional[Callable[[Exception], None]] = None
):
    """
    重试装饰器（用于同步函数）
    
    Usage:
        @with_retry_sync(max_attempts=3, initial_delay=1.0)
        def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                max_delay=max_delay,
                strategy=strategy,
                retryable_exceptions=retryable_exceptions,
                on_retry=on_retry,
                on_failure=on_failure
            )
            return retry_sync(func, config, *args, **kwargs)
        return wrapper
    return decorator


# 预定义的重试配置
NETWORK_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    initial_delay=2.0,
    max_delay=30.0,
    strategy=RetryStrategy.EXPONENTIAL,
    retryable_exceptions=(NetworkError, TimeoutError, ConnectionError, OSError)
)

SESSION_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=5.0,
    max_delay=60.0,
    strategy=RetryStrategy.EXPONENTIAL,
    retryable_exceptions=(SessionError, ConnectionError)
)

API_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=10.0,
    strategy=RetryStrategy.EXPONENTIAL,
    retryable_exceptions=(TimeoutError, ConnectionError)
)

