# 現在執行 - 修復 cache.py

> **日期**: 2025-12-01  
> **錯誤**: `ImportError: cannot import name 'cached' from 'app.core.cache'`

---

## 🚀 立即執行修復

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
print("✅ 已備份原文件")

# 添加函數
additional = '''

def cached(prefix: str = "cache", ttl: Optional[int] = None, expire: Optional[int] = None):
    """緩存裝飾器（獨立函數版本）"""
    ttl = ttl or expire
    cache_manager = get_cache_manager()
    return cache_manager.cached(prefix=prefix, ttl=ttl)


def invalidate_cache(pattern: str) -> int:
    """使緩存失效"""
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
PYEOF
```

---

## ✅ 修復後重啟服務

修復完成後，重啟後端服務：

```bash
cd /home/ubuntu/liaotian/deployment-package/admin-backend && \
pkill -f "uvicorn.*app.main:app" && sleep 3 && \
VENV_PYTHON=/home/ubuntu/liaotian/admin-backend/.venv/bin/python3 && \
export PYTHONPATH=/home/ubuntu/liaotian/deployment-package && \
nohup "$VENV_PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 & \
sleep 5 && \
curl http://localhost:8000/health
```

---

**先執行修復命令，然後告訴我結果！**
