# 修復 cache.py 缺失函數

> **日期**: 2025-12-01  
> **錯誤**: `ImportError: cannot import name 'cached' from 'app.core.cache'`  
> **原因**: 服務器上的 `cache.py` 缺少 `cached` 和 `invalidate_cache` 函數

---

## 🔍 檢查服務器上的 cache.py

執行以下命令檢查服務器上的文件：

```bash
cd /home/ubuntu/liaotian/deployment-package/admin-backend
grep -n "def cached" app/core/cache.py
grep -n "def invalidate_cache" app/core/cache.py
```

---

## 🔧 修復方案：添加缺失的函數

如果函數不存在，執行以下 Python 腳本添加：

```bash
cd /home/ubuntu/liaotian/deployment-package/admin-backend

python3 << 'PYTHON_EOF'
cache_file = 'app/core/cache.py'

# 讀取文件
with open(cache_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 檢查是否已存在
if 'def cached(prefix: str = "cache"' in content:
    print("✅ cached 函數已存在")
    exit(0)

# 添加缺失的函數（追加到文件末尾）
additional_code = '''

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

# 備份原文件
import shutil
shutil.copy(cache_file, cache_file + '.bak')
print(f"✅ 已備份原文件: {cache_file}.bak")

# 追加到文件末尾
with open(cache_file, 'a', encoding='utf-8') as f:
    f.write(additional_code)

print("✅ 已添加 cached 和 invalidate_cache 函數")
PYTHON_EOF
```

---

**先執行檢查命令，告訴我結果，然後應用修復！**
