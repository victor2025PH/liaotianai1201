"use client";

import { useQuery } from "@tanstack/react-query";
import { getSessionDetail, type SessionDetail } from "@/lib/api";

interface UseSessionDetailReturn {
  data: SessionDetail | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useSessionDetail(id: string): UseSessionDetailReturn {
  const queryKey = ["sessionDetail", id];

  const { data, isLoading, error, refetch, isFetching } = useQuery<SessionDetail, Error>({
    queryKey: queryKey,
    queryFn: async () => {
      if (!id) {
        throw new Error("會話 ID 不能為空");
      }
      const result = await getSessionDetail(id);
      if (result.error) {
        throw new Error(result.error.message || "無法載入會話詳情");
      }
      if (!result.data) {
        throw new Error("未返回數據");
      }
      return result.data;
    },
    enabled: !!id, // 只有當 id 存在時才執行查詢
    staleTime: 60 * 1000, // 60 秒
    gcTime: 5 * 60 * 1000, // 5 分鐘
    placeholderData: (previousData) => previousData,
    retry: 1,
    retryDelay: 1000,
  });

  return {
    data: data || null,
    loading: isLoading || isFetching,
    error: error as Error | null,
    refetch,
  };
}
