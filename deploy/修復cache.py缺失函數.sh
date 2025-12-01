#!/bin/bash
# 修復服務器上 cache.py 缺失的函數

cd /home/ubuntu/liaotian/deployment-package/admin-backend

echo "檢查 cache.py 文件..."
if [ ! -f "app/core/cache.py" ]; then
    echo "❌ cache.py 文件不存在"
    exit 1
fi

echo "檢查是否包含 cached 函數..."
if grep -q "def cached(prefix: str = \"cache\"" app/core/cache.py; then
    echo "✅ cached 函數已存在"
    exit 0
fi

echo "❌ cached 函數不存在，正在添加..."

# 備份原文件
cp app/core/cache.py app/core/cache.py.bak
echo "✅ 已備份原文件"

# 添加缺失的函數
python3 << 'PYEOF'
cache_file = 'app/core/cache.py'

additional = '''

def cached(prefix: str = "cache", ttl: Optional[int] = None, expire: Optional[int] = None):
    """
    緩存裝飾器（獨立函數版本）
    
    Usage:
        @cached(prefix="user", ttl=600)
        async def get_user(user_id: int):
            # 函數邏輯
            pass
    """
    ttl = ttl or expire
    cache_manager = get_cache_manager()
    return cache_manager.cached(prefix=prefix, ttl=ttl)


def invalidate_cache(pattern: str) -> int:
    """
    使緩存失效（同步版本，可在異步上下文中安全調用）
    只清除內存緩存，避免異步調用問題
    
    Args:
        pattern: 緩存鍵模式（支持 * 通配符）
    
    Returns:
        清除的緩存數量
    """
    try:
        cache_manager = get_cache_manager()
        keys_to_delete = [k for k in cache_manager.memory_cache.keys() if pattern.replace("*", "") in k]
        for key in keys_to_delete:
            if key in cache_manager.memory_cache:
                del cache_manager.memory_cache[key]
        return len(keys_to_delete)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"清除緩存失敗: {e}，繼續執行")
        return 0
'''

with open(cache_file, 'a', encoding='utf-8') as f:
    f.write(additional)

print("✅ 已添加 cached 和 invalidate_cache 函數")
PYEOF

echo "✅ 修復完成"
