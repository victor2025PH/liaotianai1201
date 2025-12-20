"""
統一錯誤處理機制
提供錯誤處理裝飾器和工具函數
"""
import asyncio
import logging
from functools import wraps
from typing import Callable, Any, Optional, Type, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class RetryableError(Exception):
    """可重試的錯誤"""
    pass


class NonRetryableError(Exception):
    """不可重試的錯誤"""
    pass


class NetworkError(RetryableError):
    """網絡錯誤"""
    pass


class DatabaseError(RetryableError):
    """數據庫錯誤"""
    pass


class ValidationError(NonRetryableError):
    """驗證錯誤"""
    pass


def handle_errors(
    retry_times: int = 3,
    retry_delay: float = 1.0,
    log_error: bool = True,
    default_return: Any = None,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    non_retryable_exceptions: Tuple[Type[Exception], ...] = (ValidationError,)
):
    """
    統一錯誤處理裝飾器
    
    Args:
        retry_times: 重試次數
        retry_delay: 重試延遲（秒），會使用指數退避
        log_error: 是否記錄錯誤日誌
        default_return: 失敗時的默認返回值
        retryable_exceptions: 可重試的異常類型
        non_retryable_exceptions: 不可重試的異常類型
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_error = None
            for attempt in range(retry_times):
                try:
                    return await func(*args, **kwargs)
                except non_retryable_exceptions as e:
                    # 不可重試的錯誤，直接拋出
                    if log_error:
                        logger.error(
                            f"函數 {func.__name__} 執行失敗（不可重試）: {e}",
                            exc_info=True,
                            extra={
                                "function": func.__name__,
                                "error_type": type(e).__name__,
                                "args": str(args)[:200],
                                "kwargs": str(kwargs)[:200]
                            }
                        )
                    if default_return is not None:
                        return default_return
                    raise
                except retryable_exceptions as e:
                    last_error = e
                    if log_error:
                        logger.warning(
                            f"函數 {func.__name__} 執行失敗 (嘗試 {attempt + 1}/{retry_times}): {e}",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_attempts": retry_times,
                                "error_type": type(e).__name__,
                                "args": str(args)[:200],
                                "kwargs": str(kwargs)[:200]
                            }
                        )
                    
                    if attempt < retry_times - 1:
                        # 指數退避
                        delay = retry_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                    else:
                        # 最後一次嘗試失敗
                        if log_error:
                            logger.error(
                                f"函數 {func.__name__} 執行失敗（已重試 {retry_times} 次）: {e}",
                                exc_info=True,
                                extra={
                                    "function": func.__name__,
                                    "total_attempts": retry_times,
                                    "error_type": type(e).__name__,
                                    "args": str(args)[:200],
                                    "kwargs": str(kwargs)[:200]
                                }
                            )
                        if default_return is not None:
                            return default_return
                        raise
                except Exception as e:
                    # 其他未預期的錯誤
                    last_error = e
                    if log_error:
                        logger.error(
                            f"函數 {func.__name__} 執行失敗（未預期錯誤）: {e}",
                            exc_info=True,
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "error_type": type(e).__name__,
                                "args": str(args)[:200],
                                "kwargs": str(kwargs)[:200]
                            }
                        )
                    if attempt < retry_times - 1:
                        delay = retry_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                    else:
                        if default_return is not None:
                            return default_return
                        raise
            
            # 如果所有重試都失敗
            if default_return is not None:
                return default_return
            raise last_error
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            """同步函數包裝器"""
            last_error = None
            for attempt in range(retry_times):
                try:
                    return func(*args, **kwargs)
                except non_retryable_exceptions as e:
                    if log_error:
                        logger.error(
                            f"函數 {func.__name__} 執行失敗（不可重試）: {e}",
                            exc_info=True
                        )
                    if default_return is not None:
                        return default_return
                    raise
                except retryable_exceptions as e:
                    last_error = e
                    if log_error:
                        logger.warning(
                            f"函數 {func.__name__} 執行失敗 (嘗試 {attempt + 1}/{retry_times}): {e}"
                        )
                    
                    if attempt < retry_times - 1:
                        import time
                        delay = retry_delay * (2 ** attempt)
                        time.sleep(delay)
                    else:
                        if log_error:
                            logger.error(
                                f"函數 {func.__name__} 執行失敗（已重試 {retry_times} 次）: {e}",
                                exc_info=True
                            )
                        if default_return is not None:
                            return default_return
                        raise
            
            if default_return is not None:
                return default_return
            raise last_error
        
        # 判斷是異步還是同步函數
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    log_error: bool = True,
    **kwargs
) -> Any:
    """
    安全執行函數（同步）
    
    Args:
        func: 要執行的函數
        *args: 位置參數
        default_return: 失敗時的默認返回值
        log_error: 是否記錄錯誤
        **kwargs: 關鍵字參數
        
    Returns:
        函數返回值或 default_return
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            logger.error(f"執行函數 {func.__name__} 失敗: {e}", exc_info=True)
        return default_return


async def safe_execute_async(
    func: Callable,
    *args,
    default_return: Any = None,
    log_error: bool = True,
    **kwargs
) -> Any:
    """
    安全執行函數（異步）
    
    Args:
        func: 要執行的異步函數
        *args: 位置參數
        default_return: 失敗時的默認返回值
        log_error: 是否記錄錯誤
        **kwargs: 關鍵字參數
        
    Returns:
        函數返回值或 default_return
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        if log_error:
            logger.error(f"執行函數 {func.__name__} 失敗: {e}", exc_info=True)
        return default_return
