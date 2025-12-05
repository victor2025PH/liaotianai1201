"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Activity,
  Users,
  MessageSquare,
  Gift,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Wifi,
  WifiOff,
  RefreshCw,
  Bell,
} from "lucide-react";

// ==================== 類型定義 ====================

interface SystemMetrics {
  groups: {
    total: number;
    active: number;
    full: number;
  };
  ais: {
    total: number;
    online: number;
    busy: number;
  };
  users: {
    total: number;
    active_1h: number;
    new_24h: number;
  };
  messages: {
    count_1h: number;
    count_24h: number;
  };
  redpackets: {
    sent_24h: number;
    claimed_24h: number;
    amount_24h: number;
  };
  system: {
    uptime_seconds: number;
    error_count_1h: number;
  };
}

interface GroupMetrics {
  group_id: number;
  group_name: string;
  status: string;
  ai_count: number;
  user_count: number;
  online_users: number;
  messages_1h: number;
  user_joins_1h: number;
  engagement_rate: number;
}

interface Alert {
  level: string;
  title: string;
  message: string;
  timestamp: string;
  group_id?: number;
  resolved: boolean;
}

interface MonitorEvent {
  event_type: string;
  timestamp: string;
  data: Record<string, any>;
  group_id?: number;
  user_id?: number;
}

// ==================== 工具函數 ====================

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (days > 0) return `${days}天 ${hours}小時`;
  if (hours > 0) return `${hours}小時 ${minutes}分`;
  return `${minutes}分鐘`;
}

function formatNumber(num: number): string {
  if (num >= 10000) return `${(num / 10000).toFixed(1)}萬`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

function getStatusColor(status: string): string {
  switch (status) {
    case "active": return "bg-green-500";
    case "warming_up": return "bg-yellow-500";
    case "full": return "bg-blue-500";
    case "error": return "bg-red-500";
    default: return "bg-gray-500";
  }
}

function getStatusText(status: string): string {
  switch (status) {
    case "active": return "活躍";
    case "warming_up": return "熱身中";
    case "full": return "已滿";
    case "archived": return "已歸檔";
    case "error": return "錯誤";
    default: return status;
  }
}

function getAlertLevelColor(level: string): string {
  switch (level) {
    case "critical": return "destructive";
    case "error": return "destructive";
    case "warning": return "warning";
    default: return "secondary";
  }
}

// ==================== 組件 ====================

// 統計卡片
function StatCard({
  title,
  value,
  subValue,
  icon: Icon,
  trend,
  trendValue,
}: {
  title: string;
  value: string | number;
  subValue?: string;
  icon: any;
  trend?: "up" | "down" | "stable";
  trendValue?: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <div className="flex items-center text-xs text-muted-foreground">
          {trend && (
            <span className={`mr-1 ${trend === "up" ? "text-green-500" : trend === "down" ? "text-red-500" : ""}`}>
              {trend === "up" ? <TrendingUp className="h-3 w-3 inline" /> : 
               trend === "down" ? <TrendingDown className="h-3 w-3 inline" /> : null}
              {trendValue}
            </span>
          )}
          {subValue}
        </div>
      </CardContent>
    </Card>
  );
}

// 群組卡片
function GroupCard({ group }: { group: GroupMetrics }) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium truncate">
            {group.group_name}
          </CardTitle>
          <Badge variant="outline" className={getStatusColor(group.status)}>
            {getStatusText(group.status)}
          </Badge>
        </div>
        <CardDescription className="text-xs">
          ID: {group.group_id}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex items-center gap-1">
            <Users className="h-3 w-3 text-muted-foreground" />
            <span>{group.user_count} 用戶</span>
          </div>
          <div className="flex items-center gap-1">
            <Activity className="h-3 w-3 text-muted-foreground" />
            <span>{group.ai_count} AI</span>
          </div>
          <div className="flex items-center gap-1">
            <MessageSquare className="h-3 w-3 text-muted-foreground" />
            <span>{group.messages_1h}/h</span>
          </div>
          <div className="flex items-center gap-1">
            <TrendingUp className="h-3 w-3 text-muted-foreground" />
            <span>{group.engagement_rate}%</span>
          </div>
        </div>
        <div className="mt-2">
          <div className="flex justify-between text-xs text-muted-foreground mb-1">
            <span>參與度</span>
            <span>{group.engagement_rate}%</span>
          </div>
          <Progress value={group.engagement_rate} className="h-1" />
        </div>
      </CardContent>
    </Card>
  );
}

// 事件列表項
function EventItem({ event }: { event: MonitorEvent }) {
  const getEventIcon = () => {
    switch (event.event_type) {
      case "user_joined": return <Users className="h-4 w-4 text-green-500" />;
      case "group_message": return <MessageSquare className="h-4 w-4 text-blue-500" />;
      case "redpacket_claimed": return <Gift className="h-4 w-4 text-red-500" />;
      case "alert": return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default: return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getEventText = () => {
    switch (event.event_type) {
      case "user_joined": return `用戶 ${event.user_id} 加入群組`;
      case "group_message": return `群組 ${event.group_id} 新消息`;
      case "redpacket_claimed": return `紅包被領取 ${event.data?.amount || 0} USDT`;
      case "system_status": return "系統狀態更新";
      default: return event.event_type;
    }
  };

  return (
    <div className="flex items-center gap-3 py-2 border-b last:border-b-0">
      {getEventIcon()}
      <div className="flex-1 min-w-0">
        <p className="text-sm truncate">{getEventText()}</p>
        <p className="text-xs text-muted-foreground">
          {new Date(event.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}

// 告警項
function AlertItem({ alert }: { alert: Alert }) {
  return (
    <div className={`p-3 rounded-lg border ${
      alert.level === "critical" || alert.level === "error" 
        ? "border-red-200 bg-red-50" 
        : alert.level === "warning"
        ? "border-yellow-200 bg-yellow-50"
        : "border-gray-200 bg-gray-50"
    }`}>
      <div className="flex items-start gap-2">
        <AlertTriangle className={`h-4 w-4 mt-0.5 ${
          alert.level === "critical" || alert.level === "error" 
            ? "text-red-500" 
            : "text-yellow-500"
        }`} />
        <div className="flex-1">
          <p className="font-medium text-sm">{alert.title}</p>
          <p className="text-xs text-muted-foreground">{alert.message}</p>
          <p className="text-xs text-muted-foreground mt-1">
            {new Date(alert.timestamp).toLocaleString()}
          </p>
        </div>
        {!alert.resolved && (
          <Button variant="ghost" size="sm" className="h-6 text-xs">
            解決
          </Button>
        )}
      </div>
    </div>
  );
}

// ==================== 主頁面 ====================

export default function RealtimeMonitorPage() {
  // 狀態
  const [isConnected, setIsConnected] = useState(false);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [groups, setGroups] = useState<GroupMetrics[]>([]);
  const [events, setEvents] = useState<MonitorEvent[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  
  // WebSocket ref
  const wsRef = useRef<WebSocket | null>(null);
  
  // 模擬數據（實際應從 WebSocket 獲取）
  useEffect(() => {
    // 模擬初始數據
    setSystemMetrics({
      groups: { total: 5, active: 3, full: 1 },
      ais: { total: 12, online: 10, busy: 6 },
      users: { total: 156, active_1h: 45, new_24h: 23 },
      messages: { count_1h: 342, count_24h: 2845 },
      redpackets: { sent_24h: 28, claimed_24h: 156, amount_24h: 234.5 },
      system: { uptime_seconds: 86400 * 3 + 3600 * 5, error_count_1h: 2 }
    });
    
    setGroups([
      { group_id: -1001234567890, group_name: "🧧 福利群 1", status: "active", ai_count: 6, user_count: 45, online_users: 23, messages_1h: 89, user_joins_1h: 5, engagement_rate: 68 },
      { group_id: -1001234567891, group_name: "🧧 福利群 2", status: "active", ai_count: 4, user_count: 32, online_users: 15, messages_1h: 56, user_joins_1h: 3, engagement_rate: 52 },
      { group_id: -1001234567892, group_name: "🧧 福利群 3", status: "warming_up", ai_count: 6, user_count: 8, online_users: 6, messages_1h: 34, user_joins_1h: 8, engagement_rate: 85 },
      { group_id: -1001234567893, group_name: "🧧 福利群 4", status: "full", ai_count: 5, user_count: 100, online_users: 42, messages_1h: 123, user_joins_1h: 0, engagement_rate: 75 },
    ]);
    
    setAlerts([
      { level: "warning", title: "AI 負載較高", message: "AI-003 當前分配了 5 個群組，接近上限", timestamp: new Date().toISOString(), resolved: false },
      { level: "info", title: "新群組創建", message: "福利群 3 已創建並開始熱身", timestamp: new Date(Date.now() - 300000).toISOString(), resolved: true },
    ]);
    
    setIsConnected(true);
    setLastUpdate(new Date());
    
    // 模擬實時事件
    const interval = setInterval(() => {
      const eventTypes = ["user_joined", "group_message", "redpacket_claimed", "system_status"];
      const newEvent: MonitorEvent = {
        event_type: eventTypes[Math.floor(Math.random() * eventTypes.length)],
        timestamp: new Date().toISOString(),
        data: { amount: Math.random() * 5 },
        group_id: -1001234567890 + Math.floor(Math.random() * 4),
        user_id: Math.floor(Math.random() * 1000000)
      };
      
      setEvents(prev => [newEvent, ...prev.slice(0, 49)]);
      setLastUpdate(new Date());
    }, 3000);
    
    return () => clearInterval(interval);
  }, []);
  
  // 刷新數據
  const handleRefresh = useCallback(() => {
    setLastUpdate(new Date());
  }, []);

  return (
    <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
      {/* 標題和狀態 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">實時監控</h2>
          <p className="text-muted-foreground">
            監控所有群組和 AI 帳號的實時狀態
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* 連接狀態 */}
          <div className="flex items-center gap-2">
            {isConnected ? (
              <>
                <Wifi className="h-4 w-4 text-green-500" />
                <span className="text-sm text-green-600">已連接</span>
              </>
            ) : (
              <>
                <WifiOff className="h-4 w-4 text-red-500" />
                <span className="text-sm text-red-600">已斷開</span>
              </>
            )}
          </div>
          
          {/* 最後更新時間 */}
          {lastUpdate && (
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <Clock className="h-3 w-3" />
              {lastUpdate.toLocaleTimeString()}
            </div>
          )}
          
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-1" />
            刷新
          </Button>
        </div>
      </div>

      {/* 系統概覽卡片 */}
      {systemMetrics && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="活躍群組"
            value={systemMetrics.groups.active}
            subValue={`共 ${systemMetrics.groups.total} 個群組`}
            icon={Activity}
          />
          <StatCard
            title="在線 AI"
            value={systemMetrics.ais.online}
            subValue={`${systemMetrics.ais.busy} 個忙碌中`}
            icon={Users}
          />
          <StatCard
            title="今日消息"
            value={formatNumber(systemMetrics.messages.count_24h)}
            subValue={`最近1小時 ${systemMetrics.messages.count_1h}`}
            icon={MessageSquare}
            trend="up"
            trendValue="+12%"
          />
          <StatCard
            title="紅包金額"
            value={`${systemMetrics.redpackets.amount_24h} USDT`}
            subValue={`${systemMetrics.redpackets.claimed_24h} 次領取`}
            icon={Gift}
          />
        </div>
      )}

      {/* 主內容區 */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* 左側：群組列表 */}
        <div className="md:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>群組狀態</CardTitle>
              <CardDescription>所有活躍群組的實時狀態</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2">
                {groups.map(group => (
                  <GroupCard key={group.group_id} group={group} />
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 右側：事件和告警 */}
        <div className="space-y-4">
          {/* 告警 */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">告警</CardTitle>
                <Badge variant="outline">
                  {alerts.filter(a => !a.resolved).length}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[200px]">
                <div className="space-y-2">
                  {alerts.length === 0 ? (
                    <div className="flex items-center justify-center h-20 text-sm text-muted-foreground">
                      <CheckCircle className="h-4 w-4 mr-2" />
                      暫無告警
                    </div>
                  ) : (
                    alerts.map((alert, i) => (
                      <AlertItem key={i} alert={alert} />
                    ))
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* 實時事件 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">實時事件</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[300px]">
                {events.length === 0 ? (
                  <div className="flex items-center justify-center h-20 text-sm text-muted-foreground">
                    等待事件...
                  </div>
                ) : (
                  events.map((event, i) => (
                    <EventItem key={i} event={event} />
                  ))
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* 系統信息 */}
      {systemMetrics && (
        <Card>
          <CardHeader>
            <CardTitle>系統信息</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div>
                <p className="text-sm text-muted-foreground">運行時間</p>
                <p className="text-lg font-medium">
                  {formatUptime(systemMetrics.system.uptime_seconds)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">總用戶數</p>
                <p className="text-lg font-medium">{systemMetrics.users.total}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">新增用戶(24h)</p>
                <p className="text-lg font-medium text-green-600">
                  +{systemMetrics.users.new_24h}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">錯誤數(1h)</p>
                <p className={`text-lg font-medium ${
                  systemMetrics.system.error_count_1h > 0 ? "text-red-600" : ""
                }`}>
                  {systemMetrics.system.error_count_1h}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
