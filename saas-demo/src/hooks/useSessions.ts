"use client";

import { useState } from "react";
import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import { getSessions, type SessionList } from "@/lib/api";

interface UseSessionsReturn {
  data: SessionList | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
  page: number;
  pageSize: number;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
}

export function useSessions(
  initialPage: number = 1,
  initialPageSize: number = 20
): UseSessionsReturn {
  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);

  const queryKey = ["sessions", page, pageSize];
  
  const queryOptions: UseQueryOptions<SessionList, Error> = {
    queryKey,
    queryFn: async () => {
      const result = await getSessions(page, pageSize);
      
      if (result.error) {
        throw new Error(result.error.message || "無法載入會話列表");
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

  return {
    data: data ?? null,
    loading: isLoading || isFetching,
    error: error ?? null,
    refetch: () => {
      refetch();
    },
    page,
    pageSize,
    setPage,
    setPageSize,
  };
}
