# 立即修復 cache.py - 執行命令

> **日期**: 2025-12-01  
> **問題**: 服務器上的 `cache.py` 缺少 `cached` 函數

---

## 🚀 一鍵修復命令

在服務器上執行以下命令：

```bash
cd /home/ubuntu/liaotian/deployment-package/admin-backend && \
python3 << 'PYEOF'
import sys
import shutil

cache_file = 'app/core/cache.py'

# 讀取文件
with open(cache_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 檢查是否已存在
if 'def cached(prefix: str = "cache"' in content:
    print("✅ cached 函數已存在")
    sys.exit(0)

print("❌ cached 函數不存在，正在添加...")

# 備份
shutil.copy(cache_file, cache_file + '.bak')
print(f"✅ 已備份: {cache_file}.bak")

# 添加函數
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
```

---

**執行這個命令修復 cache.py，然後告訴我結果！**
