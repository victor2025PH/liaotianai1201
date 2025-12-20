"use client";

import { useQuery } from "@tanstack/react-query";
import { getDashboardData, type DashboardData } from "@/lib/api";

interface UseDashboardDataReturn {
  data: DashboardData | null;
  loading: boolean;
  error: Error | null;
  isMock: boolean;
  refetch: () => void;
}

export function useDashboardData(): UseDashboardDataReturn {
  const queryKey = ["dashboard"];

  const { data, isLoading, error, refetch, isFetching } = useQuery<DashboardData, Error>({
    queryKey: queryKey,
    queryFn: async () => {
      const result = await getDashboardData();
      if (!result.ok || result.error) {
        throw new Error(result.error?.message || "無法載入 Dashboard 數據");
      }
      if (!result.data) {
        throw new Error("未返回數據");
      }
      return result.data;
    },
    staleTime: 30 * 1000, // 30 秒（優化：減少 CPU 負載）
    gcTime: 10 * 60 * 1000, // 10 分鐘
    refetchInterval: 30 * 1000, // 每 30 秒自動刷新（優化：減少 CPU 負載）
    refetchOnWindowFocus: false, // 切換視窗時不自動刷新
    placeholderData: (previousData) => previousData,
    retry: 1,
    retryDelay: 1000,
  });

  // 檢查是否為 mock 數據（通過檢查數據結構或 API 響應）
  const isMock = data ? (data as any)._isMock || false : false;

  return {
    data: data || null,
    loading: isLoading || isFetching,
    error: error as Error | null,
    isMock,
    refetch,
  };
}
