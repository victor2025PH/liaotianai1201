/**
 * 統一的 API 客戶端
 * - 5 秒超時自動 fallback 到 mock 數據
 * - 統一的錯誤處理和 toast 提示
 */

import { toast } from "@/hooks/use-toast";
import { getAuthHeaders } from "@/lib/api/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
const API_TIMEOUT = 30000; // 30 秒超時（增加超时时间以处理较慢的API响应）

// 導入 mock 數據
import { mockSessions, mockSessionDetail } from "@/mock/sessions";
import { mockLogs } from "@/mock/logs";
import { mockSystemStats } from "@/mock/stats";

// Mock 數據生成器
const mockData: Record<string, any> = {
  dashboard: {
    stats: {
      today_sessions: 0,
      sessions_change: "0%",
      success_rate: 0.0,
      success_rate_change: "0%",
      token_usage: 0,
      token_usage_change: "0%",
      error_count: 0,
      error_count_change: "0%",
      avg_response_time: 0.0,
      response_time_change: "0%",
      active_users: 0,
      active_users_change: "0%",
    },
    recent_sessions: [],
    recent_errors: [],
  },
  metrics: {
    response_time: {
      data_points: Array.from({ length: 24 }, (_, i) => ({
        hour: i,
        timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
        avg_response_time: 1.0 + Math.random() * 0.5,
      })),
      average: 1.23,
      min: 0.8,
      max: 1.8,
      trend: "-5%",
    },
    system_status: {
      status_items: [
        { label: "API 服務器", status: "正常", value: "運行中", description: "所有服務正常運行" },
        { label: "數據庫", status: "正常", value: "已連接", description: "連接穩定" },
        { label: "Redis", status: "正常", value: "已連接", description: "緩存正常" },
      ],
      last_updated: new Date().toISOString(),
    },
  },
  logs: {
    items: mockLogs,
    total: mockLogs.length,
    page: 1,
    page_size: 20,
  },
  sessions: {
    items: mockSessions,
    total: mockSessions.length,
    page: 1,
    page_size: 20,
  },
  "sessions/": (id: string) => mockSessionDetail[id] || mockSessionDetail["session-001"],
  "settings/alerts": {
    error_rate_threshold: 5.0,
    max_response_time: 2000,
    notification_method: "email",
    email_recipients: "admin@example.com",
    webhook_url: "",
    webhook_enabled: false,
  },
  "system/monitor": mockSystemStats,
};

/**
 * 從端點路徑獲取 mock 數據鍵
 */
function getMockKey(endpoint: string): string {
  // 移除前綴 /api/v1 和查詢參數
  let path = endpoint.replace(/^\/api\/v1\//, "").split("?")[0];
  
  // 處理帶 ID 的路徑（如 /sessions/123 -> sessions/123）
  // 保持 sessions/ 前綴以便識別
  if (path.match(/^sessions\/[^/]+$/)) {
    return path; // 保持 sessions/{id} 格式
  }
  
  return path;
}

/**
 * 獲取 mock 數據
 */
function getMockData<T>(endpoint: string): T {
  const key = getMockKey(endpoint);
  
  // 處理帶 ID 的路徑（如 /sessions/{id}）
  if (key.startsWith("sessions/") && key !== "sessions") {
    const sessionId = key.replace("sessions/", "");
    const mock = mockSessionDetail[sessionId] || mockSessionDetail["session-001"];
    if (mock) {
      return JSON.parse(JSON.stringify(mock)) as T;
    }
  }
  
  const mock = mockData[key];
  
  if (!mock) {
    console.warn(`[API Client] No mock data for ${key}, returning empty object`);
    return {} as T;
  }
  
  // 深拷貝避免修改原始數據
  return JSON.parse(JSON.stringify(mock)) as T;
}

/**
 * API 響應結果類型
 * 統一的 API 返回結構，確保所有接口都有一致的錯誤處理
 */
export interface ApiResult<T> {
  /** 請求是否成功 */
  ok: boolean;
  /** 響應數據（成功時） */
  data?: T;
  /** 錯誤信息（失敗時） */
  error?: {
    /** 錯誤消息 */
    message: string;
    /** 錯誤代碼（如 CLIENT_ERROR, SERVER_ERROR, NETWORK_ERROR） */
    code?: string;
    /** HTTP 狀態碼 */
    status?: number;
  };
  /** 是否使用 mock 數據 */
  _isMock?: boolean;
}

/**
 * 統一的 API 請求函數
 * - 5 秒超時
 * - 自動 fallback 到 mock 數據
 * - 統一的錯誤處理和 toast
 * - 網絡錯誤或 5xx 時返回帶 error 字段的結果
 * - 4xx 錯誤用 toast 提示
 */
export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit & {
    showErrorToast?: boolean;
    showSuccessToast?: boolean;
    successMessage?: string;
  }
): Promise<ApiResult<T>> {
  const {
    showErrorToast = true,
    showSuccessToast = false,
    successMessage,
    ...fetchOptions
  } = options || {};

  const url = `${API_BASE_URL}${endpoint}`;
  
  // 獲取認證頭
  const authHeaders = getAuthHeaders();
  
  const headers = {
    ...authHeaders,
    ...fetchOptions.headers,
  };

  // 創建超時控制器
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText);
      const errorMessage = `API 錯誤 (${response.status}): ${errorText || response.statusText}`;
      
      // 401 未授權：清除 token 並立即重定向到登入頁
      if (response.status === 401) {
        // 清除 token 並強制重定向
        if (typeof window !== "undefined") {
          const { logout } = await import("@/lib/api/auth");
          // 強制重定向到登入頁
          logout(true); // 清除 token 並重定向
        }
        return {
          ok: false,
          error: {
            message: "未授權，請重新登入",
            code: "UNAUTHORIZED",
            status: 401,
          },
        };
      }
      
      // 4xx 錯誤：參數錯誤等，用 toast 提示
      if (response.status >= 400 && response.status < 500) {
        if (showErrorToast) {
          toast({
            title: "請求參數錯誤",
            description: errorText || response.statusText,
            variant: "destructive",
          });
        }
        return {
          ok: false,
          error: {
            message: errorMessage,
            code: "CLIENT_ERROR",
            status: response.status,
          },
        };
      }
      
      // 5xx 錯誤：服務器錯誤，返回帶 error 字段的結果
      if (response.status >= 500) {
        return {
          ok: false,
          error: {
            message: errorMessage,
            code: "SERVER_ERROR",
            status: response.status,
          },
        };
      }
      
      // 其他錯誤
      return {
        ok: false,
        error: {
          message: errorMessage,
          code: "UNKNOWN_ERROR",
          status: response.status,
        },
      };
    }

    const data = await response.json();
    
    if (showSuccessToast && successMessage) {
      toast({
        title: "成功",
        description: successMessage,
      });
    }

    return { ok: true, data: data as T };
  } catch (error) {
    clearTimeout(timeoutId);
    
    // 如果是超時或網絡錯誤，不返回mock數據，而是返回錯誤
    // 這樣可以確保前端顯示真實的錯誤狀態，而不是誤導性的模擬數據
    if (
      error instanceof Error &&
      (error.name === "AbortError" ||
        error.message.includes("timeout") ||
        error.message.includes("Failed to fetch") ||
        error.message.includes("NetworkError"))
    ) {
      console.warn(`[API Client] Request timeout/error for ${endpoint}`);
      
      if (showErrorToast) {
        toast({
          title: "連接失敗",
          description: `無法連接到後端服務器，請檢查服務是否運行`,
          variant: "destructive",
        });
      }

      // 不再返回mock數據，而是返回錯誤
      return {
        ok: false,
        error: {
          message: "無法連接到後端服務器",
          code: "NETWORK_ERROR",
        },
      };
    }

    // 其他錯誤：返回帶 error 字段的結果
    const errorMessage = error instanceof Error ? error.message : "未知錯誤";
    
    if (showErrorToast) {
      toast({
        title: "請求失敗",
        description: errorMessage,
        variant: "destructive",
      });
    }

    return {
      ok: false,
      error: {
        message: errorMessage,
        code: "NETWORK_ERROR",
      },
    };
  }
}

/**
 * GET 請求
 */
export async function apiGet<T>(
  endpoint: string,
  options?: RequestInit & {
    showErrorToast?: boolean;
  }
): Promise<ApiResult<T>> {
  return apiClient<T>(endpoint, {
    ...options,
    method: "GET",
  });
}

/**
 * POST 請求
 */
export async function apiPost<T>(
  endpoint: string,
  data?: any,
  options?: RequestInit & {
    showErrorToast?: boolean;
    showSuccessToast?: boolean;
    successMessage?: string;
  }
): Promise<ApiResult<T>> {
  return apiClient<T>(endpoint, {
    ...options,
    method: "POST",
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * PUT 請求
 */
export async function apiPut<T>(
  endpoint: string,
  data?: any,
  options?: RequestInit & {
    showErrorToast?: boolean;
    showSuccessToast?: boolean;
    successMessage?: string;
  }
): Promise<ApiResult<T>> {
  return apiClient<T>(endpoint, {
    ...options,
    method: "PUT",
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * DELETE 請求
 */
export async function apiDelete<T>(
  endpoint: string,
  options?: RequestInit & {
    showErrorToast?: boolean;
    showSuccessToast?: boolean;
    successMessage?: string;
  }
): Promise<ApiResult<T>> {
  return apiClient<T>(endpoint, {
    ...options,
    method: "DELETE",
  });
}

