"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { QueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { WebSocketProvider } from "@/hooks/useWebSocket";

export function Providers({ children }: { children: React.ReactNode }) {
  // 在客戶端創建 QueryClient 實例，避免序列化問題
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30 * 1000, // 30 秒內數據被認為是新鮮的
            gcTime: 5 * 60 * 1000, // 5 分鐘後未使用的數據被垃圾回收
            refetchOnWindowFocus: false, // 窗口聚焦時不自動重新獲取
            retry: 1, // 失敗時重試 1 次
            retryDelay: (attemptIndex) =>
              Math.min(1000 * 2 ** attemptIndex, 30000), // 指數退避
          },
          mutations: {
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <WebSocketProvider>
        {children}
      </WebSocketProvider>
    </QueryClientProvider>
  );
}

