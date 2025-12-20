"use client";

import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import { getMetrics, MetricsData } from "@/lib/api";

interface UseMetricsReturn {
  data: MetricsData | null;
  loading: boolean;
  error: Error | null;
  isMock: boolean;
  refetch: () => void;
}

export function useMetrics(): UseMetricsReturn {
  const queryKey = ["metrics"];
  
  const queryOptions: UseQueryOptions<MetricsData, Error> = {
    queryKey,
    queryFn: async () => {
      const result = await getMetrics();
      
      if (result.error) {
        // 如果有 mock 數據，使用 mock 數據
        if (result._isMock && result.data) {
          return result.data;
        }
        throw new Error(result.error.message || "無法載入指標數據");
      }
      
      if (!result.data) {
        throw new Error("未返回數據");
      }
      
      return result.data;
    },
    staleTime: 30 * 1000, // 30 秒內數據被認為是新鮮的（指標數據更新較頻繁）
    gcTime: 2 * 60 * 1000, // 2 分鐘後未使用的數據被垃圾回收
    retry: 1, // 失敗時重試 1 次
    refetchOnWindowFocus: false, // 窗口聚焦時不自動重新獲取
    refetchInterval: 30 * 1000, // 每 30 秒自動刷新一次（優化：減少 CPU 負載）
  };

  const { data, isLoading, error, refetch, isFetching } = useQuery(queryOptions);
  
  // 獲取 mock 狀態
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
