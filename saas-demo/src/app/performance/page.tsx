"use client";

export const dynamic = 'force-dynamic';

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { RefreshCw, TrendingUp, TrendingDown, Clock, AlertTriangle, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";
import { fetchWithAuth } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";

interface PerformanceStats {
  request_count: number;
  total_response_time: number;
  average_response_time: number;
  slow_requests: Array<{
    path: string;
    method: string;
    response_time?: number;
    response_time_ms?: number;
    timestamp?: string;
  }>;
  requests_by_endpoint: Record<string, {
    count: number;
    total_time: number;
    average_time: number;
    max_time: number;
    min_time: number;
  }>;
  requests_by_status: Record<string, number>;
}

async function fetchPerformanceStats(): Promise<PerformanceStats> {
  const apiBase = getApiBaseUrl();
  const response = await fetchWithAuth(`${apiBase}/system/performance`);
  
  if (!response.ok) {
    throw new Error("获取性能数据失败");
  }
  
  return response.json();
}

export default function PerformancePage() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState<PerformanceStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadData = async () => {
    try {
      setError(null);
      const data = await fetchPerformanceStats();
      setStats(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "加载失败";
      setError(message);
      toast({
        title: "加载失败",
        description: message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        setRefreshing(true);
        loadData();
      }, 30000); // 每30秒刷新（優化：減少 CPU 負載）
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-destructive">加载失败</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={handleRefresh}>重试</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const avgResponseTime = stats?.average_response_time || 0;
  const slowRequestsCount = stats?.slow_requests?.length || 0;
  const totalRequests = stats?.request_count || 0;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 页面标题和操作 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">性能监控</h1>
          <p className="text-muted-foreground mt-1">
            实时监控 API 性能和响应时间
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

      {/* 概览指标 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>总请求数</CardDescription>
            <CardTitle className="text-3xl">{totalRequests.toLocaleString()}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center text-sm text-muted-foreground">
              <Clock className="w-4 h-4 mr-1" />
              所有 API 请求
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>平均响应时间</CardDescription>
            <CardTitle className="text-3xl">
              {avgResponseTime.toFixed(0)}ms
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center text-sm">
              {avgResponseTime < 200 ? (
                <>
                  <CheckCircle2 className="w-4 h-4 mr-1 text-green-500" />
                  <span className="text-green-500">优秀</span>
                </>
              ) : avgResponseTime < 500 ? (
                <>
                  <AlertTriangle className="w-4 h-4 mr-1 text-yellow-500" />
                  <span className="text-yellow-500">良好</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 mr-1 text-red-500" />
                  <span className="text-red-500">需要优化</span>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>慢请求数</CardDescription>
            <CardTitle className="text-3xl">{slowRequestsCount}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center text-sm text-muted-foreground">
              <AlertTriangle className="w-4 h-4 mr-1" />
              响应时间 &gt; 1000ms
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 详细数据 */}
      <Tabs defaultValue="endpoints" className="space-y-4">
        <TabsList>
          <TabsTrigger value="endpoints">端点性能</TabsTrigger>
          <TabsTrigger value="slow">慢请求</TabsTrigger>
          <TabsTrigger value="status">状态码统计</TabsTrigger>
        </TabsList>

        <TabsContent value="endpoints" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>端点性能统计</CardTitle>
              <CardDescription>按端点分组的性能指标</CardDescription>
            </CardHeader>
            <CardContent>
              {stats?.requests_by_endpoint ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>端点</TableHead>
                      <TableHead>请求数</TableHead>
                      <TableHead>平均响应时间</TableHead>
                      <TableHead>最大响应时间</TableHead>
                      <TableHead>最小响应时间</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(stats.requests_by_endpoint)
                      .sort((a, b) => b[1].average_time - a[1].average_time)
                      .map(([endpoint, data]) => (
                        <TableRow key={endpoint}>
                          <TableCell className="font-mono text-sm">{endpoint}</TableCell>
                          <TableCell>{data.count}</TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                data.average_time < 200 ? "default" :
                                data.average_time < 500 ? "secondary" : "destructive"
                              }
                            >
                              {data.average_time.toFixed(0)}ms
                            </Badge>
                          </TableCell>
                          <TableCell>{data.max_time.toFixed(0)}ms</TableCell>
                          <TableCell>{data.min_time.toFixed(0)}ms</TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-muted-foreground text-center py-8">暂无数据</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="slow" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>慢请求列表</CardTitle>
              <CardDescription>响应时间超过 1000ms 的请求</CardDescription>
            </CardHeader>
            <CardContent>
              {stats?.slow_requests && stats.slow_requests.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>时间</TableHead>
                      <TableHead>方法</TableHead>
                      <TableHead>路径</TableHead>
                      <TableHead>响应时间</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {stats.slow_requests.map((req, idx) => (
                      <TableRow key={idx}>
                        <TableCell className="text-sm">
                          {req.timestamp ? new Date(req.timestamp).toLocaleString() : "未知"}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{req.method}</Badge>
                        </TableCell>
                        <TableCell className="font-mono text-sm">{req.path}</TableCell>
                        <TableCell>
                          <Badge variant="destructive">
                            {(req.response_time || req.response_time_ms || 0).toFixed(0)}ms
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8">
                  <CheckCircle2 className="w-12 h-12 mx-auto text-green-500 mb-2" />
                  <p className="text-muted-foreground">暂无慢请求</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="status" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>HTTP 状态码统计</CardTitle>
              <CardDescription>按状态码分组的请求数</CardDescription>
            </CardHeader>
            <CardContent>
              {stats?.requests_by_status ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(stats.requests_by_status)
                    .sort((a, b) => parseInt(b[0]) - parseInt(a[0]))
                    .map(([status, count]) => (
                      <div key={status} className="text-center p-4 border rounded-lg">
                        <div className="text-2xl font-bold">{count}</div>
                        <div className="text-sm text-muted-foreground">
                          <Badge
                            variant={
                              status.startsWith("2") ? "default" :
                              status.startsWith("4") ? "secondary" :
                              status.startsWith("5") ? "destructive" : "outline"
                            }
                          >
                            {status}
                          </Badge>
                        </div>
                      </div>
                    ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-center py-8">暂无数据</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

