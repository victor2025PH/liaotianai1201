/**
 * 實時指標更新 Hook
 * 使用 React Query 進行數據獲取和緩存
 */

import { useQuery } from "@tanstack/react-query";
import { getMetrics, MetricsData } from "@/lib/api";

interface UseRealtimeMetricsOptions {
  interval?: number; // 輪詢間隔（毫秒）
  enabled?: boolean;
}

export function useRealtimeMetrics(options: UseRealtimeMetricsOptions = {}) {
  const { interval = 10000, enabled = true } = options; // 默認改為 10 秒
  const queryKey = ["realtimeMetrics"];

  const { data, isLoading, error, refetch, isFetching } = useQuery<MetricsData, Error>({
    queryKey: queryKey,
    queryFn: async () => {
      const result = await getMetrics();
      if (!result.ok || result.error) {
        throw new Error(result.error?.message || "無法載入指標數據");
      }
      if (!result.data) {
        throw new Error("未返回數據");
      }
      return result.data;
    },
    staleTime: 10 * 1000, // 10 秒（與輪詢間隔一致）
    gcTime: 2 * 60 * 1000, // 2 分鐘
    refetchInterval: enabled ? interval : false, // 根據 enabled 決定是否輪詢
    enabled, // 根據 enabled 決定是否啟用查詢
    placeholderData: (previousData) => previousData,
    retry: 1,
    retryDelay: 1000,
  });

  // 檢查是否為 mock 數據
  const isMock = data ? (data as any)._isMock || false : false;

  return {
    data: data || null,
    loading: isLoading || isFetching,
    error: error as Error | null,
    isMock,
    refetch,
  };
}
