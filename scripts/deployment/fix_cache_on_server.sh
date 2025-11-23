#!/bin/bash
# 在服务器上修复 cache.py 文件

cd /home/ubuntu/admin-backend/app/core

# 检查是否已存在 cached 函数
if grep -q "def cached(prefix: str = \"cache\"" cache.py; then
    echo "✓ cached 函数已存在"
else
    echo "添加 cached 和 invalidate_cache 函数..."
    cat >> cache.py << 'ENDFUNC'

def cached(prefix: str = "cache", ttl: Optional[int] = None):
    """
    缓存装饰器（独立函数版本）
    """
    cache_manager = get_cache_manager()
    return cache_manager.cached(prefix=prefix, ttl=ttl)


def invalidate_cache(pattern: str) -> int:
    """
    使缓存失效
    """
    cache_manager = get_cache_manager()
    return asyncio.run(cache_manager.clear_pattern(pattern))
ENDFUNC
    echo "✓ 函数已添加"
fi

# 验证
python3 -c "from app.core.cache import cached; print('✓ cached 函数可用')" 2>&1


