import { useQuery } from "@tanstack/react-query";
import { getSystemMonitor, SystemMonitorData } from "@/lib/api";

export function useSystemMonitor() {
  const queryKey = ["systemMonitor"];

  const { data, isLoading, error, refetch, isFetching } = useQuery<SystemMonitorData, Error>({
    queryKey: queryKey,
    queryFn: async () => {
      const result = await getSystemMonitor();
      if (!result.ok || result.error) {
        throw new Error(result.error?.message || "無法載入系統監控數據");
      }
      if (!result.data) {
        throw new Error("未返回數據");
      }
      return result.data;
    },
    staleTime: 30 * 1000, // 30 秒
    gcTime: 5 * 60 * 1000, // 5 分鐘
    refetchInterval: 30 * 1000, // 每 30 秒自動刷新
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
    refetch 
  };
}
