/**
 * SSE (Server-Sent Events) Hook
 * 用於實時更新指標數據
 */

import { useEffect, useState, useRef } from "react";

interface UseSSEOptions {
  url: string;
  enabled?: boolean;
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
}

export function useSSE<T = any>(options: UseSSEOptions) {
  const { url, enabled = true, onMessage, onError } = options;
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Event | null>(null);
  const [connected, setConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    try {
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setConnected(true);
        setError(null);
      };

      eventSource.onmessage = (event) => {
        try {
          const parsedData = JSON.parse(event.data);
          setData(parsedData);
          if (onMessage) {
            onMessage(parsedData);
          }
        } catch (err) {
          console.error("[SSE] Failed to parse message:", err);
        }
      };

      eventSource.onerror = (err) => {
        setError(err);
        setConnected(false);
        if (onError) {
          onError(err);
        }
        // 如果連接失敗，關閉 EventSource
        eventSource.close();
      };

      return () => {
        eventSource.close();
        eventSourceRef.current = null;
      };
    } catch (err) {
      console.error("[SSE] Failed to create EventSource:", err);
      setError(err as Event);
    }
  }, [url, enabled, onMessage, onError]);

  const reconnect = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setError(null);
    setConnected(false);
    // 觸發重新連接
    setData(null);
  };

  return {
    data,
    error,
    connected,
    reconnect,
  };
}

