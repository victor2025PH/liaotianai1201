/**
 * 簡單的 API 緩存機制
 * 用於減少重複請求，提高頁面載入速度
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

class APICache {
  private cache: Map<string, CacheEntry<unknown>> = new Map();
  private pendingRequests: Map<string, Promise<unknown>> = new Map();

  /**
   * 獲取緩存數據或執行請求
   * @param key 緩存鍵
   * @param fetcher 數據獲取函數
   * @param ttl 緩存時間（毫秒），默認 30 秒
   */
  async get<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number = 30000
  ): Promise<T> {
    const now = Date.now();
    const cached = this.cache.get(key) as CacheEntry<T> | undefined;

    // 如果緩存有效，直接返回
    if (cached && cached.expiresAt > now) {
      return cached.data;
    }

    // 如果有相同的請求正在進行，等待它完成
    const pending = this.pendingRequests.get(key);
    if (pending) {
      return pending as Promise<T>;
    }

    // 執行請求
    const promise = fetcher().then((data) => {
      this.cache.set(key, {
        data,
        timestamp: now,
        expiresAt: now + ttl,
      });
      this.pendingRequests.delete(key);
      return data;
    }).catch((error) => {
      this.pendingRequests.delete(key);
      throw error;
    });

    this.pendingRequests.set(key, promise);
    return promise;
  }

  /**
   * 使緩存失效
   */
  invalidate(key: string) {
    this.cache.delete(key);
  }

  /**
   * 使所有緩存失效
   */
  invalidateAll() {
    this.cache.clear();
  }

  /**
   * 使匹配前綴的緩存失效
   */
  invalidateByPrefix(prefix: string) {
    for (const key of this.cache.keys()) {
      if (key.startsWith(prefix)) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * 預載數據
   */
  prefetch<T>(key: string, fetcher: () => Promise<T>, ttl: number = 30000) {
    this.get(key, fetcher, ttl).catch(() => {
      // 預載失敗時靜默處理
    });
  }
}

// 單例導出
export const apiCache = new APICache();

// 常用緩存鍵
export const CACHE_KEYS = {
  DASHBOARD: 'dashboard',
  WORKERS: 'workers',
  SESSIONS: (page: number) => `sessions:${page}`,
  ACCOUNTS: 'accounts',
  SCRIPTS: 'scripts',
  NOTIFICATIONS: 'notifications',
} as const;

// 緩存時間常量
export const CACHE_TTL = {
  SHORT: 10 * 1000,      // 10 秒
  MEDIUM: 30 * 1000,     // 30 秒
  LONG: 60 * 1000,       // 1 分鐘
  VERY_LONG: 5 * 60 * 1000, // 5 分鐘
} as const;

