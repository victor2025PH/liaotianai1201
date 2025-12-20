"""
數據庫查詢優化工具
提供查詢結果緩存和 N+1 查詢優化
"""
import hashlib
import json
import logging
from functools import wraps
from typing import Callable, Any, Optional, Type
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    from app.core.cache import get_cache_manager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("緩存管理器不可用，查詢緩存功能將受限")


def cache_query_result(
    ttl: int = 60,
    key_prefix: str = "query",
    include_args: bool = True,
    include_kwargs: bool = True
):
    """
    緩存查詢結果的裝飾器
    
    Args:
        ttl: 緩存時間（秒）
        key_prefix: 緩存鍵前綴
        include_args: 是否在緩存鍵中包含位置參數
        include_kwargs: 是否在緩存鍵中包含關鍵字參數
    
    Example:
        @cache_query_result(ttl=60)
        async def get_accounts(db: Session, active: bool = True):
            return db.query(Account).filter(Account.active == active).all()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成緩存鍵
            cache_key_parts = [key_prefix, func.__name__]
            
            if include_args:
                # 過濾掉數據庫會話對象（不可序列化）
                filtered_args = [
                    arg for arg in args
                    if not hasattr(arg, 'query')  # 過濾 SQLAlchemy Session
                ]
                if filtered_args:
                    cache_key_parts.append(str(hash(str(filtered_args))))
            
            if include_kwargs:
                # 過濾掉數據庫會話
                filtered_kwargs = {
                    k: v for k, v in kwargs.items()
                    if not hasattr(v, 'query')  # 過濾 SQLAlchemy Session
                }
                if filtered_kwargs:
                    cache_key_parts.append(str(hash(json.dumps(filtered_kwargs, sort_keys=True, default=str))))
            
            cache_key = ":".join(cache_key_parts)
            
            # 嘗試從緩存獲取
            if CACHE_AVAILABLE:
                try:
                    cache = get_cache_manager()
                    cached_result = cache.get(cache_key)  # 使用同步方法
                    if cached_result is not None:
                        logger.debug(f"查詢緩存命中: {func.__name__}")
                        return cached_result
                except Exception as e:
                    logger.debug(f"獲取緩存失敗: {e}")
            
            # 執行查詢
            result = await func(*args, **kwargs)
            
            # 緩存結果
            if CACHE_AVAILABLE:
                try:
                    cache = get_cache_manager()
                    cache.set(cache_key, result, ttl=ttl)  # 使用同步方法
                    logger.debug(f"查詢結果已緩存: {func.__name__} (TTL: {ttl}s)")
                except Exception as e:
                    logger.debug(f"設置緩存失敗: {e}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步函數版本
            cache_key_parts = [key_prefix, func.__name__]
            
            if include_args:
                filtered_args = [
                    arg for arg in args
                    if not hasattr(arg, 'query')
                ]
                if filtered_args:
                    cache_key_parts.append(str(hash(str(filtered_args))))
            
            if include_kwargs:
                filtered_kwargs = {
                    k: v for k, v in kwargs.items()
                    if not hasattr(v, 'query')
                }
                if filtered_kwargs:
                    cache_key_parts.append(str(hash(json.dumps(filtered_kwargs, sort_keys=True, default=str))))
            
            cache_key = ":".join(cache_key_parts)
            
            # 嘗試從緩存獲取
            if CACHE_AVAILABLE:
                try:
                    cache = get_cache_manager()
                    cached_result = cache.get_sync(cache_key)
                    if cached_result is not None:
                        logger.debug(f"查詢緩存命中: {func.__name__}")
                        return cached_result
                except Exception as e:
                    logger.debug(f"獲取緩存失敗: {e}")
            
            # 執行查詢
            result = func(*args, **kwargs)
            
            # 緩存結果
            if CACHE_AVAILABLE:
                try:
                    cache = get_cache_manager()
                    cache.set_sync(cache_key, result, ttl=ttl)
                    logger.debug(f"查詢結果已緩存: {func.__name__} (TTL: {ttl}s)")
                except Exception as e:
                    logger.debug(f"設置緩存失敗: {e}")
            
            return result
        
        # 判斷是異步還是同步函數
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def optimize_query(use_joinedload: bool = False, use_selectinload: bool = False):
    """
    優化查詢的裝飾器（用於修復 N+1 問題）
    
    Args:
        use_joinedload: 使用 joinedload 預加載關聯
        use_selectinload: 使用 selectinload 預加載關聯
    
    Note:
        這個裝飾器主要用於提示開發者，實際優化需要在查詢中使用 joinedload/selectinload
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 這裡可以添加查詢優化邏輯
            # 例如：自動檢測 N+1 查詢並記錄警告
            return func(*args, **kwargs)
        return wrapper
    return decorator


def monitor_query_performance(threshold: float = 1.0):
    """
    監控查詢性能的裝飾器
    
    Args:
        threshold: 慢查詢閾值（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            if duration > threshold:
                logger.warning(
                    f"慢查詢檢測: {func.__name__} 耗時 {duration:.2f} 秒（閾值: {threshold} 秒）",
                    extra={
                        "function": func.__name__,
                        "duration": duration,
                        "threshold": threshold,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }
                )
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            if duration > threshold:
                logger.warning(
                    f"慢查詢檢測: {func.__name__} 耗時 {duration:.2f} 秒（閾值: {threshold} 秒）",
                    extra={
                        "function": func.__name__,
                        "duration": duration,
                        "threshold": threshold
                    }
                )
            
            return result
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
