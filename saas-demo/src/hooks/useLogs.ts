"use client";

import { useState } from "react";
import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import { getLogs, type LogList } from "@/lib/api";

interface UseLogsReturn {
  data: LogList | null;
  loading: boolean;
  error: Error | null;
  isMock: boolean;
  refetch: () => void;
  page: number;
  pageSize: number;
  level: "error" | "warning" | "info" | undefined;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  setLevel: (level: "error" | "warning" | "info" | undefined) => void;
}

export function useLogs(
  initialPage: number = 1,
  initialPageSize: number = 20,
  initialLevel?: "error" | "warning" | "info",
  searchQuery?: string
): UseLogsReturn {
  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [level, setLevel] = useState<"error" | "warning" | "info" | undefined>(initialLevel);

  const queryKey = ["logs", page, pageSize, level, searchQuery];
  
  const queryOptions: UseQueryOptions<LogList, Error> = {
    queryKey,
    queryFn: async () => {
      try {
        const result = await getLogs(page, pageSize, level, searchQuery);
        
        if (!result.ok || result.error) {
          // 如果有 mock 數據，使用 mock 數據
          if (result._isMock && result.data) {
            return result.data;
          }
          // API 不可用時返回空數據而不是拋出錯誤
          console.warn("日誌 API 不可用:", result.error?.message);
          return { items: [], total: 0, page: 1, page_size: pageSize };
        }
        
        if (!result.data) {
          return { items: [], total: 0, page: 1, page_size: pageSize };
        }
        
        return result.data;
      } catch (err) {
        // 網絡錯誤或其他異常時返回空數據
        console.warn("獲取日誌列表失敗:", err);
        return { items: [], total: 0, page: 1, page_size: pageSize };
      }
    },
    staleTime: 10 * 1000, // 10 秒內數據被認為是新鮮的（日誌數據更新較頻繁）
    gcTime: 2 * 60 * 1000, // 2 分鐘後未使用的數據被垃圾回收
    retry: 0, // 不重試（API 可能不存在）
    refetchOnWindowFocus: false, // 窗口聚焦時不自動重新獲取
    refetchInterval: false, // 禁用自動刷新（避免頻繁請求不存在的 API）
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
    page,
    pageSize,
    level,
    setPage,
    setPageSize,
    setLevel,
  };
}
