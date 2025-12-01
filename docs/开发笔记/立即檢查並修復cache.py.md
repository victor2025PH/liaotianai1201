# 立即檢查並修復 cache.py

> **日期**: 2025-12-01

---

## 🔍 步驟 1: 檢查服務器上的 cache.py

```bash
cd /home/ubuntu/liaotian/deployment-package/admin-backend

# 檢查是否包含 cached 函數
grep -n "def cached" app/core/cache.py
grep -n "def invalidate_cache" app/core/cache.py
```

---

## 🔧 步驟 2: 如果函數不存在，添加它們

執行以下 Python 腳本：

```bash
cd /home/ubuntu/liaotian/deployment-package/admin-backend

python3 << 'EOF'
import sys

cache_file = 'app/core/cache.py'

# 讀取文件
with open(cache_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 檢查是否已存在
if 'def cached(prefix: str = "cache"' in content:
    print("✅ cached 函數已存在")
    sys.exit(0)

# 備份
import shutil
shutil.copy(cache_file, cache_file + '.bak')
print(f"✅ 已備份: {cache_file}.bak")

# 添加函數
additional = '''

def cached(prefix: str = "cache", ttl: Optional[int] = None, expire: Optional[int] = None):
    """
    緩存裝飾器（獨立函數版本）
    """
    ttl = ttl or expire
    cache_manager = get_cache_manager()
    return cache_manager.cached(prefix=prefix, ttl=ttl)


def invalidate_cache(pattern: str) -> int:
    """
    使緩存失效
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
        logger.warning(f"清除緩存失敗: {e}")
        return 0
'''

with open(cache_file, 'a', encoding='utf-8') as f:
    f.write(additional)

print("✅ 已添加 cached 和 invalidate_cache 函數")
EOF
```

---

**先執行步驟 1 檢查，告訴我結果！**
