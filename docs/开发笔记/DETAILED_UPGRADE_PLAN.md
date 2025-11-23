# 詳細開發升級方案

> **方案版本**: v1.0  
> **制定日期**: 2025-01-07  
> **適用版本**: v0.8 → v1.0  
> **預計完成時間**: 4-6 個月

---

## 目錄

1. [升級概述](#升級概述)
2. [第一階段：性能優化與穩定性提升（1-2 個月）](#第一階段性能優化與穩定性提升1-2-個月)
3. [第二階段：功能完善與用戶體驗優化（2-4 個月）](#第二階段功能完善與用戶體驗優化2-4-個月)
4. [第三階段：新功能開發（3-6 個月）](#第三階段新功能開發3-6-個月)
5. [測試策略](#測試策略)
6. [部署方案](#部署方案)
7. [風險管理](#風險管理)
8. [時間表與里程碑](#時間表與里程碑)

---

## 升級概述

### 升級目標

1. **性能提升 50-70%**
   - API 響應時間 P95 < 500ms
   - 數據庫查詢優化
   - 前端渲染性能提升

2. **穩定性提升 80%**
   - 錯誤處理完善
   - 系統監控增強
   - 自動恢復機制

3. **功能完整性提升至 95%**
   - 權限管理系統
   - 實時通知
   - 批量操作

4. **用戶體驗提升 60-80%**
   - 界面優化
   - 操作反饋改進
   - 移動端適配

### 技術棧升級

- **後端**: FastAPI + SQLAlchemy + Redis
- **前端**: Next.js 16 + React 19 + TypeScript
- **數據庫**: SQLite → PostgreSQL（可選）
- **緩存**: Redis
- **任務隊列**: Celery（可選）

---

## 第一階段：性能優化與穩定性提升（1-2 個月）

### 1.1 數據庫優化（2 週）

#### 1.1.1 實施連接池

**文件**: `admin-backend/app/db.py`

**當前代碼**:
```python
engine = create_engine(settings.database_url, echo=False, future=True)
```

**升級後代碼**:
```python
from sqlalchemy.pool import QueuePool
from sqlalchemy import event

# 連接池配置
pool_config = {
    "pool_size": 10,           # 連接池大小
    "max_overflow": 20,        # 最大溢出連接數
    "pool_pre_ping": True,     # 連接前檢查
    "pool_recycle": 3600,      # 連接回收時間（秒）
    "pool_timeout": 30,        # 獲取連接超時時間
    "echo": False,
    "future": True
}

engine = create_engine(settings.database_url, **pool_config)

# 連接池事件監聽
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """SQLite 特定優化"""
    if "sqlite" in settings.database_url:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB 緩存
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# 連接池統計
@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """連接檢查出事件"""
    pass

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """連接歸還事件"""
    pass
```

**配置文件更新**: `admin-backend/.env.example`
```env
# 數據庫連接池配置
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_RECYCLE=3600
DATABASE_POOL_TIMEOUT=30
```

#### 1.1.2 添加數據庫索引

**創建遷移文件**: `admin-backend/alembic/versions/002_add_indexes.py`

```python
"""添加數據庫索引優化查詢性能

Revision ID: 002_add_indexes
Revises: 001_create_group_ai_tables
Create Date: 2025-01-07
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002_add_indexes'
down_revision = '001_create_group_ai_tables'
branch_labels = None
depends_on = None

def upgrade():
    # 群組 AI 賬號表索引
    op.create_index(
        'idx_group_ai_account_status',
        'group_ai_accounts',
        ['status'],
        unique=False
    )
    op.create_index(
        'idx_group_ai_account_created',
        'group_ai_accounts',
        ['created_at'],
        unique=False
    )
    op.create_index(
        'idx_group_ai_account_session',
        'group_ai_accounts',
        ['session_file'],
        unique=False
    )
    
    # 劇本表索引
    op.create_index(
        'idx_group_ai_script_active',
        'group_ai_scripts',
        ['is_active'],
        unique=False
    )
    op.create_index(
        'idx_group_ai_script_version',
        'group_ai_scripts',
        ['version'],
        unique=False
    )
    
    # 監控指標表索引
    op.create_index(
        'idx_group_ai_metrics_account_time',
        'group_ai_metrics',
        ['account_id', 'timestamp'],
        unique=False
    )
    op.create_index(
        'idx_group_ai_metrics_type',
        'group_ai_metrics',
        ['metric_type'],
        unique=False
    )
    
    # 告警表索引
    op.create_index(
        'idx_group_ai_alerts_status',
        'group_ai_alerts',
        ['status'],
        unique=False
    )
    op.create_index(
        'idx_group_ai_alerts_created',
        'group_ai_alerts',
        ['created_at'],
        unique=False
    )

def downgrade():
    op.drop_index('idx_group_ai_account_status', table_name='group_ai_accounts')
    op.drop_index('idx_group_ai_account_created', table_name='group_ai_accounts')
    op.drop_index('idx_group_ai_account_session', table_name='group_ai_accounts')
    op.drop_index('idx_group_ai_script_active', table_name='group_ai_scripts')
    op.drop_index('idx_group_ai_script_version', table_name='group_ai_scripts')
    op.drop_index('idx_group_ai_metrics_account_time', table_name='group_ai_metrics')
    op.drop_index('idx_group_ai_metrics_type', table_name='group_ai_metrics')
    op.drop_index('idx_group_ai_alerts_status', table_name='group_ai_alerts')
    op.drop_index('idx_group_ai_alerts_created', table_name='group_ai_alerts')
```

**執行遷移**:
```bash
cd admin-backend
poetry run alembic upgrade head
```

#### 1.1.3 查詢優化

**文件**: `admin-backend/app/api/group_ai/accounts.py`

**優化前**:
```python
@router.get("/", response_model=AccountListResponse)
async def list_accounts(db: Session = Depends(get_db)):
    accounts = db.query(GroupAIAccount).all()
    return AccountListResponse(accounts=[...], total=len(accounts))
```

**優化後**:
```python
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select, func

@router.get("/", response_model=AccountListResponse)
async def list_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    # 構建查詢
    query = select(GroupAIAccount)
    
    # 狀態過濾
    if status:
        query = query.where(GroupAIAccount.status == status)
    
    # 獲取總數（優化：使用 COUNT）
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()
    
    # 分頁查詢（使用 LIMIT/OFFSET）
    query = query.order_by(GroupAIAccount.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    # 執行查詢
    accounts = db.execute(query).scalars().all()
    
    return AccountListResponse(
        accounts=[AccountResponse.from_orm(acc) for acc in accounts],
        total=total,
        page=page,
        page_size=page_size
    )
```

#### 1.1.4 實施查詢緩存

**文件**: `admin-backend/app/core/cache.py` (新建)

```python
"""
Redis 緩存管理
"""
import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
import redis
from app.core.config import get_settings

settings = get_settings()

# Redis 連接池
redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    max_connections=50,
    decode_responses=True
)
redis_client = redis.Redis(connection_pool=redis_pool)


def cache_key(prefix: str, *args, **kwargs) -> str:
    """生成緩存鍵"""
    key_data = f"{prefix}:{args}:{kwargs}"
    key_hash = hashlib.md5(key_data.encode()).hexdigest()
    return f"cache:{prefix}:{key_hash}"


def cached(prefix: str, ttl: int = 60):
    """緩存裝飾器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成緩存鍵
            key = cache_key(prefix, *args, **kwargs)
            
            # 嘗試從緩存獲取
            try:
                cached_value = redis_client.get(key)
                if cached_value:
                    return json.loads(cached_value)
            except Exception as e:
                # 緩存失敗不影響主流程
                pass
            
            # 執行函數
            result = await func(*args, **kwargs)
            
            # 寫入緩存
            try:
                redis_client.setex(
                    key,
                    ttl,
                    json.dumps(result, default=str)
                )
            except Exception as e:
                # 緩存失敗不影響主流程
                pass
            
            return result
        return wrapper
    return decorator


def invalidate_cache(prefix: str, pattern: str = "*"):
    """清除緩存"""
    try:
        keys = redis_client.keys(f"cache:{prefix}:{pattern}")
        if keys:
            redis_client.delete(*keys)
    except Exception:
        pass
```

**使用示例**:
```python
from app.core.cache import cached, invalidate_cache

@router.get("/accounts/")
@cached("accounts_list", ttl=30)
async def list_accounts(...):
    ...

# 更新賬號時清除緩存
@router.put("/accounts/{id}")
async def update_account(...):
    ...
    invalidate_cache("accounts_list")
    ...
```

---

### 1.2 API 性能優化（2 週）

#### 1.2.1 實施 API 限流

**安裝依賴**:
```bash
cd admin-backend
poetry add slowapi
```

**文件**: `admin-backend/app/core/limiter.py` (新建)

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
    "auth": "10/minute",
    "heavy": "20/minute",
    "light": "200/minute"
}
```

**文件**: `admin-backend/app/main.py`

```python
from app.core.limiter import limiter, RATE_LIMITS, RateLimitExceeded
from slowapi.errors import _rate_limit_exceeded_handler

app = FastAPI(...)

# 添加限流異常處理
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 全局限流中間件
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # 跳過健康檢查端點
    if request.url.path == "/health":
        return await call_next(request)
    return await call_next(request)
```

**使用示例**:
```python
from app.core.limiter import limiter, RATE_LIMITS

@router.get("/accounts/")
@limiter.limit(RATE_LIMITS["default"])
async def list_accounts(request: Request, ...):
    ...
```

#### 1.2.2 實施異步任務隊列

**安裝依賴**:
```bash
poetry add celery redis
```

**文件**: `admin-backend/app/core/celery_app.py` (新建)

```python
"""
Celery 任務隊列配置
"""
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "group_ai_tasks",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 分鐘
    task_soft_time_limit=240,  # 4 分鐘
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)
```

**文件**: `admin-backend/app/tasks/__init__.py` (新建)

```python
"""
異步任務定義
"""
from app.core.celery_app import celery_app

@celery_app.task(bind=True, max_retries=3)
def process_ai_generation(self, account_id: str, message: dict):
    """異步處理 AI 生成"""
    try:
        # AI 生成邏輯
        from group_ai_service.ai_generator import AIGenerator
        generator = AIGenerator()
        result = generator.generate(message)
        return result
    except Exception as exc:
        # 重試邏輯
        raise self.retry(exc=exc, countdown=60)

@celery_app.task
def batch_update_accounts(account_ids: list, config: dict):
    """批量更新賬號"""
    # 批量操作邏輯
    pass
```

**API 使用**:
```python
from app.tasks import process_ai_generation

@router.post("/messages/process")
async def process_message(message: dict):
    # 異步處理
    task = process_ai_generation.delay(account_id, message)
    return {"task_id": task.id, "status": "processing"}
```

#### 1.2.3 優化前端超時策略

**文件**: `saas-demo/src/lib/api-client.ts`

```typescript
// 不同端點的超時配置
const API_TIMEOUTS: Record<string, number> = {
  default: 5000,        // 5 秒
  list: 5000,          // 列表查詢
  detail: 10000,       // 詳情查詢
  create: 15000,       // 創建操作
  update: 15000,       // 更新操作
  delete: 10000,       // 刪除操作
  batch: 30000,        // 批量操作
  upload: 60000,       // 文件上傳
};

export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit & {
    timeout?: number;
    showErrorToast?: boolean;
    showSuccessToast?: boolean;
    successMessage?: string;
  }
): Promise<ApiResult<T>> {
  const {
    timeout,
    showErrorToast = true,
    showSuccessToast = false,
    successMessage,
    ...fetchOptions
  } = options || {};

  // 根據端點類型確定超時時間
  const endpointType = getEndpointType(endpoint);
  const apiTimeout = timeout || API_TIMEOUTS[endpointType] || API_TIMEOUTS.default;

  // ... 其餘代碼
}

function getEndpointType(endpoint: string): string {
  if (endpoint.includes('/batch')) return 'batch';
  if (endpoint.includes('/upload')) return 'upload';
  if (endpoint.match(/\/\d+$/)) return 'detail';  // 帶 ID 的端點
  if (['POST', 'PUT', 'PATCH'].includes(method)) return 'create';
  if (method === 'DELETE') return 'delete';
  return 'list';
}
```

---

### 1.3 內存優化（1 週）

#### 1.3.1 實施 LRU 緩存

**文件**: `group_ai_service/dialogue_manager.py`

```python
from functools import lru_cache
from collections import OrderedDict
import time

class LRUCache:
    """LRU 緩存實現"""
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}
    
    def get(self, key: str):
        """獲取緩存"""
        if key not in self.cache:
            return None
        
        # 檢查過期
        if time.time() - self.timestamps[key] > self.ttl:
            self.delete(key)
            return None
        
        # 移動到末尾（最近使用）
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def set(self, key: str, value: Any):
        """設置緩存"""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                # 刪除最舊的
                oldest_key = next(iter(self.cache))
                self.delete(oldest_key)
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def delete(self, key: str):
        """刪除緩存"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)

class DialogueManager:
    def __init__(self):
        self.contexts: Dict[str, DialogueContext] = {}
        self.context_cache = LRUCache(max_size=200, ttl=3600)  # 1 小時 TTL
        # ...
    
    def get_context(self, account_id: str, group_id: int) -> DialogueContext:
        """獲取上下文（帶緩存）"""
        context_key = f"{account_id}:{group_id}"
        
        # 嘗試從緩存獲取
        cached_context = self.context_cache.get(context_key)
        if cached_context:
            return cached_context
        
        # 從內存獲取或創建
        context = self.contexts.get(context_key)
        if not context:
            context = DialogueContext(account_id, group_id)
            self.contexts[context_key] = context
        
        # 更新緩存
        self.context_cache.set(context_key, context)
        return context
    
    def cleanup_inactive_contexts(self):
        """清理非活動上下文"""
        current_time = time.time()
        inactive_threshold = 86400  # 24 小時
        
        keys_to_remove = []
        for key, context in self.contexts.items():
            last_activity = getattr(context, 'last_activity', 0)
            if current_time - last_activity > inactive_threshold:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self.contexts.pop(key, None)
            self.context_cache.delete(key)
```

**定期清理任務**:
```python
import asyncio

async def periodic_cleanup():
    """定期清理任務"""
    while True:
        await asyncio.sleep(3600)  # 每小時清理一次
        dialogue_manager.cleanup_inactive_contexts()

# 在應用啟動時啟動清理任務
asyncio.create_task(periodic_cleanup())
```

---

### 1.4 前端性能優化（2 週）

#### 1.4.1 實施虛擬滾動

**安裝依賴**:
```bash
cd saas-demo
npm install react-window react-window-infinite-loader
```

**文件**: `saas-demo/src/components/ui/virtual-list.tsx` (新建)

```typescript
import React, { useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';
import InfiniteLoader from 'react-window-infinite-loader';

interface VirtualListProps<T> {
  items: T[];
  height: number;
  itemHeight: number;
  renderItem: (props: { index: number; style: React.CSSProperties; data: T }) => React.ReactNode;
  hasNextPage?: boolean;
  loadNextPage?: () => void;
  isNextPageLoading?: boolean;
}

export function VirtualList<T>({
  items,
  height,
  itemHeight,
  renderItem,
  hasNextPage = false,
  loadNextPage,
  isNextPageLoading = false,
}: VirtualListProps<T>) {
  const itemCount = hasNextPage ? items.length + 1 : items.length;
  const isItemLoaded = (index: number) => !hasNextPage || index < items.length;

  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    if (!isItemLoaded(index)) {
      return (
        <div style={style} className="flex items-center justify-center p-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
        </div>
      );
    }

    return renderItem({ index, style, data: items[index] });
  };

  return (
    <InfiniteLoader
      isItemLoaded={isItemLoaded}
      itemCount={itemCount}
      loadMoreItems={loadNextPage || (() => {})}
    >
      {({ onItemsRendered, ref }) => (
        <List
          ref={ref}
          height={height}
          itemCount={itemCount}
          itemSize={itemHeight}
          onItemsRendered={onItemsRendered}
          width="100%"
        >
          {Row}
        </List>
      )}
    </InfiniteLoader>
  );
}
```

**使用示例**:
```typescript
import { VirtualList } from '@/components/ui/virtual-list';

function AccountsList({ accounts }: { accounts: Account[] }) {
  return (
    <VirtualList
      items={accounts}
      height={600}
      itemHeight={80}
      renderItem={({ index, style, data }) => (
        <div style={style}>
          <AccountCard account={data} />
        </div>
      )}
    />
  );
}
```

#### 1.4.2 實施請求去重和緩存

**安裝依賴**:
```bash
npm install @tanstack/react-query
```

**文件**: `saas-demo/src/lib/query-client.ts` (新建)

```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,  // 30 秒
      cacheTime: 5 * 60 * 1000,  // 5 分鐘
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});
```

**文件**: `saas-demo/src/hooks/useAccounts.ts` (新建)

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost, apiPut, apiDelete } from '@/lib/api-client';

export function useAccounts(page: number = 1, pageSize: number = 20) {
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['accounts', page, pageSize],
    queryFn: async () => {
      const result = await apiGet<AccountListResponse>(
        `/group-ai/accounts?page=${page}&page_size=${pageSize}`
      );
      if (!result.ok) throw new Error(result.error?.message);
      return result.data;
    },
  });

  const createAccount = useMutation({
    mutationFn: async (account: CreateAccountRequest) => {
      const result = await apiPost<AccountResponse>('/group-ai/accounts', account);
      if (!result.ok) throw new Error(result.error?.message);
      return result.data;
    },
    onSuccess: () => {
      // 清除緩存，觸發重新獲取
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });

  return {
    accounts: data?.accounts || [],
    total: data?.total || 0,
    isLoading,
    error,
    refetch,
    createAccount,
  };
}
```

---

### 1.5 錯誤處理改進（1 週）

#### 1.5.1 用戶友好錯誤信息

**文件**: `admin-backend/app/core/errors.py` (新建)

```python
"""
統一錯誤處理
"""
from typing import Optional
from fastapi import HTTPException, status

class UserFriendlyError(HTTPException):
    """用戶友好錯誤"""
    
    ERROR_MESSAGES = {
        "DATABASE_ERROR": "數據庫連接失敗，請稍後重試",
        "NETWORK_ERROR": "網絡連接異常，請檢查網絡設置",
        "TIMEOUT": "請求超時，請稍後重試",
        "NOT_FOUND": "請求的資源不存在",
        "VALIDATION_ERROR": "輸入數據格式錯誤，請檢查後重試",
        "PERMISSION_DENIED": "您沒有權限執行此操作",
        "RATE_LIMIT": "請求過於頻繁，請稍後再試",
    }
    
    def __init__(
        self,
        error_code: str,
        detail: Optional[str] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        technical_detail: Optional[str] = None
    ):
        message = self.ERROR_MESSAGES.get(error_code, "發生未知錯誤")
        if detail:
            message = f"{message}: {detail}"
        
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code,
                "message": message,
                "technical_detail": technical_detail  # 僅在開發環境顯示
            }
        )
```

**使用示例**:
```python
from app.core.errors import UserFriendlyError

@router.get("/accounts/{id}")
async def get_account(id: str, db: Session = Depends(get_db)):
    try:
        account = db.query(GroupAIAccount).filter_by(id=id).first()
        if not account:
            raise UserFriendlyError("NOT_FOUND", status_code=404)
        return account
    except Exception as e:
        raise UserFriendlyError(
            "DATABASE_ERROR",
            technical_detail=str(e)
        )
```

#### 1.5.2 全局錯誤處理

**文件**: `admin-backend/app/main.py`

```python
from app.core.errors import UserFriendlyError
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(UserFriendlyError)
async def user_friendly_error_handler(request: Request, exc: UserFriendlyError):
    """用戶友好錯誤處理"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用異常處理"""
    logger.exception(f"未處理的異常: {exc}")
    
    # 生產環境返回通用錯誤，開發環境返回詳細錯誤
    if settings.environment == "development":
        detail = {
            "error_code": "INTERNAL_ERROR",
            "message": "服務器內部錯誤",
            "technical_detail": str(exc)
        }
    else:
        detail = {
            "error_code": "INTERNAL_ERROR",
            "message": "服務器內部錯誤，請聯繫管理員"
        }
    
    return JSONResponse(
        status_code=500,
        content=detail
    )
```

---

## 第二階段：功能完善與用戶體驗優化（2-4 個月）

### 2.1 權限管理系統（3 週）

#### 2.1.1 數據庫模型擴展

**文件**: `admin-backend/app/models/team.py` (新建)

```python
"""
團隊和權限管理模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db import Base

# 團隊成員關聯表
team_member_table = Table(
    'team_members',
    Base.metadata,
    Column('team_id', Integer, ForeignKey('teams.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role', String(50)),  # owner, admin, member
    Column('joined_at', DateTime, default=datetime.utcnow)
)

class Team(Base):
    """團隊表"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    members = relationship("User", secondary=team_member_table, back_populates="teams")
    accounts = relationship("GroupAIAccount", back_populates="team")

class OperationLog(Base):
    """操作審計日誌"""
    __tablename__ = "operation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    action = Column(String(100), nullable=False)  # create, update, delete
    resource_type = Column(String(100), nullable=False)  # account, script
    resource_id = Column(String(100))
    details = Column(JSON)  # 操作詳情
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User", back_populates="operation_logs")
```

#### 2.1.2 權限檢查中間件

**文件**: `admin-backend/app/core/permissions.py` (新建)

```python
"""
權限檢查系統
"""
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.user import User
from app.models.team import Team
from app.api.deps import get_current_user

class Permission:
    """權限定義"""
    ACCOUNT_READ = "account:read"
    ACCOUNT_WRITE = "account:write"
    ACCOUNT_DELETE = "account:delete"
    SCRIPT_READ = "script:read"
    SCRIPT_WRITE = "script:write"
    SCRIPT_DELETE = "script:delete"
    TEAM_MANAGE = "team:manage"

def check_permission(
    required_permission: str,
    resource_team_id: Optional[int] = None
):
    """權限檢查裝飾器"""
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # 超級管理員擁有所有權限
        if current_user.is_superuser:
            return current_user
        
        # 檢查用戶權限
        user_permissions = get_user_permissions(current_user, db)
        
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您沒有權限執行此操作"
            )
        
        # 檢查資源團隊權限
        if resource_team_id:
            if not user_in_team(current_user.id, resource_team_id, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="您沒有權限訪問此資源"
                )
        
        return current_user
    
    return permission_checker

def get_user_permissions(user: User, db: Session) -> List[str]:
    """獲取用戶權限列表"""
    permissions = []
    
    # 從角色獲取權限
    for role in user.roles:
        for permission in role.permissions:
            permissions.append(permission.name)
    
    return list(set(permissions))

def user_in_team(user_id: int, team_id: int, db: Session) -> bool:
    """檢查用戶是否在團隊中"""
    team = db.query(Team).filter_by(id=team_id).first()
    if not team:
        return False
    
    return any(member.id == user_id for member in team.members)
```

**使用示例**:
```python
from app.core.permissions import check_permission, Permission

@router.get("/accounts/{id}")
async def get_account(
    id: str,
    current_user: User = Depends(check_permission(Permission.ACCOUNT_READ)),
    db: Session = Depends(get_db)
):
    ...
```

---

### 2.2 實時通知系統（2 週）

#### 2.2.1 通知服務

**文件**: `admin-backend/app/services/notification.py` (新建)

```python
"""
通知服務
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import requests
from app.core.config import get_settings

settings = get_settings()

class NotificationService:
    """通知服務"""
    
    def __init__(self):
        self.email_enabled = settings.email_enabled
        self.webhook_enabled = settings.webhook_enabled
    
    async def send_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ):
        """發送郵件"""
        if not self.email_enabled:
            return
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.email_from
        msg['To'] = ', '.join(recipients)
        
        msg.attach(MIMEText(body, 'plain'))
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))
        
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        except Exception as e:
            logger.error(f"發送郵件失敗: {e}")
    
    async def send_webhook(self, url: str, payload: dict):
        """發送 Webhook"""
        if not self.webhook_enabled:
            return
        
        try:
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"發送 Webhook 失敗: {e}")
    
    async def send_alert_notification(
        self,
        alert: dict,
        recipients: List[str]
    ):
        """發送告警通知"""
        subject = f"【告警】{alert['title']}"
        body = f"""
告警詳情：
標題：{alert['title']}
級別：{alert['level']}
描述：{alert['description']}
時間：{alert['created_at']}
        """
        
        # 發送郵件
        await self.send_email(recipients, subject, body)
        
        # 發送 Webhook
        if settings.webhook_url:
            await self.send_webhook(settings.webhook_url, {
                "type": "alert",
                "data": alert
            })
```

#### 2.2.2 瀏覽器推送通知

**文件**: `saas-demo/src/hooks/useNotifications.ts` (新建)

```typescript
import { useEffect, useState } from 'react';

export function useNotifications() {
  const [permission, setPermission] = useState<NotificationPermission>('default');

  useEffect(() => {
    if ('Notification' in window) {
      setPermission(Notification.permission);
    }
  }, []);

  const requestPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      const result = await Notification.requestPermission();
      setPermission(result);
      return result === 'granted';
    }
    return permission === 'granted';
  };

  const showNotification = (title: string, options?: NotificationOptions) => {
    if (permission === 'granted') {
      new Notification(title, {
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        ...options,
      });
    }
  };

  return {
    permission,
    requestPermission,
    showNotification,
  };
}
```

---

### 2.3 批量操作功能（2 週）

#### 2.3.1 批量操作 API

**文件**: `admin-backend/app/api/group_ai/accounts.py`

```python
@router.post("/accounts/batch-update")
async def batch_update_accounts(
    request: BatchUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新賬號"""
    account_ids = request.account_ids
    updates = request.updates
    
    # 驗證權限
    accounts = db.query(GroupAIAccount).filter(
        GroupAIAccount.id.in_(account_ids)
    ).all()
    
    if len(accounts) != len(account_ids):
        raise HTTPException(400, "部分賬號不存在")
    
    # 批量更新
    updated_count = 0
    errors = []
    
    for account in accounts:
        try:
            for key, value in updates.items():
                setattr(account, key, value)
            account.updated_at = datetime.utcnow()
            updated_count += 1
        except Exception as e:
            errors.append({
                "account_id": account.id,
                "error": str(e)
            })
    
    db.commit()
    
    # 記錄操作日誌
    log_operation(
        user_id=current_user.id,
        action="batch_update",
        resource_type="account",
        details={"count": updated_count, "errors": errors}
    )
    
    return {
        "success": True,
        "updated_count": updated_count,
        "errors": errors
    }
```

---

## 第三階段：新功能開發（3-6 個月）

### 3.1 協作與團隊管理（6-8 週）

詳細實施方案見獨立文檔：`docs/TEAM_COLLABORATION_FEATURE.md`

### 3.2 智能分析系統（8-10 週）

詳細實施方案見獨立文檔：`docs/INTELLIGENT_ANALYSIS_FEATURE.md`

---

## 測試策略

### 單元測試

**文件**: `admin-backend/tests/test_db_optimization.py` (新建)

```python
import pytest
from app.db import engine
from sqlalchemy import text

def test_connection_pool():
    """測試連接池"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1

def test_pool_size():
    """測試連接池大小"""
    pool = engine.pool
    assert pool.size() <= 10
```

### 性能測試

**文件**: `admin-backend/tests/performance/test_api_performance.py` (新建)

```python
import pytest
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_response_time():
    """測試 API 響應時間"""
    start = time.time()
    response = client.get("/api/v1/group-ai/accounts")
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 0.5  # 500ms
```

### 集成測試

**文件**: `admin-backend/tests/integration/test_account_flow.py` (新建)

```python
def test_account_lifecycle():
    """測試賬號完整生命週期"""
    # 創建
    # 啟動
    # 更新
    # 停止
    # 刪除
    pass
```

---

## 部署方案

### 數據庫遷移

```bash
# 1. 備份數據庫
cp admin.db admin.db.backup

# 2. 執行遷移
cd admin-backend
poetry run alembic upgrade head

# 3. 驗證遷移
poetry run alembic current
```

### 零停機部署

1. **藍綠部署**
   - 部署新版本到綠色環境
   - 驗證通過後切換流量
   - 保留藍色環境作為回滾

2. **數據庫遷移策略**
   - 向後兼容的遷移
   - 分階段遷移
   - 數據驗證

---

## 風險管理

### 風險識別

1. **數據庫遷移風險**
   - 風險：數據丟失
   - 緩解：完整備份、測試環境驗證

2. **性能回退風險**
   - 風險：優化後性能變差
   - 緩解：性能基準測試、逐步發布

3. **兼容性風險**
   - 風險：API 變更影響現有客戶端
   - 緩解：版本控制、向後兼容

### 回滾方案

1. **代碼回滾**
   ```bash
   git revert <commit>
   docker-compose up -d --build
   ```

2. **數據庫回滾**
   ```bash
   poetry run alembic downgrade -1
   ```

---

## 時間表與里程碑

### 第一階段（1-2 個月）

- **第 1-2 週**: 數據庫優化
- **第 3-4 週**: API 性能優化
- **第 5 週**: 內存優化
- **第 6-7 週**: 前端性能優化
- **第 8 週**: 錯誤處理改進、測試

### 第二階段（2-4 個月）

- **第 9-11 週**: 權限管理系統
- **第 12-13 週**: 實時通知系統
- **第 14-15 週**: 批量操作功能
- **第 16 週**: 用戶體驗優化、測試

### 第三階段（3-6 個月）

- **第 17-24 週**: 協作與團隊管理
- **第 25-32 週**: 智能分析系統

---

## 總結

本升級方案涵蓋了：

1. **性能優化**：數據庫、API、前端全面優化
2. **功能完善**：權限管理、通知系統、批量操作
3. **新功能開發**：團隊協作、智能分析

**預期成果**：
- 性能提升 50-70%
- 穩定性提升 80%
- 功能完整性提升至 95%
- 用戶體驗提升 60-80%

**下一步行動**：
1. 審查並批准方案
2. 分配開發資源
3. 開始第一階段實施

---

**文檔結束**

