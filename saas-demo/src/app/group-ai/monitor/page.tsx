"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Activity, TrendingUp, AlertCircle, Users, RefreshCw, CheckCircle2 } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import {
  getSystemMetrics,
  getAccountMetrics,
  getAlerts,
  resolveAlert,
  getSystemMetricsHistory,
  getSystemStatistics,
  type SystemMetrics,
  type AccountMetrics,
  type Alert as AlertType,
  type MetricsHistoryData,
  type MetricsStatistics,
} from "@/lib/api/group-ai"
import { MetricsChart } from "@/components/monitor/metrics-chart"
import { PermissionGuard } from "@/components/permissions/permission-guard"

export default function GroupAIMonitorPage() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null)
  const [accountMetrics, setAccountMetrics] = useState<AccountMetrics[]>([])
  const [alerts, setAlerts] = useState<AlertType[]>([])
  const [metricsHistory, setMetricsHistory] = useState<MetricsHistoryData | null>(null)
  const [statistics, setStatistics] = useState<MetricsStatistics | null>(null)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [selectedMetricType, setSelectedMetricType] = useState<"messages" | "replies" | "errors" | "redpackets">("messages")
  const [selectedPeriod, setSelectedPeriod] = useState<"1h" | "24h" | "7d" | "30d">("24h")

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [system, accounts, alertsData] = await Promise.all([
        getSystemMetrics(),
        getAccountMetrics(),
        getAlerts(20, undefined, false), // 獲取最近 20 個未解決的告警
      ])
      
      setSystemMetrics(system)
      setAccountMetrics(accounts)
      setAlerts(alertsData)
    } catch (err) {
      setError(err instanceof Error ? err.message : "加載失敗")
    } finally {
      setLoading(false)
    }
  }

  const fetchHistory = async (metricType: typeof selectedMetricType, period: typeof selectedPeriod) => {
    try {
      setHistoryLoading(true)
      const data = await getSystemMetricsHistory(metricType, period)
      setMetricsHistory(data)
    } catch (err) {
      toast({
        title: "加載歷史數據失敗",
        description: err instanceof Error ? err.message : "無法加載指標歷史數據",
        variant: "destructive",
      })
    } finally {
      setHistoryLoading(false)
    }
  }

  const fetchStatistics = async (period: typeof selectedPeriod) => {
    try {
      const data = await getSystemStatistics(period)
      setStatistics(data)
    } catch (err) {
      console.error("加載統計數據失敗:", err)
    }
  }

  useEffect(() => {
    fetchData()
    fetchHistory(selectedMetricType, selectedPeriod)
    fetchStatistics(selectedPeriod)
    // 每 30 秒自動刷新
    const interval = setInterval(() => {
      fetchData()
      fetchHistory(selectedMetricType, selectedPeriod)
      fetchStatistics(selectedPeriod)
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    fetchHistory(selectedMetricType, selectedPeriod)
    fetchStatistics(selectedPeriod)
  }, [selectedMetricType, selectedPeriod])

  const handleResolveAlert = async (alertId: string) => {
    try {
      await resolveAlert(alertId)
      setAlerts(alerts.filter(a => a.alert_id !== alertId))
      // 可以顯示成功提示
    } catch (err) {
      // 處理錯誤
    }
  }

  const getAlertBadgeVariant = (type: string): "default" | "destructive" => {
    switch (type) {
      case "error":
        return "destructive" as const
      case "warning":
        return "default" as const
      default:
        return "default" as const // Alert 组件只支持 "default" 和 "destructive"
    }
  }

  return (
    <PermissionGuard permission="monitor:view" fallback={
      <div className="container mx-auto py-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>您沒有權限查看監控數據</AlertDescription>
        </Alert>
      </div>
    }>
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">群組 AI 監控</h1>
            <p className="text-muted-foreground mt-2">實時監控 AI 賬號運行狀態</p>
          </div>
          <PermissionGuard permission="monitor:view">
            <Button onClick={fetchData} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              刷新
            </Button>
          </PermissionGuard>
        </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

        {/* 統計卡片 */}
        <PermissionGuard permission="monitor:statistics:view">
          {statistics && (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">回復率</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.reply_rate.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">
                總消息: {statistics.total_messages.toLocaleString()}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">錯誤率</CardTitle>
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.error_rate.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">
                總錯誤: {statistics.total_errors.toLocaleString()}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">平均回復時間</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.average_reply_time.toFixed(2)}s</div>
              <p className="text-xs text-muted-foreground">
                總回復: {statistics.total_replies.toLocaleString()}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">紅包數量</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.total_redpackets.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">
                時間範圍: {selectedPeriod}
              </p>
            </CardContent>
          </Card>
            </div>
          )}
        </PermissionGuard>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活躍賬號</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">
                {systemMetrics?.online_accounts || 0}
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              在線 / {systemMetrics?.total_accounts || 0} 總數
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總消息數</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">
                {systemMetrics?.total_messages || 0}
              </div>
            )}
            <p className="text-xs text-muted-foreground">累計消息數</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">回復數</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">
                {systemMetrics?.total_replies || 0}
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              平均回復時間: {systemMetrics?.average_reply_time.toFixed(2) || "0.00"}s
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">錯誤數</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">
                {systemMetrics?.total_errors || 0}
              </div>
            )}
            <p className="text-xs text-muted-foreground">累計錯誤數</p>
          </CardContent>
        </Card>
      </div>

        {/* 指標歷史圖表 */}
        <PermissionGuard permission="monitor:history:view">
          <MetricsChart
            data={metricsHistory?.data_points || []}
            title="系統指標趨勢"
            description={`${selectedPeriod} 內的 ${selectedMetricType === "messages" ? "消息" : selectedMetricType === "replies" ? "回復" : selectedMetricType === "errors" ? "錯誤" : "紅包"} 趨勢`}
            loading={historyLoading}
            metricType={selectedMetricType}
            period={selectedPeriod}
            chartType="area"
            onMetricTypeChange={(type) => {
              setSelectedMetricType(type)
            }}
            onPeriodChange={(period) => {
              setSelectedPeriod(period)
            }}
          />
        </PermissionGuard>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>賬號指標</CardTitle>
            <CardDescription>各賬號的運行狀態和指標</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : accountMetrics.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                暫無賬號指標
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>賬號 ID</TableHead>
                    <TableHead>消息</TableHead>
                    <TableHead>回復</TableHead>
                    <TableHead>紅包</TableHead>
                    <TableHead>錯誤</TableHead>
                    <TableHead>成功率</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {accountMetrics.map((metrics) => {
                    const total = metrics.message_count + metrics.reply_count + metrics.redpacket_count
                    const successCount = total - metrics.error_count
                    const successRate = total > 0
                      ? ((successCount / total) * 100).toFixed(1)
                      : "0.0"
                    
                    return (
                      <TableRow key={metrics.account_id}>
                        <TableCell className="font-medium">{metrics.account_id}</TableCell>
                        <TableCell>{metrics.message_count}</TableCell>
                        <TableCell>{metrics.reply_count}</TableCell>
                        <TableCell>{metrics.redpacket_count}</TableCell>
                        <TableCell>
                          <Badge variant={metrics.error_count > 0 ? "destructive" : "secondary"}>
                            {metrics.error_count}
                          </Badge>
                        </TableCell>
                        <TableCell>{successRate}%</TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>告警列表</CardTitle>
            <CardDescription>最近的系統告警</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : alerts.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <CheckCircle2 className="h-12 w-12 mx-auto mb-2 text-green-500" />
                <p>暫無告警</p>
              </div>
            ) : (
              <div className="space-y-2">
                {alerts.map((alert) => (
                  <Alert key={alert.alert_id} variant={getAlertBadgeVariant(alert.alert_type)}>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription className="flex items-center justify-between">
                      <span>{alert.message}</span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleResolveAlert(alert.alert_id)}
                      >
                        解決
                      </Button>
                    </AlertDescription>
                  </Alert>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        </div>
      </div>
    </PermissionGuard>
  )
}

