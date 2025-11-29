"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useRealtimeMetrics } from "@/hooks/useRealtimeMetrics";
import { cn } from "@/lib/utils";

const iconMap: Record<string, any> = {
  "API Key 状态": "🔑",
  "模型状态": "💻",
  "系統健康度": "❤️",
};

export function SystemStatus() {
  const { data, loading, error, isMock } = useRealtimeMetrics({ interval: 10000 });

  if (loading) {
    return (
      <Card className="shadow-sm">
        <CardHeader>
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-64 mt-2" />
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card className="shadow-sm border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">加载失败</CardTitle>
          <CardDescription>{error?.message || "无法加载系統状态数据"}</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // 防禦式邏輯：確保数据結構完整
  const systemStatusData = data?.system_status;
  const statusItems = Array.isArray(systemStatusData?.status_items) 
    ? systemStatusData.status_items 
    : [];
  const lastUpdated = systemStatusData?.last_updated 
    ? new Date(systemStatusData.last_updated) 
    : new Date();

  // 如果沒有状态項，顯示空状态
  if (statusItems.length === 0) {
    return (
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>系統状态</CardTitle>
          <CardDescription>实时监控關鍵服務和配置状态</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">暫時无法獲取系統状态数据</p>
            <p className="text-xs mt-1">請稍後重試</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>系統状态</CardTitle>
        <CardDescription>实时监控關鍵服務和配置状态</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {statusItems.map((item) => (
          <div
            key={item.label}
            className="flex items-center justify-between rounded-lg border border-border/60 bg-card p-4 transition hover:border-primary/40"
          >
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  "rounded-full p-2",
                  item.status === "active" || item.status === "healthy"
                    ? "bg-emerald-100 dark:bg-emerald-900/30"
                    : "bg-destructive/10"
                )}
              >
                {item.status === "active" || item.status === "healthy" ? (
                  <CheckCircle2
                    className={cn(
                      "h-4 w-4",
                      item.status === "active" || item.status === "healthy"
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-destructive"
                    )}
                  />
                ) : (
                  <XCircle className="h-4 w-4 text-destructive" />
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{iconMap[item.label] || "📊"}</span>
                  <span className="text-sm font-medium text-foreground">
                    {item.label}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {item.description}
                </p>
              </div>
            </div>
            <Badge
              variant={
                item.status === "active" || item.status === "healthy"
                  ? "default"
                  : "destructive"
              }
              className="text-xs"
            >
              {item.value}
            </Badge>
          </div>
        ))}
        <div className="rounded-lg border border-border/60 bg-muted/30 p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">最后更新</span>
            </div>
            <span className="text-xs font-medium text-foreground">
              {lastUpdated.toLocaleTimeString("zh-TW", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

