"use client";

import { useRouter } from "next/navigation";
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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ResponseTimeChart } from "@/components/dashboard/response-time-chart";
import { SystemStatus } from "@/components/dashboard/system-status";
import { useDashboardData } from "@/hooks/useDashboardData";
import { ErrorBoundary } from "@/components/error-boundary";
import { getSessions, getSessionDetail, SessionDetail } from "@/lib/api";
import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Eye, BookOpen, UserPlus, UserCog, Settings as SettingsIcon, ArrowRight, Info } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import Link from "next/link";

export default function Dashboard() {
  const router = useRouter();
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
          // 如果有 mock 數據，使用 mock 數據
          if (result._isMock && result.data && Array.isArray(result.data.items)) {
            setRecentSessions(result.data.items.slice(0, 10));
            setIsUsingMockSessions(true);
          } else {
            // 使用 dashboard 數據作為 fallback
            if (data?.recent_sessions && Array.isArray(data.recent_sessions)) {
              setRecentSessions(data.recent_sessions);
            } else {
              setRecentSessions([]);
            }
          }
        } else if (result.data && Array.isArray(result.data.items)) {
          // 確保 items 是數組後再 slice
          setRecentSessions(result.data.items.slice(0, 10));
          setIsUsingMockSessions(result._isMock || false);
        } else {
          // 數據結構異常，使用空數組
          setRecentSessions([]);
        }
      } catch (err) {
        console.error("Failed to fetch recent sessions:", err);
        setIsUsingMockSessions(true);
        // 使用 dashboard 數據作為 fallback
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
        // 如果失敗，至少顯示基本信息
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
      // 如果失敗，至少顯示基本信息
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
            <CardTitle className="text-destructive">載入失敗</CardTitle>
            <CardDescription>
              {error.message || "無法連接到後端服務器，請檢查後端服務是否正在運行"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={refetch} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              重試
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
            <CardTitle>數據載入中...</CardTitle>
            <CardDescription>正在獲取儀表板數據</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  const stats = [
    {
      label: "今日會話量",
      value: (data.stats?.today_sessions || 0).toLocaleString(),
      change: data.stats?.sessions_change || "0%",
      icon: MessageSquare,
      trend: (data.stats?.sessions_change || "0%").startsWith("+") ? "up" : "down",
    },
    {
      label: "成功率",
      value: `${((data.stats?.success_rate || 0)).toFixed(1)}%`,
      change: data.stats?.success_rate_change || "0%",
      icon: TrendingUp,
      trend: (data.stats?.success_rate_change || "0%").startsWith("+") ? "up" : "down",
    },
    {
      label: "Token 用量",
      value: `${((data.stats?.token_usage || 0) / 1000000).toFixed(1)}M`,
      change: data.stats?.token_usage_change || "0%",
      icon: Zap,
      trend: (data.stats?.token_usage_change || "0%").startsWith("+") ? "up" : "down",
    },
    {
      label: "錯誤數",
      value: (data.stats?.error_count || 0).toString(),
      change: data.stats?.error_count_change || "0%",
      icon: AlertCircle,
      trend: (data.stats?.error_count_change || "0%").startsWith("-") ? "down" : "up",
    },
    {
      label: "平均響應時間",
      value: `${((data.stats?.avg_response_time || 0)).toFixed(1)}s`,
      change: data.stats?.response_time_change || "0%",
      icon: Clock,
      trend: (data.stats?.response_time_change || "0%").startsWith("-") ? "down" : "up",
    },
    {
      label: "活躍用戶",
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
            總覽儀表板
          </h1>
          <p className="text-muted-foreground mt-2">
            監控聊天 AI 系統的關鍵指標和實時狀態
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="px-3 py-1">
            Production
          </Badge>
          <Button variant="ghost" size="icon" onClick={refetch}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* 操作引導卡片 */}
      <Alert className="border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-950/30">
        <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
        <AlertTitle className="text-blue-900 dark:text-blue-100">快速操作指南</AlertTitle>
        <AlertDescription className="mt-2 space-y-3">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            按照以下步驟順序操作，確保系統正常運行：
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
                <div className="text-xs font-semibold text-blue-900 dark:text-blue-100">劇本管理</div>
                <div className="text-xs text-blue-600 dark:text-blue-400">創建劇本</div>
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
                <div className="text-xs font-semibold text-blue-900 dark:text-blue-100">賬號管理</div>
                <div className="text-xs text-blue-600 dark:text-blue-400">創建賬號</div>
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
                <div className="text-xs font-semibold text-blue-900 dark:text-blue-100">角色分配</div>
                <div className="text-xs text-blue-600 dark:text-blue-400">可選步驟</div>
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
                <div className="text-xs font-semibold text-blue-900 dark:text-blue-100">分配方案</div>
                <div className="text-xs text-blue-600 dark:text-blue-400">可選步驟</div>
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
                <div className="text-xs font-semibold text-blue-900 dark:text-blue-100">自動化任務</div>
                <div className="text-xs text-blue-600 dark:text-blue-400">可選步驟</div>
              </div>
            </Link>
          </div>
          <p className="text-xs text-blue-700 dark:text-blue-300">
            💡 <strong>重要提示：</strong>必須先完成 ① 劇本管理和 ② 賬號管理，才能啟動賬號。如果啟動失敗提示"無法加載劇本"，請檢查賬號關聯的劇本是否存在。
          </p>
        </AlertDescription>
      </Alert>

      {/* 統計卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {stats.map((stat) => {
          const isClickable =
            stat.label === "今日會話量" ||
            stat.label === "錯誤數" ||
            stat.label === "平均響應時間";
          const clickHandler = () => {
            if (stat.label === "今日會話量") {
              handleCardClick("sessions", { range: "24h" });
            } else if (stat.label === "錯誤數") {
              handleCardClick("logs", { level: "error", range: "24h" });
            } else if (stat.label === "平均響應時間") {
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
            <CardTitle>最近 10 條會話</CardTitle>
            <CardDescription>
              查看最新的會話記錄和處理狀態
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>會話 ID</TableHead>
                  <TableHead>用戶</TableHead>
                  <TableHead>訊息數</TableHead>
                  <TableHead>狀態</TableHead>
                  <TableHead>持續時間</TableHead>
                  <TableHead className="text-right">時間</TableHead>
                  <TableHead className="w-16">操作</TableHead>
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
                          {session.status === "completed"
                            ? "已完成"
                            : session.status === "active"
                            ? "進行中"
                            : "失敗"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {session.duration}
                      </TableCell>
                      <TableCell className="text-right text-xs text-muted-foreground">
                        {new Date(session.started_at || session.timestamp).toLocaleString("zh-TW")}
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
                      暫無會話記錄
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
              <CardTitle>最近錯誤與警告</CardTitle>
              <CardDescription>
                系統異常和需要關注的事件
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
                            {error.severity === "high"
                              ? "高"
                              : error.severity === "medium"
                              ? "中"
                              : "低"}
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
                    暫無錯誤記錄
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
            <DialogTitle>會話詳情</DialogTitle>
            <DialogDescription>
              查看完整的會話信息和消息記錄
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
                    <span className="text-sm font-medium text-muted-foreground">會話 ID</span>
                    <span className="text-sm font-mono">{selectedSession.id}</span>
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">用戶</span>
                    <span className="text-sm">{selectedSession.user}</span>
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">狀態</span>
                    <Badge
                      variant={
                        selectedSession.status === "completed"
                          ? "default"
                          : selectedSession.status === "active"
                          ? "secondary"
                          : "destructive"
                      }
                    >
                      {selectedSession.status === "completed"
                        ? "已完成"
                        : selectedSession.status === "active"
                        ? "進行中"
                        : "失敗"}
                    </Badge>
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">持續時間</span>
                    <span className="text-sm">{selectedSession.duration}</span>
                  </div>
                  {selectedSession.token_usage && (
                    <>
                      <Separator />
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-muted-foreground">Token 用量</span>
                        <span className="text-sm">{selectedSession.token_usage.toLocaleString()}</span>
                      </div>
                    </>
                  )}
                  {selectedSession.model && (
                    <>
                      <Separator />
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-muted-foreground">模型</span>
                        <span className="text-sm">{selectedSession.model}</span>
                      </div>
                    </>
                  )}
                  {selectedSession.error_message && (
                    <>
                      <Separator />
                      <div className="space-y-2">
                        <span className="text-sm font-medium text-muted-foreground">錯誤信息</span>
                        <p className="text-sm text-destructive bg-destructive/10 p-2 rounded">
                          {selectedSession.error_message}
                        </p>
                      </div>
                    </>
                  )}
                  <Separator />
                  <div className="space-y-2">
                    <span className="text-sm font-medium text-muted-foreground">消息記錄</span>
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
                                {msg.role === "user" ? "用戶" : msg.role === "assistant" ? "助手" : "系統"}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {new Date(msg.timestamp).toLocaleString("zh-TW")}
                              </span>
                            </div>
                            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">暫無消息記錄</p>
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
