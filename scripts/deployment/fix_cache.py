#!/usr/bin/env python3
"""修复 cache.py 文件，添加 cached 和 invalidate_cache 函数"""
import sys
import os

cache_file = sys.argv[1] if len(sys.argv) > 1 else "app/core/cache.py"

# 读取文件
with open(cache_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 检查是否已存在 cached 函数
if "def cached(prefix: str = \"cache\"" in content:
    print("✓ cached 函数已存在")
    sys.exit(0)

# 添加函数
additions = """

def cached(prefix: str = "cache", ttl: Optional[int] = None):
    \"\"\"
    缓存装饰器（独立函数版本）
    
    Usage:
        @cached(prefix="user", ttl=600)
        async def get_user(user_id: int):
            # 函数逻辑
            pass
    \"\"\"
    cache_manager = get_cache_manager()
    return cache_manager.cached(prefix=prefix, ttl=ttl)


def invalidate_cache(pattern: str) -> int:
    \"\"\"
    使缓存失效
    
    Args:
        pattern: 缓存键模式（支持 * 通配符）
    
    Returns:
        清除的缓存数量
    \"\"\"
    cache_manager = get_cache_manager()
    return asyncio.run(cache_manager.clear_pattern(pattern))
"""

# 追加到文件末尾
with open(cache_file, 'a', encoding='utf-8') as f:
    f.write(additions)

print("✓ 已添加 cached 和 invalidate_cache 函数")


