"use client";

import { useSystemMonitor } from "@/hooks/useSystemMonitor";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Activity,
  Cpu,
  HardDrive,
  Network,
  RefreshCw,
  Server,
  CheckCircle2,
  AlertCircle,
  XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info } from "lucide-react";
import { useState, useEffect } from "react";
import { PermissionGuard } from "@/components/permissions/permission-guard";

export default function MonitoringPage() {
  const { data, loading, error, isMock, refetch } = useSystemMonitor();

  if (loading) {
    return (
      <div className="flex-1 space-y-6 p-6">
        <div className="space-y-2">
          <Skeleton className="h-9 w-48" />
          <Skeleton className="h-5 w-96" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-32" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error && !isMock) {
    return (
      <div className="flex-1 space-y-6 p-6">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">載入失敗</CardTitle>
            <CardDescription>
              {error.message || "無法連接到後端服務器，請檢查後端服務是否正在運行"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => refetch()} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              重試
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // 防禦式邏輯：確保數據結構完整
  if (!data) {
    return (
      <div className="flex-1 space-y-6 p-6">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">無法載入數據</CardTitle>
            <CardDescription>
              暫時無法獲取系統監控數據，請稍後重試
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => refetch()} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              重試
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // 安全地提取數據，使用默認值
  const health = data.health || {
    status: "unknown",
    uptime_seconds: 0,
    version: "unknown",
    timestamp: new Date().toISOString(),
  };

  const metrics = data.metrics || {
    cpu_usage_percent: 0,
    memory_usage_percent: 0,
    disk_usage_percent: 0,
    active_connections: 0,
    queue_length: 0,
    timestamp: new Date().toISOString(),
  };

  const services = data.services || {};

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (days > 0) {
      return `${days} 天 ${hours} 小時`;
    } else if (hours > 0) {
      return `${hours} 小時 ${minutes} 分鐘`;
    } else {
      return `${minutes} 分鐘`;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case "healthy":
      case "running":
      case "connected":
        return <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />;
      case "degraded":
      case "warning":
        return <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400" />;
      default:
        return <XCircle className="h-4 w-4 text-destructive" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "healthy":
      case "running":
      case "connected":
        return <Badge variant="default">正常</Badge>;
      case "degraded":
        return <Badge variant="default">降級</Badge>;
      default:
        return <Badge variant="destructive">異常</Badge>;
    }
  };

  return (
    <PermissionGuard permission="monitor:view" fallback={
      <div className="flex-1 space-y-6 p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>您沒有權限查看系統監控</AlertDescription>
        </Alert>
      </div>
    }>
      <div className="flex-1 space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              系統監控
            </h1>
            <p className="text-muted-foreground mt-2">
              實時監控系統健康狀態和資源使用情況
            </p>
          </div>
          <PermissionGuard permission="monitor:view">
            <Button variant="outline" onClick={() => refetch()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              刷新
            </Button>
          </PermissionGuard>
        </div>

      {/* Mock 數據提示 */}
      {isMock && (
        <Alert className="border-amber-500/50 bg-amber-500/10">
          <Info className="h-4 w-4 text-amber-600 dark:text-amber-400" />
          <AlertDescription className="text-amber-600 dark:text-amber-400">
            當前使用模擬監控數據。後端服務器不可用，已自動切換到模擬數據模式。
          </AlertDescription>
        </Alert>
      )}

      {/* 系統健康狀態 */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            系統健康狀態
          </CardTitle>
          <CardDescription>
            最後更新: {new Date(health.timestamp).toLocaleString("zh-TW")}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="flex items-center justify-between rounded-lg border border-border/60 bg-card p-4">
              <div className="flex items-center gap-3">
                {getStatusIcon(health.status)}
                <div>
                  <p className="text-sm font-medium">系統狀態</p>
                  <p className="text-xs text-muted-foreground">整體健康度</p>
                </div>
              </div>
              {getStatusBadge(health.status)}
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border/60 bg-card p-4">
              <div className="flex items-center gap-3">
                <Server className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">運行時間</p>
                  <p className="text-xs text-muted-foreground">服務持續運行</p>
                </div>
              </div>
              <span className="text-sm font-semibold">
                {formatUptime(health.uptime_seconds)}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border/60 bg-card p-4">
              <div className="flex items-center gap-3">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">版本</p>
                  <p className="text-xs text-muted-foreground">當前版本號</p>
                </div>
              </div>
              <Badge variant="outline">{health.version}</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 資源使用情況 */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            資源使用情況
          </CardTitle>
          <CardDescription>
            最後更新: {new Date(metrics.timestamp).toLocaleString("zh-TW")}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">CPU 使用率</span>
                </div>
                <span className="text-sm font-semibold">
                  {metrics.cpu_usage_percent.toFixed(1)}%
                </span>
              </div>
              <Progress 
                value={metrics.cpu_usage_percent} 
                className={cn(
                  "h-2",
                  metrics.cpu_usage_percent > 80 ? "bg-destructive" : 
                  metrics.cpu_usage_percent > 60 ? "bg-amber-500" : "bg-emerald-500"
                )}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <HardDrive className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">內存使用率</span>
                </div>
                <span className="text-sm font-semibold">
                  {metrics.memory_usage_percent.toFixed(1)}%
                </span>
              </div>
              <Progress 
                value={metrics.memory_usage_percent} 
                className={cn(
                  "h-2",
                  metrics.memory_usage_percent > 80 ? "bg-destructive" : 
                  metrics.memory_usage_percent > 60 ? "bg-amber-500" : "bg-emerald-500"
                )}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <HardDrive className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">磁盤使用率</span>
                </div>
                <span className="text-sm font-semibold">
                  {metrics.disk_usage_percent.toFixed(1)}%
                </span>
              </div>
              <Progress 
                value={metrics.disk_usage_percent} 
                className={cn(
                  "h-2",
                  metrics.disk_usage_percent > 80 ? "bg-destructive" : 
                  metrics.disk_usage_percent > 60 ? "bg-amber-500" : "bg-emerald-500"
                )}
              />
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border/60 bg-card p-4">
              <div className="flex items-center gap-2">
                <Network className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">活躍連接數</span>
              </div>
              <span className="text-sm font-semibold">
                {metrics.active_connections}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border/60 bg-card p-4">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">隊列長度</span>
              </div>
              <span className="text-sm font-semibold">
                {metrics.queue_length}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 服務狀態 */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            服務狀態
          </CardTitle>
          <CardDescription>各個服務組件的運行狀態</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3">
            {Object.keys(services).length > 0 ? (
              Object.entries(services).map(([serviceName, serviceData]: [string, any]) => (
              <div
                key={serviceName}
                className="flex items-center justify-between rounded-lg border border-border/60 bg-card p-4"
              >
                <div className="flex items-center gap-3">
                  {getStatusIcon(serviceData.status)}
                  <div>
                    <p className="text-sm font-medium capitalize">
                      {serviceName.replace("_", " ")}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {serviceData.status === "running" && serviceData.uptime
                        ? `運行時間: ${formatUptime(serviceData.uptime)}`
                        : serviceData.status === "connected" && serviceData.response_time_ms
                        ? `響應時間: ${serviceData.response_time_ms}ms`
                        : serviceData.active_sessions
                        ? `活躍會話: ${serviceData.active_sessions}`
                        : ""}
                    </p>
                  </div>
                </div>
                {getStatusBadge(serviceData.status)}
              </div>
            ))
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Server className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">暫無服務狀態數據</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      </div>
    </PermissionGuard>
  );
}

