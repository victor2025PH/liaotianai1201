# 升級實施指南

> **版本**: v1.0  
> **適用於**: 開發升級方案實施  
> **更新日期**: 2025-01-07

---

## 快速開始

### 前置要求

1. **環境準備**
   ```bash
   # Python 環境
   python >= 3.9
   poetry >= 1.5.0
   
   # Node.js 環境
   node >= 18.0.0
   npm >= 9.0.0
   
   # Redis（可選，用於緩存和任務隊列）
   redis >= 7.0.0
   ```

2. **依賴安裝**
   ```bash
   # 後端
   cd admin-backend
   poetry install
   poetry add slowapi celery redis
   
   # 前端
   cd saas-demo
   npm install
   npm install react-window @tanstack/react-query
   ```

---

## 第一階段實施步驟

### 步驟 1: 數據庫連接池配置

#### 1.1 更新數據庫配置

**文件**: `admin-backend/app/db.py`

```python
import logging
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# 連接池配置
pool_config = {
    "poolclass": pool.QueuePool,
    "pool_size": int(getattr(settings, 'database_pool_size', 10)),
    "max_overflow": int(getattr(settings, 'database_max_overflow', 20)),
    "pool_pre_ping": True,
    "pool_recycle": int(getattr(settings, 'database_pool_recycle', 3600)),
    "pool_timeout": int(getattr(settings, 'database_pool_timeout', 30)),
    "echo": False,
    "future": True
}

try:
    engine = create_engine(settings.database_url, **pool_config)
except ModuleNotFoundError as exc:
    logger.warning("無法加載數據庫驅動 %s，回退到內置 SQLite。", exc)
    settings.database_url = "sqlite:///./admin.db"
    # SQLite 使用 NullPool
    pool_config["poolclass"] = pool.NullPool
    engine = create_engine(settings.database_url, **pool_config)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# SQLite 優化
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """SQLite 特定優化"""
    if "sqlite" in settings.database_url:
        cursor = dbapi_conn.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA temp_store=MEMORY")
        except Exception as e:
            logger.warning(f"SQLite 優化失敗: {e}")
        finally:
            cursor.close()

def get_db():
    """獲取數據庫會話"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### 1.2 更新配置類

**文件**: `admin-backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # ... 現有配置 ...
    
    # 數據庫連接池配置
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_recycle: int = 3600
    database_pool_timeout: int = 30
```

#### 1.3 更新環境變量

**文件**: `admin-backend/.env.example`

```env
# 數據庫連接池配置
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_RECYCLE=3600
DATABASE_POOL_TIMEOUT=30
```

### 步驟 2: 創建數據庫索引遷移

#### 2.1 創建遷移文件

```bash
cd admin-backend
poetry run alembic revision -m "add_indexes_for_performance"
```

#### 2.2 編輯遷移文件

**文件**: `admin-backend/alembic/versions/002_add_indexes.py`

```python
"""添加數據庫索引優化查詢性能

Revision ID: 002_add_indexes
Revises: 001_create_group_ai_tables
Create Date: 2025-01-07
"""
from alembic import op
import sqlalchemy as sa

revision = '002_add_indexes'
down_revision = '001_create_group_ai_tables'
branch_labels = None
depends_on = None

def upgrade():
    # 檢查表是否存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'group_ai_accounts' in tables:
        # 群組 AI 賬號表索引
        op.create_index(
            'idx_group_ai_account_status',
            'group_ai_accounts',
            ['status'],
            unique=False,
            if_not_exists=True
        )
        op.create_index(
            'idx_group_ai_account_created',
            'group_ai_accounts',
            ['created_at'],
            unique=False,
            if_not_exists=True
        )
    
    if 'group_ai_scripts' in tables:
        # 劇本表索引
        op.create_index(
            'idx_group_ai_script_active',
            'group_ai_scripts',
            ['is_active'],
            unique=False,
            if_not_exists=True
        )

def downgrade():
    op.drop_index('idx_group_ai_account_status', table_name='group_ai_accounts', if_exists=True)
    op.drop_index('idx_group_ai_account_created', table_name='group_ai_accounts', if_exists=True)
    op.drop_index('idx_group_ai_script_active', table_name='group_ai_scripts', if_exists=True)
```

#### 2.3 執行遷移

```bash
poetry run alembic upgrade head
```

### 步驟 3: 實施 Redis 緩存

#### 3.1 安裝 Redis 客戶端

```bash
poetry add redis
```

#### 3.2 創建緩存服務

**文件**: `admin-backend/app/core/cache.py`

```python
"""
Redis 緩存管理
"""
import json
import hashlib
from typing import Optional, Any, Callable, TypeVar
from functools import wraps
import redis
from app.core.config import get_settings

settings = get_settings()

T = TypeVar('T')

# Redis 連接池
try:
    redis_pool = redis.ConnectionPool.from_url(
        settings.redis_url,
        max_connections=50,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True
    )
    redis_client = redis.Redis(connection_pool=redis_pool)
    
    # 測試連接
    redis_client.ping()
    CACHE_ENABLED = True
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Redis 連接失敗，緩存功能將被禁用: {e}")
    redis_client = None
    CACHE_ENABLED = False


def cache_key(prefix: str, *args, **kwargs) -> str:
    """生成緩存鍵"""
    # 過濾掉不可序列化的參數
    key_data = {
        "prefix": prefix,
        "args": [str(arg) for arg in args],
        "kwargs": {k: str(v) for k, v in kwargs.items()}
    }
    key_str = json.dumps(key_data, sort_keys=True)
    key_hash = hashlib.md5(key_str.encode()).hexdigest()
    return f"cache:{prefix}:{key_hash}"


def cached(prefix: str, ttl: int = 60):
    """緩存裝飾器（支持同步和異步函數）"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if not CACHE_ENABLED:
            return func
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            key = cache_key(prefix, *args, **kwargs)
            
            # 嘗試從緩存獲取
            try:
                cached_value = redis_client.get(key)
                if cached_value:
                    return json.loads(cached_value)
            except Exception:
                pass
            
            # 執行函數
            result = await func(*args, **kwargs)
            
            # 寫入緩存
            try:
                redis_client.setex(
                    key,
                    ttl,
                    json.dumps(result, default=str, ensure_ascii=False)
                )
            except Exception:
                pass
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            key = cache_key(prefix, *args, **kwargs)
            
            # 嘗試從緩存獲取
            try:
                cached_value = redis_client.get(key)
                if cached_value:
                    return json.loads(cached_value)
            except Exception:
                pass
            
            # 執行函數
            result = func(*args, **kwargs)
            
            # 寫入緩存
            try:
                redis_client.setex(
                    key,
                    ttl,
                    json.dumps(result, default=str, ensure_ascii=False)
                )
            except Exception:
                pass
            
            return result
        
        # 判斷是異步還是同步函數
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def invalidate_cache(prefix: str, pattern: str = "*"):
    """清除緩存"""
    if not CACHE_ENABLED:
        return
    
    try:
        keys = redis_client.keys(f"cache:{prefix}:{pattern}")
        if keys:
            redis_client.delete(*keys)
    except Exception:
        pass


def get_cache(key: str) -> Optional[Any]:
    """直接獲取緩存"""
    if not CACHE_ENABLED:
        return None
    
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
    except Exception:
        pass
    return None


def set_cache(key: str, value: Any, ttl: int = 60):
    """直接設置緩存"""
    if not CACHE_ENABLED:
        return
    
    try:
        redis_client.setex(
            key,
            ttl,
            json.dumps(value, default=str, ensure_ascii=False)
        )
    except Exception:
        pass
```

#### 3.3 在 API 中使用緩存

**文件**: `admin-backend/app/api/group_ai/accounts.py`

```python
from app.core.cache import cached, invalidate_cache

@router.get("/", response_model=AccountListResponse)
@cached("accounts_list", ttl=30)
async def list_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # ... 查詢邏輯 ...
    pass

@router.put("/{id}")
async def update_account(
    id: str,
    account_update: AccountUpdate,
    db: Session = Depends(get_db)
):
    # ... 更新邏輯 ...
    
    # 清除緩存
    invalidate_cache("accounts_list")
    
    return updated_account
```

### 步驟 4: 實施 API 限流

#### 4.1 安裝依賴

```bash
poetry add slowapi
```

#### 4.2 配置限流

**文件**: `admin-backend/app/core/limiter.py`

```python
"""
API 限流配置
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

# 限流配置
RATE_LIMITS = {
    "default": "100/minute",
    "auth": "10/minute",      # 認證相關
    "heavy": "20/minute",      # 重操作
    "light": "200/minute",     # 輕操作
    "upload": "10/minute",     # 上傳
}
```

#### 4.3 在 FastAPI 中集成

**文件**: `admin-backend/app/main.py`

```python
from app.core.limiter import limiter, RateLimitExceeded
from slowapi.errors import _rate_limit_exceeded_handler

app = FastAPI(...)

# 添加限流
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

#### 4.4 在路由中使用

```python
from app.core.limiter import limiter, RATE_LIMITS

@router.get("/accounts/")
@limiter.limit(RATE_LIMITS["default"])
async def list_accounts(request: Request, ...):
    ...
```

---

## 測試驗證

### 性能測試腳本

**文件**: `scripts/test_performance.py`

```python
"""
性能測試腳本
"""
import time
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor

API_BASE = "http://localhost:8000/api/v1"

def test_endpoint(endpoint: str, iterations: int = 100):
    """測試端點性能"""
    times = []
    errors = 0
    
    for i in range(iterations):
        start = time.time()
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
            elapsed = time.time() - start
            times.append(elapsed)
            
            if response.status_code != 200:
                errors += 1
        except Exception as e:
            errors += 1
            print(f"請求失敗: {e}")
    
    if times:
        avg = statistics.mean(times)
        p95 = statistics.quantiles(times, n=20)[18]  # 95th percentile
        p99 = statistics.quantiles(times, n=100)[98]  # 99th percentile
        max_time = max(times)
        min_time = min(times)
        
        print(f"\n端點: {endpoint}")
        print(f"  平均響應時間: {avg:.3f}s")
        print(f"  P95: {p95:.3f}s")
        print(f"  P99: {p99:.3f}s")
        print(f"  最大: {max_time:.3f}s")
        print(f"  最小: {min_time:.3f}s")
        print(f"  錯誤數: {errors}/{iterations}")
    
    return {
        "endpoint": endpoint,
        "avg": avg if times else 0,
        "p95": p95 if times else 0,
        "errors": errors
    }

def test_concurrent(endpoint: str, concurrent: int = 10, total: int = 100):
    """並發測試"""
    def make_request():
        start = time.time()
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
            elapsed = time.time() - start
            return {"success": response.status_code == 200, "time": elapsed}
        except Exception as e:
            return {"success": False, "time": 0, "error": str(e)}
    
    with ThreadPoolExecutor(max_workers=concurrent) as executor:
        results = list(executor.map(lambda _: make_request(), range(total)))
    
    success_count = sum(1 for r in results if r.get("success"))
    times = [r["time"] for r in results if r.get("time", 0) > 0]
    
    if times:
        avg = statistics.mean(times)
        print(f"\n並發測試 ({concurrent} 並發, {total} 請求):")
        print(f"  成功率: {success_count}/{total}")
        print(f"  平均響應時間: {avg:.3f}s")

if __name__ == "__main__":
    # 測試各個端點
    endpoints = [
        "/group-ai/accounts",
        "/group-ai/scripts",
        "/group-ai/monitor/accounts",
    ]
    
    for endpoint in endpoints:
        test_endpoint(endpoint, iterations=50)
        test_concurrent(endpoint, concurrent=10, total=50)
```

### 運行測試

```bash
python scripts/test_performance.py
```

---

## 部署檢查清單

### 部署前檢查

- [ ] 數據庫備份完成
- [ ] 遷移腳本測試通過
- [ ] 性能測試通過
- [ ] 單元測試通過
- [ ] 集成測試通過
- [ ] 環境變量配置正確
- [ ] Redis 服務運行正常（如使用）

### 部署步驟

1. **停止服務**
   ```bash
   docker-compose down
   # 或
   pkill -f uvicorn
   ```

2. **備份數據庫**
   ```bash
   cp admin.db admin.db.backup.$(date +%Y%m%d_%H%M%S)
   ```

3. **更新代碼**
   ```bash
   git pull
   ```

4. **安裝依賴**
   ```bash
   cd admin-backend
   poetry install
   ```

5. **執行遷移**
   ```bash
   poetry run alembic upgrade head
   ```

6. **啟動服務**
   ```bash
   docker-compose up -d
   # 或
   poetry run uvicorn app.main:app --reload
   ```

7. **驗證服務**
   ```bash
   curl http://localhost:8000/health
   ```

### 回滾步驟

如果出現問題，可以快速回滾：

1. **停止服務**
2. **恢復數據庫**
   ```bash
   cp admin.db.backup.* admin.db
   ```
3. **回滾代碼**
   ```bash
   git revert HEAD
   ```
4. **回滾遷移**
   ```bash
   poetry run alembic downgrade -1
   ```
5. **重啟服務**

---

## 常見問題

### Q1: Redis 連接失敗

**問題**: 緩存功能無法使用

**解決方案**:
1. 檢查 Redis 服務是否運行: `redis-cli ping`
2. 檢查 `REDIS_URL` 環境變量
3. 系統會自動降級，不影響主功能

### Q2: 遷移失敗

**問題**: Alembic 遷移執行失敗

**解決方案**:
1. 檢查數據庫連接
2. 查看遷移日誌
3. 手動執行 SQL（如需要）
4. 聯繫開發團隊

### Q3: 性能未提升

**問題**: 優化後性能未見改善

**解決方案**:
1. 檢查緩存是否生效
2. 檢查索引是否創建
3. 運行性能測試對比
4. 檢查數據庫連接池配置

---

## 下一步

完成第一階段後，繼續：

1. **第二階段**: 功能完善與用戶體驗優化
2. **第三階段**: 新功能開發

詳細方案見：`docs/DETAILED_UPGRADE_PLAN.md`

---

**文檔結束**

