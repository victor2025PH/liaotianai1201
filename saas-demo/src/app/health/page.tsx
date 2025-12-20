"use client";

export const dynamic = 'force-dynamic';

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { RefreshCw, CheckCircle2, AlertCircle, XCircle, HelpCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { getHealthCheck, ComponentHealth, HealthCheckResponse } from "@/lib/api/health";
import { ErrorBoundary } from "@/components/error-boundary";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

// 状态图标映射
const statusIcons = {
  healthy: CheckCircle2,
  degraded: AlertCircle,
  unhealthy: XCircle,
  unknown: HelpCircle,
};

// 状态颜色映射
const statusColors = {
  healthy: "bg-green-500",
  degraded: "bg-yellow-500",
  unhealthy: "bg-red-500",
  unknown: "bg-gray-500",
};

// 状态文本颜色映射
const statusTextColors = {
  healthy: "text-green-600",
  degraded: "text-yellow-600",
  unhealthy: "text-red-600",
  unknown: "text-gray-600",
};

// 状态标签颜色映射
const statusBadgeColors = {
  healthy: "bg-green-100 text-green-800 border-green-200",
  degraded: "bg-yellow-100 text-yellow-800 border-yellow-200",
  unhealthy: "bg-red-100 text-red-800 border-red-200",
  unknown: "bg-gray-100 text-gray-800 border-gray-200",
};

function ComponentCard({ component }: { component: ComponentHealth }) {
  const Icon = statusIcons[component.status] || HelpCircle;
  const badgeColor = statusBadgeColors[component.status] || statusBadgeColors.unknown;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold capitalize">
            {component.name.replace(/_/g, " ")}
          </CardTitle>
          <Badge className={cn("border", badgeColor)}>
            <Icon className="w-3 h-3 mr-1" />
            {component.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {component.message && (
            <p className="text-sm text-muted-foreground">{component.message}</p>
          )}
          
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            {component.response_time_ms !== undefined && (
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                <span>{component.response_time_ms.toFixed(2)} ms</span>
              </div>
            )}
            {component.timestamp && (
              <div className="flex items-center gap-1">
                <span>{new Date(component.timestamp).toLocaleTimeString()}</span>
              </div>
            )}
          </div>

          {component.details && Object.keys(component.details).length > 0 && (
            <div className="mt-3 pt-3 border-t">
              <p className="text-xs font-medium text-muted-foreground mb-2">详细信息:</p>
              <div className="space-y-1">
                {Object.entries(component.details).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-xs">
                    <span className="text-muted-foreground capitalize">
                      {key.replace(/_/g, " ")}:
                    </span>
                    <span className="font-medium">
                      {typeof value === "object" ? JSON.stringify(value) : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function HealthCheckPage() {
  const [healthData, setHealthData] = useState<HealthCheckResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  const fetchHealthData = async () => {
    try {
      setError(null);
      const data = await getHealthCheck(true);
      setHealthData(data);
    } catch (err: any) {
      setError(err.message || "获取健康检查数据失败");
      console.error("Health check error:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHealthData();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        setRefreshing(true);
        fetchHealthData();
      }, 30000); // 每30秒自动刷新（優化：減少 CPU 負載）
      setRefreshInterval(interval);
      return () => {
        if (interval) clearInterval(interval);
      };
    } else {
      if (refreshInterval) {
        clearInterval(refreshInterval);
        setRefreshInterval(null);
      }
    }
  }, [autoRefresh]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchHealthData();
  };

          const overallStatus = healthData?.status || "unknown";
          const OverallIcon = statusIcons[overallStatus] || HelpCircle;
          const overallBadgeColor = statusBadgeColors[overallStatus] || statusBadgeColors.unknown;

  // 按状态分组组件
  const componentsByStatus = healthData?.components.reduce(
    (acc, component) => {
      if (!acc[component.status]) {
        acc[component.status] = [];
      }
      acc[component.status].push(component);
      return acc;
    },
    {} as Record<string, ComponentHealth[]>
  ) || {};

  return (
    <ErrorBoundary>
      <div className="container mx-auto p-6 space-y-6">
        {/* 页面标题和操作 */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">系统健康检查</h1>
            <p className="text-muted-foreground mt-1">
              实时监控系统各组件的健康状态
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              {autoRefresh ? "停止自动刷新" : "启用自动刷新"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={cn("w-4 h-4 mr-2", refreshing && "animate-spin")} />
              刷新
            </Button>
          </div>
        </div>

        {/* 错误提示 */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>错误</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* 整体状态概览 */}
        {loading ? (
          <Card>
            <CardContent className="pt-6">
              <Skeleton className="h-32" />
            </CardContent>
          </Card>
        ) : healthData ? (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>整体状态</CardTitle>
                  <CardDescription>
                    最后更新: {new Date(healthData.timestamp).toLocaleString()}
                  </CardDescription>
                </div>
                <Badge className={cn("border text-lg px-4 py-2", overallBadgeColor)}>
                  <OverallIcon className="w-5 h-5 mr-2" />
                  {overallStatus.toUpperCase()}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {healthData.summary?.healthy ?? componentsByStatus.healthy?.length ?? 0}
                  </div>
                  <div className="text-sm text-muted-foreground">健康</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">
                    {healthData.summary?.degraded ?? componentsByStatus.degraded?.length ?? 0}
                  </div>
                  <div className="text-sm text-muted-foreground">降级</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {healthData.summary?.unhealthy ?? componentsByStatus.unhealthy?.length ?? 0}
                  </div>
                  <div className="text-sm text-muted-foreground">异常</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-600">
                    {healthData.summary?.unknown ?? componentsByStatus.unknown?.length ?? 0}
                  </div>
                  <div className="text-sm text-muted-foreground">未知</div>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : null}

        {/* 组件详情 */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Card key={i}>
                <CardContent className="pt-6">
                  <Skeleton className="h-32" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : healthData ? (
          <div className="space-y-6">
            {/* 按状态分组显示 */}
            {(["unhealthy", "degraded", "unknown", "healthy"] as const).map((status) => {
              const components = componentsByStatus[status] || [];
              if (components.length === 0) return null;

              return (
                <div key={status} className="space-y-4">
                  <h2 className="text-xl font-semibold capitalize flex items-center gap-2">
                    <span className={cn("w-2 h-2 rounded-full", statusColors[status])} />
                    {status === "healthy" ? "健康组件" : status === "degraded" ? "降级组件" : status === "unhealthy" ? "异常组件" : "未知状态组件"}
                    <Badge variant="outline">{components.length}</Badge>
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {components.map((component) => (
                      <ComponentCard key={component.name} component={component} />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        ) : null}
      </div>
    </ErrorBoundary>
  );
}

