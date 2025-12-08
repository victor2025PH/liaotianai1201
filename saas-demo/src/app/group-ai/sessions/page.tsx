"use client"

import { useState, useEffect, useMemo } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { useToast } from "@/hooks/use-toast"
import { 
  getAccounts, 
  stopAccount,
  type Account 
} from "@/lib/api/group-ai"
import { MessageSquare, Search, RefreshCw, LogOut, User, Phone, Clock, Server, AlertCircle, CheckCircle2, XCircle } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"

// 格式化时间戳
const formatTimestamp = (timestamp?: string | null): string => {
  if (!timestamp) return "从未活跃"
  try {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return "刚刚"
    if (minutes < 60) return `${minutes} 分钟前`
    if (hours < 24) return `${hours} 小时前`
    if (days < 7) return `${days} 天前`
    
    return date.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
  } catch {
    return timestamp
  }
}

// 获取状态信息
const getStatusInfo = (status: string) => {
  const statusLower = status.toLowerCase()
  
  if (statusLower.includes("running") || statusLower.includes("active") || statusLower === "online") {
    return {
      label: "在线",
      variant: "default" as const,
      icon: CheckCircle2,
      color: "text-green-600",
      dotColor: "bg-green-500",
    }
  } else if (statusLower.includes("stopped") || statusLower.includes("inactive") || statusLower === "offline") {
    return {
      label: "离线",
      variant: "secondary" as const,
      icon: XCircle,
      color: "text-gray-600",
      dotColor: "bg-gray-500",
    }
  } else if (statusLower.includes("error") || statusLower.includes("failed")) {
    return {
      label: "错误",
      variant: "destructive" as const,
      icon: AlertCircle,
      color: "text-red-600",
      dotColor: "bg-red-500",
    }
  } else {
    return {
      label: status,
      variant: "outline" as const,
      icon: Clock,
      color: "text-yellow-600",
      dotColor: "bg-yellow-500",
    }
  }
}

// 获取头像显示名称
const getAvatarName = (account: Account): string => {
  if (account.display_name) return account.display_name
  if (account.first_name) return account.first_name
  if (account.username) return account.username
  if (account.phone_number) return account.phone_number
  return account.account_id.slice(0, 2).toUpperCase()
}

// Mock 数据（用于演示）
const mockSessions: Account[] = [
  {
    account_id: "mock-001",
    session_file: "session_001.session",
    script_id: "default",
    status: "running",
    group_count: 5,
    message_count: 120,
    reply_count: 45,
    last_activity: new Date(Date.now() - 300000).toISOString(),
    phone_number: "+1234567890",
    username: "test_user_1",
    display_name: "测试用户 1",
    first_name: "测试",
    avatar_url: undefined,
    server_id: "server-1",
    node_id: "node-1",
  },
  {
    account_id: "mock-002",
    session_file: "session_002.session",
    script_id: "default",
    status: "stopped",
    group_count: 3,
    message_count: 80,
    reply_count: 30,
    last_activity: new Date(Date.now() - 3600000).toISOString(),
    phone_number: "+1234567891",
    username: "test_user_2",
    display_name: "测试用户 2",
    first_name: "测试",
    avatar_url: undefined,
    server_id: "server-1",
    node_id: "node-1",
  },
  {
    account_id: "mock-003",
    session_file: "session_003.session",
    script_id: "default",
    status: "error",
    group_count: 0,
    message_count: 0,
    reply_count: 0,
    last_activity: new Date(Date.now() - 86400000).toISOString(),
    phone_number: "+1234567892",
    username: "test_user_3",
    display_name: "测试用户 3",
    first_name: "测试",
    avatar_url: undefined,
    server_id: "server-2",
    node_id: "node-2",
  },
]

export default function SessionsPage() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [useMockData, setUseMockData] = useState(false)
  const [disconnectDialogOpen, setDisconnectDialogOpen] = useState(false)
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null)
  const [disconnecting, setDisconnecting] = useState(false)
  const { toast } = useToast()

  // 加载账号列表
  const loadAccounts = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getAccounts()
      setAccounts(data)
      setUseMockData(false)
    } catch (err) {
      console.error("加载账号列表失败:", err)
      setError(err instanceof Error ? err.message : "加载账号列表失败")
      // 如果 API 失败，使用 mock 数据
      if (!useMockData) {
        setAccounts(mockSessions)
        setUseMockData(true)
        toast({
          title: "使用 Mock 数据",
          description: "无法连接到后端服务，已切换到演示数据",
          variant: "default",
        })
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAccounts()
  }, [])

  // 过滤账号
  const filteredAccounts = useMemo(() => {
    if (!searchQuery) return accounts

    const query = searchQuery.toLowerCase()
    return accounts.filter(
      (account) =>
        account.account_id.toLowerCase().includes(query) ||
        account.phone_number?.toLowerCase().includes(query) ||
        account.username?.toLowerCase().includes(query) ||
        account.display_name?.toLowerCase().includes(query) ||
        account.first_name?.toLowerCase().includes(query)
    )
  }, [accounts, searchQuery])

  // 断开连接
  const handleDisconnect = async () => {
    if (!selectedAccount) return

    try {
      setDisconnecting(true)
      await stopAccount(selectedAccount.account_id)
      toast({
        title: "断开成功",
        description: `账号 ${selectedAccount.display_name || selectedAccount.account_id} 已断开连接`,
      })
      setDisconnectDialogOpen(false)
      setSelectedAccount(null)
      // 重新加载列表
      await loadAccounts()
    } catch (err) {
      toast({
        title: "断开失败",
        description: err instanceof Error ? err.message : "断开连接时发生错误",
        variant: "destructive",
      })
    } finally {
      setDisconnecting(false)
    }
  }

  // 统计信息
  const stats = useMemo(() => {
    const total = accounts.length
    const online = accounts.filter((acc) => {
      const status = acc.status.toLowerCase()
      return status.includes("running") || status.includes("active") || status === "online"
    }).length
    const offline = total - online
    return { total, online, offline }
  }, [accounts])

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-6 w-6" />
          <h1 className="text-3xl font-bold">会话管理</h1>
        </div>
        {useMockData && (
          <Badge variant="outline" className="text-yellow-600 border-yellow-600">
            使用 Mock 数据
          </Badge>
        )}
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总会话数</CardTitle>
            <User className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">所有已连接的账号</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">在线</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.online}</div>
            <p className="text-xs text-muted-foreground">当前活跃的会话</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">离线</CardTitle>
            <XCircle className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-600">{stats.offline}</div>
            <p className="text-xs text-muted-foreground">已断开或未激活</p>
          </CardContent>
        </Card>
      </div>

      {/* 搜索和操作 */}
      <Card>
        <CardHeader>
          <CardTitle>搜索与操作</CardTitle>
          <CardDescription>搜索账号或管理会话</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="搜索账号（ID、手机号、用户名...）"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button
              variant="outline"
              onClick={loadAccounts}
              disabled={loading}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              刷新
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 账号列表 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>会话列表</CardTitle>
              <CardDescription>
                共 {filteredAccounts.length} 个会话
                {searchQuery && `（搜索：${searchQuery}）`}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <Card key={i}>
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <Skeleton className="h-12 w-12 rounded-full" />
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-3 w-32" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : error && !useMockData ? (
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <AlertCircle className="h-12 w-12 text-destructive" />
              <div className="text-center">
                <p className="text-lg font-semibold">加载会话失败</p>
                <p className="text-sm text-muted-foreground mt-1">{error}</p>
                <Button
                  variant="outline"
                  onClick={() => {
                    setUseMockData(true)
                    setAccounts(mockSessions)
                    toast({
                      title: "已切换到 Mock 数据",
                      description: "使用模拟数据进行演示",
                    })
                  }}
                  className="mt-4"
                >
                  使用 Mock 数据
                </Button>
              </div>
            </div>
          ) : filteredAccounts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <MessageSquare className="h-12 w-12 text-muted-foreground" />
              <div className="text-center">
                <p className="text-lg font-semibold">暂无会话</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {searchQuery ? "请尝试调整搜索条件" : "当前没有已连接的 Telegram 账号"}
                </p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredAccounts.map((account) => {
                const statusInfo = getStatusInfo(account.status)
                const StatusIcon = statusInfo.icon

                return (
                  <Card key={account.account_id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-6">
                      <div className="flex items-start gap-4">
                        {/* 头像 */}
                        <Avatar className="h-12 w-12">
                          <AvatarImage src={account.avatar_url} alt={getAvatarName(account)} />
                          <AvatarFallback className="bg-primary text-primary-foreground">
                            {getAvatarName(account).slice(0, 2)}
                          </AvatarFallback>
                        </Avatar>

                        {/* 信息 */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold truncate">
                              {account.display_name || account.first_name || account.username || account.account_id}
                            </h3>
                            <div className={`h-2 w-2 rounded-full ${statusInfo.dotColor} flex-shrink-0`} />
                          </div>

                          <div className="space-y-1 text-sm text-muted-foreground">
                            {account.phone_number && (
                              <div className="flex items-center gap-1">
                                <Phone className="h-3 w-3" />
                                <span className="truncate">{account.phone_number}</span>
                              </div>
                            )}
                            {account.username && (
                              <div className="flex items-center gap-1">
                                <User className="h-3 w-3" />
                                <span className="truncate">@{account.username}</span>
                              </div>
                            )}
                            <div className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              <span>{formatTimestamp(account.last_activity)}</span>
                            </div>
                            {account.server_id && (
                              <div className="flex items-center gap-1">
                                <Server className="h-3 w-3" />
                                <span className="truncate">{account.server_id}</span>
                              </div>
                            )}
                          </div>

                          {/* 状态标签 */}
                          <div className="mt-2">
                            <Badge variant={statusInfo.variant} className="flex items-center gap-1 w-fit">
                              <StatusIcon className="h-3 w-3" />
                              {statusInfo.label}
                            </Badge>
                          </div>

                          {/* 操作按钮 */}
                          <div className="mt-3">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setSelectedAccount(account)
                                setDisconnectDialogOpen(true)
                              }}
                              disabled={account.status.toLowerCase().includes("stopped")}
                              className="w-full flex items-center gap-2"
                            >
                              <LogOut className="h-4 w-4" />
                              断开连接
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 断开连接确认对话框 */}
      <AlertDialog open={disconnectDialogOpen} onOpenChange={setDisconnectDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认断开连接</AlertDialogTitle>
            <AlertDialogDescription>
              确定要断开账号 <strong>{selectedAccount?.display_name || selectedAccount?.account_id}</strong> 的连接吗？
              <br />
              断开后，该账号将停止所有活动。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={disconnecting}>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDisconnect}
              disabled={disconnecting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {disconnecting ? "断开中..." : "确认断开"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
