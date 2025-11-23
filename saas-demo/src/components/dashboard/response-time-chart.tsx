"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingDown, TrendingUp, RefreshCw } from "lucide-react";
import { useRealtimeMetrics } from "@/hooks/useRealtimeMetrics";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info } from "lucide-react";

export function ResponseTimeChart() {
  const { data, loading, error, isMock, refetch } = useRealtimeMetrics({ interval: 10000 });

  if (loading) {
    return (
      <Card className="shadow-sm">
        <CardHeader>
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-64 mt-2" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[200px] w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card className="shadow-sm border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">載入失敗</CardTitle>
          <CardDescription>{error?.message || "無法載入響應時間數據"}</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // 檢查數據結構是否完整
  if (!data.response_time || !data.response_time.data_points || data.response_time.data_points.length === 0) {
    return (
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>響應時間趨勢</CardTitle>
          <CardDescription>過去 24 小時平均響應時間變化</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[200px] text-muted-foreground">
            暫無數據
          </div>
        </CardContent>
      </Card>
    );
  }

  const responseTimeData = data.response_time.data_points;
  const maxTime = data.response_time.max ?? 0;
  const minTime = data.response_time.min ?? 0;
  const avgTime = data.response_time.average ?? 0;
  const trend = data.response_time.trend ?? "0%";
  const isPositiveTrend = trend.startsWith("-");
  return (
    <>
      {/* Mock 數據提示 */}
      {isMock && (
        <Alert className="border-amber-500/50 bg-amber-500/10 mb-4">
          <Info className="h-4 w-4 text-amber-600 dark:text-amber-400" />
          <AlertDescription className="text-amber-600 dark:text-amber-400">
            當前展示的是模擬數據。後端服務器不可用，已自動切換到模擬數據模式。
          </AlertDescription>
        </Alert>
      )}
      <Card className="shadow-sm">
        <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>響應時間趨勢</CardTitle>
            <CardDescription>過去 24 小時平均響應時間變化（每 10 秒自動更新）</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => refetch()} disabled={loading}>
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            </Button>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
            {isPositiveTrend ? (
              <>
                <TrendingDown className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span className="text-emerald-600 dark:text-emerald-400">{trend}</span>
              </>
            ) : (
              <>
                <TrendingUp className="h-4 w-4 text-destructive" />
                <span className="text-destructive">{trend}</span>
              </>
            )}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[200px] w-full">
          <svg
            viewBox="0 0 800 200"
            className="h-full w-full"
            preserveAspectRatio="none"
          >
            {/* 背景網格 */}
            <defs>
              <pattern
                id="grid"
                width="33.33"
                height="50"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M 33.33 0 L 0 0 0 50"
                  fill="none"
                  stroke="hsl(var(--border))"
                  strokeWidth="0.5"
                  opacity="0.3"
                />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />

            {/* 區域填充 */}
            {responseTimeData.length > 0 && (
              <path
                d={`M 0,${200 - ((responseTimeData[0]?.avg_response_time - minTime) / (maxTime - minTime || 1)) * 180} ${responseTimeData
                  .map(
                    (d, i) =>
                      `L ${(i / (Math.max(responseTimeData.length - 1, 1))) * 800},${200 - ((d.avg_response_time - minTime) / (maxTime - minTime || 1)) * 180}`
                  )
                  .join(" ")} L 800,200 L 0,200 Z`}
                fill="url(#gradient)"
                opacity="0.2"
              />
            )}

            {/* 漸變定義 */}
            <defs>
              <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0.3" />
                <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0" />
              </linearGradient>
            </defs>

            {/* 折線 */}
            {responseTimeData.length > 0 && (
              <path
                d={`M ${responseTimeData
                  .map(
                    (d, i) =>
                      `${(i / (Math.max(responseTimeData.length - 1, 1))) * 800},${200 - ((d.avg_response_time - minTime) / (maxTime - minTime || 1)) * 180}`
                  )
                  .join(" L ")}`}
                fill="none"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}

            {/* 數據點 */}
            {responseTimeData.map((d, i) => (
              <circle
                key={i}
                cx={(i / (Math.max(responseTimeData.length - 1, 1))) * 800}
                cy={200 - ((d.avg_response_time - minTime) / (maxTime - minTime || 1)) * 180}
                r="3"
                fill="hsl(var(--primary))"
                className="hover:r-4 transition-all"
              />
            ))}
          </svg>
        </div>
        <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
          <span>00:00</span>
          <span>06:00</span>
          <span>12:00</span>
          <span>18:00</span>
          <span>24:00</span>
        </div>
        <div className="mt-2 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-primary" />
            <span className="text-muted-foreground">平均: {avgTime.toFixed(2)}s</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-emerald-500" />
            <span className="text-muted-foreground">最低: {minTime.toFixed(2)}s</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-destructive" />
            <span className="text-muted-foreground">最高: {maxTime.toFixed(2)}s</span>
          </div>
        </div>
      </CardContent>
    </Card>
    </>
  );
}

