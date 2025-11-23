"use client";

import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import { getSessionsWithFilters, SessionList } from "@/lib/api";

interface UseSessionsWithFiltersParams {
  page: number;
  pageSize: number;
  q?: string;
  range?: string;
  startDate?: string;
  endDate?: string;
}

interface UseSessionsWithFiltersReturn {
  data: SessionList | null;
  loading: boolean;
  error: Error | null;
  isMock: boolean;
  refetch: () => void;
}

export function useSessionsWithFilters(
  page: number,
  pageSize: number,
  q?: string,
  range?: string,
  startDate?: string,
  endDate?: string
): UseSessionsWithFiltersReturn {
  const queryKey = ["sessions", "filtered", page, pageSize, q, range, startDate, endDate];
  
  const queryOptions: UseQueryOptions<SessionList, Error> = {
    queryKey,
    queryFn: async () => {
      const result = await getSessionsWithFilters(page, pageSize, q, range, startDate, endDate);
      
      if (!result.ok || result.error) {
        // 如果有 mock 數據，使用 mock 數據
        if (result._isMock && result.data) {
          return result.data;
        }
        throw new Error(result.error?.message || "無法載入會話列表");
      }
      
      if (!result.data) {
        throw new Error("未返回數據");
      }
      
      return result.data;
    },
    staleTime: 30 * 1000, // 30 秒內數據被認為是新鮮的
    gcTime: 5 * 60 * 1000, // 5 分鐘後未使用的數據被垃圾回收
    retry: 1, // 失敗時重試 1 次
    refetchOnWindowFocus: false, // 窗口聚焦時不自動重新獲取
  };

  const { data, isLoading, error, refetch, isFetching } = useQuery(queryOptions);
  
  // 獲取 mock 狀態（需要從 API 調用結果中提取）
  // 由於 React Query 不直接支持自定義元數據，我們需要通過其他方式獲取
  // 這裡簡化處理，實際使用時可以通過 context 或其他方式傳遞
  const isMock = false; // TODO: 從 API 響應中提取 mock 狀態

  return {
    data: data ?? null,
    loading: isLoading || isFetching,
    error: error ?? null,
    isMock,
    refetch: () => {
      refetch();
    },
  };
}
