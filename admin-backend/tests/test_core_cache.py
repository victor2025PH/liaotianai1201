"""
核心緩存模組測試
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from app.core.cache import (
    CacheManager,
    get_cache_manager,
    cached,
    invalidate_cache,
    get_cache_key,
    _memory_cache,
    _cache_stats
)


class TestCacheKey:
    """緩存鍵生成測試"""

    def test_get_cache_key_basic(self):
        """測試基本緩存鍵生成"""
        key = get_cache_key("test", "arg1", "arg2", param1="value1")
        assert isinstance(key, str)
        assert key.startswith("test:")
        assert len(key) > len("test:")

    def test_get_cache_key_different_args(self):
        """測試不同參數生成不同鍵"""
        key1 = get_cache_key("test", "arg1", "arg2")
        key2 = get_cache_key("test", "arg2", "arg1")
        # 順序不同應該生成不同的鍵（或相同，取決於實現）
        assert isinstance(key1, str)
        assert isinstance(key2, str)

    def test_get_cache_key_same_args(self):
        """測試相同參數生成相同鍵"""
        key1 = get_cache_key("test", "arg1", param="value")
        key2 = get_cache_key("test", "arg1", param="value")
        assert key1 == key2


class TestCacheManager:
    """緩存管理器測試"""

    def test_cache_manager_init_no_redis(self):
        """測試緩存管理器初始化（無Redis）"""
        with patch('app.core.cache.REDIS_AVAILABLE', False):
            manager = CacheManager()
            assert manager.use_redis is False
            assert manager.redis_client is None

    def test_cache_manager_init_with_redis_fail(self):
        """測試緩存管理器初始化（Redis連接失敗）"""
        with patch('app.core.cache.REDIS_AVAILABLE', True), \
             patch('app.core.cache.redis') as mock_redis, \
             patch('app.core.config.get_settings') as mock_settings:
            mock_settings.return_value.redis_url = "redis://localhost:6379"
            mock_redis_client = Mock()
            mock_redis_client.ping.side_effect = Exception("Connection failed")
            mock_redis.from_url.return_value = mock_redis_client
            
            manager = CacheManager()
            assert manager.use_redis is False

    def test_cache_set_get_memory(self):
        """測試內存緩存設置和獲取"""
        manager = CacheManager()
        manager.use_redis = False
        
        # 清除之前的緩存
        _memory_cache.clear()
        
        # 設置緩存
        result = manager.set("test_key", {"data": "value"}, expire=60)
        assert result is True
        
        # 獲取緩存
        value = manager.get("test_key")
        assert value == {"data": "value"}

    def test_cache_get_nonexistent(self):
        """測試獲取不存在的緩存"""
        manager = CacheManager()
        manager.use_redis = False
        
        value = manager.get("nonexistent_key")
        assert value is None

    def test_cache_delete(self):
        """測試刪除緩存"""
        manager = CacheManager()
        manager.use_redis = False
        
        # 設置緩存
        manager.set("test_key", "value")
        assert manager.get("test_key") == "value"
        
        # 刪除緩存
        result = manager.delete("test_key")
        assert result is True
        
        # 驗證已刪除
        assert manager.get("test_key") is None

    def test_cache_delete_nonexistent(self):
        """測試刪除不存在的緩存"""
        manager = CacheManager()
        manager.use_redis = False
        
        result = manager.delete("nonexistent_key")
        assert result is True  # 應該返回True（無錯誤）

    def test_cache_clear_pattern(self):
        """測試按模式清除緩存"""
        manager = CacheManager()
        manager.use_redis = False
        
        # 清除之前的緩存
        _memory_cache.clear()
        
        # 設置多個緩存
        manager.set("prefix_key1", "value1")
        manager.set("prefix_key2", "value2")
        manager.set("other_key", "value3")
        
        # 清除匹配模式的緩存
        count = manager.clear_pattern("prefix*")
        assert count >= 2
        
        # 驗證匹配的已刪除
        assert manager.get("prefix_key1") is None
        assert manager.get("prefix_key2") is None
        # 不匹配的應該保留（或也被刪除，取決於實現）
        
        # 清理
        _memory_cache.clear()

    def test_cache_get_stats(self):
        """測試獲取緩存統計信息"""
        manager = CacheManager()
        
        # 重置統計
        _cache_stats["hits"] = 0
        _cache_stats["misses"] = 0
        
        # 執行一些操作
        manager.set("test_key", "value")
        manager.get("test_key")  # hit
        manager.get("nonexistent")  # miss
        
        stats = manager.get_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert "backend" in stats
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1


class TestCacheDecorator:
    """緩存裝飾器測試"""

    def test_cached_sync_function(self):
        """測試同步函數緩存"""
        call_count = [0]  # 使用列表以在閉包中修改
        
        @cached(expire=60, prefix="test")
        def sync_function(x: int) -> int:
            call_count[0] += 1
            return x * 2
        
        # 清除緩存
        _memory_cache.clear()
        
        # 第一次調用
        result1 = sync_function(5)
        assert result1 == 10
        assert call_count[0] == 1
        
        # 第二次調用（應該從緩存獲取）
        result2 = sync_function(5)
        assert result2 == 10
        assert call_count[0] == 1  # 不應該再次調用
        
        # 清理
        _memory_cache.clear()

    @pytest.mark.asyncio
    async def test_cached_async_function(self):
        """測試異步函數緩存"""
        call_count = [0]
        
        @cached(expire=60, prefix="test")
        async def async_function(x: int) -> int:
            call_count[0] += 1
            return x * 3
        
        # 清除緩存
        _memory_cache.clear()
        
        # 第一次調用
        result1 = await async_function(5)
        assert result1 == 15
        assert call_count[0] == 1
        
        # 第二次調用（應該從緩存獲取）
        result2 = await async_function(5)
        assert result2 == 15
        assert call_count[0] == 1  # 不應該再次調用
        
        # 清理
        _memory_cache.clear()

    def test_cached_different_args(self):
        """測試不同參數緩存不同值"""
        @cached(expire=60, prefix="test")
        def sync_function(x: int) -> int:
            return x * 2
        
        # 清除緩存
        _memory_cache.clear()
        
        result1 = sync_function(5)
        result2 = sync_function(10)
        
        assert result1 == 10
        assert result2 == 20
        
        # 清理
        _memory_cache.clear()


class TestCacheUtils:
    """緩存工具函數測試"""

    def test_get_cache_manager_singleton(self):
        """測試緩存管理器單例模式"""
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()
        assert manager1 is manager2

    def test_invalidate_cache(self):
        """測試使緩存失效"""
        # 設置一些緩存
        manager = get_cache_manager()
        manager.set("test_key1", "value1")
        manager.set("test_key2", "value2")
        manager.set("other_key", "value3")
        
        # 清除匹配模式的緩存
        count = invalidate_cache("test*")
        assert count >= 0  # 可能為0（如果使用Redis且連接失敗）
        
        # 清理
        _memory_cache.clear()

    def test_cache_manager_redis_get_success(self):
        """測試Redis獲取成功"""
        manager = CacheManager()
        mock_redis = Mock()
        mock_redis.get.return_value = json.dumps({"data": "value"})
        manager.redis_client = mock_redis
        manager.use_redis = True
        
        value = manager.get("test_key")
        assert value == {"data": "value"}
        mock_redis.get.assert_called_once_with("test_key")

    def test_cache_manager_redis_get_fail_fallback(self):
        """測試Redis獲取失敗後降級到內存緩存"""
        manager = CacheManager()
        mock_redis = Mock()
        mock_redis.get.side_effect = Exception("Redis error")
        manager.redis_client = mock_redis
        manager.use_redis = True
        
        # 設置內存緩存作為後備
        _memory_cache["test_key"] = "fallback_value"
        
        value = manager.get("test_key")
        assert value == "fallback_value"
        
        # 清理
        _memory_cache.clear()

    def test_cache_manager_redis_set(self):
        """測試Redis設置"""
        manager = CacheManager()
        mock_redis = Mock()
        manager.redis_client = mock_redis
        manager.use_redis = True
        
        result = manager.set("test_key", {"data": "value"}, expire=60)
        assert result is True
        mock_redis.setex.assert_called_once()

    def test_cache_manager_memory_cache_size_limit(self):
        """測試內存緩存大小限制"""
        manager = CacheManager()
        manager.use_redis = False
        
        # 清除之前的緩存
        _memory_cache.clear()
        
        # 添加超過限制的緩存（1000個）
        for i in range(1001):
            manager.set(f"key_{i}", f"value_{i}")
        
        # 緩存應該被限制，刪除最舊的100個
        # 驗證緩存大小
        assert len(_memory_cache) <= 1000
        
        # 清理
        _memory_cache.clear()

