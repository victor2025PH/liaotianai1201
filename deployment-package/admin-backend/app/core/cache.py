"""
智能缓存系统
提供多级缓存、自动失效、缓存预热等功能
"""
import logging
import json
import hashlib
from typing import Any, Optional, Callable, Dict
from datetime import datetime, timedelta
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis 未安装，将使用内存缓存")


class CacheManager:
    """智能缓存管理器"""
    
    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 300):
        """
        初始化缓存管理器
        
        Args:
            redis_url: Redis 连接 URL（可选）
            default_ttl: 默认缓存时间（秒）
        """
        self.default_ttl = default_ttl
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.redis_client: Optional[redis.Redis] = None
        
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("Redis 缓存已启用")
            except Exception as e:
                logger.warning(f"Redis 连接失败，使用内存缓存: {e}")
                self.redis_client = None
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = {
            "prefix": prefix,
            "args": str(args),
            "kwargs": json.dumps(kwargs, sort_keys=True)
        }
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        # 先尝试 Redis
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.debug(f"Redis 获取失败: {e}")
        
        # 尝试内存缓存
        if key in self.memory_cache:
            cache_item = self.memory_cache[key]
            if datetime.now() < cache_item["expires_at"]:
                return cache_item["value"]
            else:
                del self.memory_cache[key]
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        ttl = ttl or self.default_ttl
        
        # 设置 Redis
        if self.redis_client:
            try:
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value, default=str)
                )
            except Exception as e:
                logger.debug(f"Redis 设置失败: {e}")
        
        # 设置内存缓存
        self.memory_cache[key] = {
            "value": value,
            "expires_at": datetime.now() + timedelta(seconds=ttl)
        }
        
        return True
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.debug(f"Redis 删除失败: {e}")
        
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        return True
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        count = 0
        
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    count += self.redis_client.delete(*keys)
            except Exception as e:
                logger.debug(f"Redis 清除模式失败: {e}")
        
        # 清除内存缓存
        keys_to_delete = [k for k in self.memory_cache.keys() if pattern.replace("*", "") in k]
        for key in keys_to_delete:
            del self.memory_cache[key]
            count += 1
        
        return count
    
    def cached(self, prefix: str = "cache", ttl: Optional[int] = None):
        """
        缓存装饰器
        
        Usage:
            @cache_manager.cached(prefix="user", ttl=600)
            async def get_user(user_id: int):
                # 函数逻辑
                pass
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = self._generate_key(prefix, *args, **kwargs)
                
                # 尝试从缓存获取
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"缓存命中: {cache_key}")
                    return cached_value
                
                # 执行函数
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                # 存入缓存
                await self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator


# 全局缓存管理器实例
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        from app.core.config import get_settings
        settings = get_settings()
        redis_url = getattr(settings, "redis_url", None) or None
        default_ttl = getattr(settings, "cache_default_ttl", 300)
        _cache_manager = CacheManager(redis_url=redis_url, default_ttl=default_ttl)
    return _cache_manager


def cache_key(prefix: str, *args, **kwargs) -> str:
    """生成缓存键的辅助函数"""
    return get_cache_manager()._generate_key(prefix, *args, **kwargs)
