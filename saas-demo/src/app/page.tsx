"use client";

import { useRouter } from "next/navigation";
import { memo, useState, useEffect, useCallback, useMemo, Suspense } from "react";
import dynamic from "next/dynamic";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  MessageSquare,
  TrendingUp,
  AlertCircle,
  Clock,
  Zap,
  Users,
  RefreshCw,
  Eye,
  ArrowRight,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useDashboardData } from "@/hooks/useDashboardData";
import { ErrorBoundary } from "@/components/error-boundary";
import { getSessions, getSessionDetail, SessionDetail } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";

// 懶加載圖表組件（非首屏關鍵）
const ResponseTimeChart = dynamic(
  () => import("@/components/dashboard/response-time-chart").then(m => ({ default: m.ResponseTimeChart })),
  { 
    ssr: false,
    loading: () => <Card className="h-[300px] animate-pulse bg-muted" />
  }
);

const SystemStatus = dynamic(
  () => import("@/components/dashboard/system-status").then(m => ({ default: m.SystemStatus })),
  { 
    ssr: false,
    loading: () => <Card className="h-[200px] animate-pulse bg-muted" />
  }
);

export default function Dashboard() {
  const router = useRouter();
  const { t, language } = useI18n();
  const { data, loading, error, isMock: isMockDashboard, refetch } = useDashboardData();
  const [recentSessions, setRecentSessions] = useState<any[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState<SessionDetail | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [isUsingMockSessions, setIsUsingMockSessions] = useState(false);

  // 獲取最近會話（防禦式邏輯，避免 undefined 報錯）
  useEffect(() => {
    const fetchRecentSessions = async () => {
      try {
        setSessionsLoading(true);
        setIsUsingMockSessions(false);
        const result = await getSessions(1, 10);
        
        if (!result.ok || result.error) {
          if (result._isMock && result.data && Array.isArray(result.data.items)) {
            setRecentSessions(result.data.items.slice(0, 10));
            setIsUsingMockSessions(true);
          } else {
            if (data?.recent_sessions && Array.isArray(data.recent_sessions)) {
              setRecentSessions(data.recent_sessions);
            } else {
              setRecentSessions([]);
            }
          }
        } else if (result.data && Array.isArray(result.data.items)) {
          setRecentSessions(result.data.items.slice(0, 10));
          setIsUsingMockSessions(result._isMock || false);
        } else {
          setRecentSessions([]);
        }
      } catch (err) {
        console.error("Failed to fetch recent sessions:", err);
        setIsUsingMockSessions(true);
        if (data?.recent_sessions && Array.isArray(data.recent_sessions)) {
          setRecentSessions(data.recent_sessions);
        } else {
          setRecentSessions([]);
        }
      } finally {
        setSessionsLoading(false);
      }
    };
    
    if (!loading) {
      fetchRecentSessions();
    }
  }, [loading, data]);

  const handleCardClick = (type: string, params?: Record<string, string>) => {
    if (type === "sessions") {
      const query = new URLSearchParams(params).toString();
      router.push(`/sessions${query ? `?${query}` : ""}`);
    } else if (type === "logs") {
      const query = new URLSearchParams(params).toString();
      router.push(`/logs${query ? `?${query}` : ""}`);
    }
  };

  const handleViewSessionDetail = async (sessionId: string) => {
    setDetailLoading(true);
    setIsDetailOpen(true);
    try {
      const result = await getSessionDetail(sessionId);
      
      if (result.error) {
        const session = recentSessions.find((s) => s.id === sessionId);
        if (session) {
          setSelectedSession({
            ...session,
            messages: [],
          } as SessionDetail);
        }
      } else if (result.data) {
        setSelectedSession(result.data);
      }
    } catch (err) {
      console.error("Failed to load session detail:", err);
      const session = recentSessions.find((s) => s.id === sessionId);
      if (session) {
        setSelectedSession({
          ...session,
          messages: [],
        } as SessionDetail);
      }
    } finally {
      setDetailLoading(false);
    }
  };

  // 获取状态文本
  const getStatusText = (status: string) => {
    if (status === "completed") return t.common.completed;
    if (status === "active") return t.common.active;
    return t.common.failed;
  };

  // 获取严重度文本
  const getSeverityText = (severity: string) => {
    if (severity === "high") return language === "en" ? "High" : language === "zh-TW" ? "高" : "高";
    if (severity === "medium") return language === "en" ? "Medium" : language === "zh-TW" ? "中" : "中";
    return language === "en" ? "Low" : language === "zh-TW" ? "低" : "低";
  };

  if (loading) {
    return (
      <div className="flex-1 space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-9 w-64" />
            <Skeleton className="h-5 w-96" />
          </div>
          <Skeleton className="h-8 w-24" />
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

  if (error && !isMockDashboard) {
    return (
      <div className="flex-1 space-y-6 p-6">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">{t.common.error}</CardTitle>
            <CardDescription>
              {error.message || (language === "en" ? "Unable to connect to backend server" : language === "zh-TW" ? "無法連接到後端伺服器" : "无法连接到后端服务器")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={refetch} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              {language === "en" ? "Retry" : language === "zh-TW" ? "重試" : "重试"}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data || !data.stats) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardHeader>
            <CardTitle>{t.common.loading}</CardTitle>
            <CardDescription>{language === "en" ? "Loading dashboard data" : language === "zh-TW" ? "正在獲取儀表板數據" : "正在获取仪表板数据"}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  const stats = [
    {
      label: t.dashboard.todaySessions,
      value: (data.stats?.today_sessions || 0).toLocaleString(),
      change: data.stats?.sessions_change || "0%",
      icon: MessageSquare,
      trend: (data.stats?.sessions_change || "0%").startsWith("+") ? "up" : "down",
    },
    {
      label: t.dashboard.successRate,
      value: `${((data.stats?.success_rate || 0)).toFixed(1)}%`,
      change: data.stats?.success_rate_change || "0%",
      icon: TrendingUp,
      trend: (data.stats?.success_rate_change || "0%").startsWith("+") ? "up" : "down",
    },
    {
      label: t.dashboard.tokenUsage,
      value: `${((data.stats?.token_usage || 0) / 1000000).toFixed(1)}M`,
      change: data.stats?.token_usage_change || "0%",
      icon: Zap,
      trend: (data.stats?.token_usage_change || "0%").startsWith("+") ? "up" : "down",
    },
    {
      label: t.dashboard.errorCount,
      value: (data.stats?.error_count || 0).toString(),
      change: data.stats?.error_count_change || "0%",
      icon: AlertCircle,
      trend: (data.stats?.error_count_change || "0%").startsWith("-") ? "down" : "up",
    },
    {
      label: t.dashboard.avgResponseTime,
      value: `${((data.stats?.avg_response_time || 0)).toFixed(1)}s`,
      change: data.stats?.response_time_change || "0%",
      icon: Clock,
      trend: (data.stats?.response_time_change || "0%").startsWith("-") ? "down" : "up",
    },
    {
      label: t.dashboard.activeUsers,
      value: (data.stats?.active_users || 0).toLocaleString(),
      change: data.stats?.active_users_change || "0%",
      icon: Users,
      trend: (data.stats?.active_users_change || "0%").startsWith("+") ? "up" : "down",
    },
  ];

  return (
    <div className="flex-1 space-y-6 p-6">
      {/* 頂部標題和環境標識 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            {t.dashboard.title}
          </h1>
          <p className="text-muted-foreground mt-2">
            {t.dashboard.subtitle}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="px-3 py-1">
            {t.header.production}
          </Badge>
          <Button variant="ghost" size="icon" onClick={refetch}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* 操作引導卡片 */}
      <Alert className="border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-950/30">
        <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
        <AlertTitle className="text-blue-900 dark:text-blue-100">{t.dashboard.quickGuide}</AlertTitle>
        <AlertDescription className="mt-2 space-y-3">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            {t.dashboard.quickGuideDesc}
          </p>
          <div className="grid gap-2 md:grid-cols-5">
            <Link 
              href="/group-ai/scripts"
              className="flex items-center gap-2 rounded-lg border border-blue-200 bg-white p-3 transition-all hover:border-blue-400 hover:shadow-sm dark:border-blue-800 dark:bg-blue-950/50 dark:hover:border-blue-600"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                ①
              </div>
              <div className="flex-1">
                <div className="text-xs font-semibold text-blue-900 dark:text-blue-100">{t.nav.scriptManagement}</div>
                <div className="text-xs text-blue-600 dark:text-blue-400">{t.scripts.createScript}</div>
              </div>
              <ArrowRight className="h-4 w-4 text-blue-400" />
            </Link>
            <Link 
              href="/group-ai/accounts"
              className="flex items-center gap-2 rounded-lg border border-blue-200 bg-white p-3 transition-all hover:border-blue-400 hover:shadow-sm dark:border-blue-800 dark:bg-blue-950/50 dark:hover:border-blue-600"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                ②
              </div>
              <div className="flex-1">
                <div className="text-xs font-semibold text-blue-900 dark:text-blue-100">{t.nav.accountManagement}</div>
                <div className="text-xs text-blue-600 dark:text-blue-400">{t.accounts.addAccount}</div>
              </div>
              <ArrowRight className="h-4 w-4 text-blue-400" />
            </Link>
            <Link 
              href="/group-ai/role-assignments"
              className="flex items-center gap-2 rounded-lg border border-blue-200 bg-white p-3 transition-all hover:border-blue-400 hover:shadow-sm dark:border-blue-800 dark:bg-blue-950/50 dark:hover:border-blue-600"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-100 text-sm font-bold text-green-700 dark:bg-green-900 dark:text-green-300">
                ③
              </div>
              <div className="flex-1">
                <div className="text-xs font-semibold text-blue-900 dark:text-blue-100">{t.nav.roleAssignment}</div>
                <div className="text-xs text-blue-600 dark:text-blue-400">{t.nav.optional}</div>
              </div>
              <ArrowRight className="h-4 w-4 text-blue-400" />
            </Link>
            <Link 
              href="/group-ai/role-assignment-schemes"
              className="flex items-center gap-2 rounded-lg border border-blue-200 bg-white p-3 transition-all hover:border-blue-400 hover:shadow-sm dark:border-blue-800 dark:bg-blue-950/50 dark:hover:border-blue-600"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-100 text-sm font-bold text-green-700 dark:bg-green-900 dark:text-green-300">
                ④
              </div>
              <div className="flex-1">
                <div className="text-xs font-semibold text-blue-900 dark:text-blue-100">{t.nav.allocationScheme}</div>
                <div className="text-xs text-blue-600 dark:text-blue-400">{t.nav.optional}</div>
              </div>
              <ArrowRight className="h-4 w-4 text-blue-400" />
            </Link>
            <Link 
              href="/group-ai/automation-tasks"
              className="flex items-center gap-2 rounded-lg border border-blue-200 bg-white p-3 transition-all hover:border-blue-400 hover:shadow-sm dark:border-blue-800 dark:bg-blue-950/50 dark:hover:border-blue-600"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-100 text-sm font-bold text-green-700 dark:bg-green-900 dark:text-green-300">
                ⑤
              </div>
              <div className="flex-1">
                <div className="text-xs font-semibold text-blue-900 dark:text-blue-100">{t.nav.automationTasks}</div>
                <div className="text-xs text-blue-600 dark:text-blue-400">{t.nav.optional}</div>
              </div>
            </Link>
          </div>
          <p className="text-xs text-blue-700 dark:text-blue-300">
            💡 <strong>{t.dashboard.importantNote}：</strong>{t.dashboard.mustComplete} ① {t.nav.scriptManagement} {t.dashboard.and} ② {t.nav.accountManagement}{t.dashboard.thenStart} {t.dashboard.checkScript}
          </p>
        </AlertDescription>
      </Alert>

      {/* 統計卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {stats.map((stat) => {
          const isClickable =
            stat.label === t.dashboard.todaySessions ||
            stat.label === t.dashboard.errorCount ||
            stat.label === t.dashboard.avgResponseTime;
          const clickHandler = () => {
            if (stat.label === t.dashboard.todaySessions) {
              handleCardClick("sessions", { range: "24h" });
            } else if (stat.label === t.dashboard.errorCount) {
              handleCardClick("logs", { level: "error", range: "24h" });
            } else if (stat.label === t.dashboard.avgResponseTime) {
              handleCardClick("sessions", { sort: "response_time" });
            }
          };

          return (
            <Card
              key={stat.label}
              className={cn(
                "border-border/70 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-lg",
                isClickable && "cursor-pointer hover:border-primary/50"
              )}
              onClick={isClickable ? clickHandler : undefined}
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.label}
                </CardTitle>
                <stat.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline justify-between">
                  <p className="text-2xl font-semibold">{stat.value}</p>
                  <Badge
                    variant={stat.trend === "up" ? "default" : "secondary"}
                    className={cn(
                      "text-xs font-medium",
                      stat.trend === "down" && "text-emerald-600 dark:text-emerald-400"
                    )}
                  >
                    {stat.change}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* 響應時間趨勢圖 */}
      <ErrorBoundary>
        <ResponseTimeChart />
      </ErrorBoundary>

      {/* 最近會話、錯誤列表和系統狀態 */}
      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        {/* 最近會話列表 */}
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle>{t.dashboard.recentSessions}</CardTitle>
            <CardDescription>
              {language === "en" ? "View latest session records and status" : language === "zh-TW" ? "查看最新的會話記錄和處理狀態" : "查看最新的会话记录和处理状态"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t.sessions.sessionId}</TableHead>
                  <TableHead>{t.sessions.user}</TableHead>
                  <TableHead>{t.sessions.messageCount}</TableHead>
                  <TableHead>{t.common.status}</TableHead>
                  <TableHead>{t.sessions.duration}</TableHead>
                  <TableHead className="text-right">{t.common.createdAt}</TableHead>
                  <TableHead className="w-16">{t.common.actions}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sessionsLoading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  </TableRow>
                ) : recentSessions.length > 0 ? (
                  recentSessions.map((session) => (
                    <TableRow
                      key={session.id}
                      className="hover:bg-muted/50"
                    >
                      <TableCell className="font-mono text-xs">
                        {session.id}
                      </TableCell>
                      <TableCell className="text-sm">{session.user}</TableCell>
                      <TableCell>{session.messages}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            session.status === "completed"
                              ? "default"
                              : session.status === "active"
                              ? "secondary"
                              : "destructive"
                          }
                          className="text-xs"
                        >
                          {getStatusText(session.status)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {session.duration}
                      </TableCell>
                      <TableCell className="text-right text-xs text-muted-foreground">
                        {new Date(session.started_at || session.timestamp).toLocaleString(language === "en" ? "en-US" : language === "zh-TW" ? "zh-TW" : "zh-CN")}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleViewSessionDetail(session.id);
                          }}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      {t.sessions.noSessions}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* 右側：錯誤列表和系統狀態 */}
        <div className="space-y-6">
          {/* 最近錯誤/警告 */}
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>{t.dashboard.recentErrors}</CardTitle>
              <CardDescription>
                {language === "en" ? "System exceptions and events requiring attention" : language === "zh-TW" ? "系統異常和需要關注的事件" : "系统异常和需要关注的事件"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Array.isArray(data.recent_errors) && data.recent_errors.length > 0 ? (
                  data.recent_errors.map((error) => (
                    <div
                      key={error.id}
                      className="flex items-start justify-between gap-2 rounded-lg border border-border/60 bg-card p-3 text-sm transition hover:border-primary/40"
                    >
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={
                              error.severity === "high"
                                ? "destructive"
                                : error.severity === "medium"
                                ? "default"
                                : "secondary"
                            }
                            className="text-xs"
                          >
                            {getSeverityText(error.severity)}
                          </Badge>
                          <span className="text-xs font-medium text-foreground">
                            {error.type}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground line-clamp-1">
                          {error.message}
                        </p>
                      </div>
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {error.timestamp}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-4 text-sm text-muted-foreground">
                    {t.logs.noLogs}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 系統狀態 */}
          <ErrorBoundary>
            <SystemStatus />
          </ErrorBoundary>
        </div>
      </div>

      {/* 會話詳情 Dialog */}
      <Dialog open={isDetailOpen} onOpenChange={setIsDetailOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>{t.common.details}</DialogTitle>
            <DialogDescription>
              {language === "en" ? "View complete session information and message records" : language === "zh-TW" ? "查看完整的會話資訊和訊息記錄" : "查看完整的会话信息和消息记录"}
            </DialogDescription>
          </DialogHeader>
          {detailLoading ? (
            <div className="flex items-center justify-center py-8">
              <Skeleton className="h-8 w-32" />
            </div>
          ) : selectedSession ? (
            <ScrollArea className="max-h-[60vh] pr-4">
              <div className="space-y-4">
                <div className="grid gap-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">{t.sessions.sessionId}</span>
                    <span className="text-sm font-mono">{selectedSession.id}</span>
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">{t.sessions.user}</span>
                    <span className="text-sm">{selectedSession.user}</span>
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">{t.common.status}</span>
                    <Badge
                      variant={
                        selectedSession.status === "completed"
                          ? "default"
                          : selectedSession.status === "active"
                          ? "secondary"
                          : "destructive"
                      }
                    >
                      {getStatusText(selectedSession.status)}
                    </Badge>
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">{t.sessions.duration}</span>
                    <span className="text-sm">{selectedSession.duration}</span>
                  </div>
                  {selectedSession.token_usage && (
                    <>
                      <Separator />
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-muted-foreground">{t.sessions.tokenUsage}</span>
                        <span className="text-sm">{selectedSession.token_usage.toLocaleString()}</span>
                      </div>
                    </>
                  )}
                  {selectedSession.model && (
                    <>
                      <Separator />
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-muted-foreground">{t.sessions.model}</span>
                        <span className="text-sm">{selectedSession.model}</span>
                      </div>
                    </>
                  )}
                  {selectedSession.error_message && (
                    <>
                      <Separator />
                      <div className="space-y-2">
                        <span className="text-sm font-medium text-muted-foreground">{t.common.error}</span>
                        <p className="text-sm text-destructive bg-destructive/10 p-2 rounded">
                          {selectedSession.error_message}
                        </p>
                      </div>
                    </>
                  )}
                  <Separator />
                  <div className="space-y-2">
                    <span className="text-sm font-medium text-muted-foreground">{language === "en" ? "Messages" : language === "zh-TW" ? "訊息記錄" : "消息记录"}</span>
                    {selectedSession.messages && selectedSession.messages.length > 0 ? (
                      <div className="space-y-2">
                        {selectedSession.messages.map((msg) => (
                          <div
                            key={msg.id}
                            className={`p-3 rounded-lg ${
                              msg.role === "user"
                                ? "bg-primary/10 border border-primary/20"
                                : "bg-muted border border-border"
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <Badge variant={msg.role === "user" ? "default" : "secondary"}>
                                {msg.role === "user" ? (language === "en" ? "User" : language === "zh-TW" ? "使用者" : "用户") : msg.role === "assistant" ? (language === "en" ? "Assistant" : language === "zh-TW" ? "助手" : "助手") : (language === "en" ? "System" : language === "zh-TW" ? "系統" : "系统")}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {new Date(msg.timestamp).toLocaleString(language === "en" ? "en-US" : language === "zh-TW" ? "zh-TW" : "zh-CN")}
                              </span>
                            </div>
                            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">{t.common.noData}</p>
                    )}
                  </div>
                </div>
              </div>
            </ScrollArea>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
