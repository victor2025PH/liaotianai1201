"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { useToast } from "@/hooks/use-toast"
import { 
  Users, MessageSquare, RefreshCw, Search, 
  Activity, Clock, UserPlus, Settings, ExternalLink, Link2
} from "lucide-react"

import { getApiBaseUrl } from "@/lib/api/config";

const API_BASE = getApiBaseUrl();

interface GroupInfo {
  id: string
  title: string
  member_count: number
  ai_accounts: number
  real_users: number
  message_count: number
  last_activity: string
  status: "active" | "idle" | "paused"
  auto_chat: boolean
  redpacket: boolean
  group_id?: number  // Telegram 群組 ID
  username?: string  // 群組用戶名
  invite_link?: string  // 邀請鏈接
}

export default function GroupsPage() {
  const { toast } = useToast()
  const [groups, setGroups] = useState<GroupInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")

  const fetchGroups = async () => {
    setLoading(true)
    try {
      // 嘗試從 Worker API 獲取群组数据
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/workers/`)
      if (!res.ok) {
        if (res.status === 404) {
          // 端点不存在，使用模拟数据
          console.warn("Workers API 端点不存在，使用模拟数据")
        } else if (res.status === 401) {
          console.warn("未授权，可能需要登录")
          toast({ title: "错误", description: "未授权，请重新登录", variant: "destructive" })
          setGroups([])
          return
        } else {
          throw new Error(`HTTP ${res.status}`)
        }
      } else {
        const data = await res.json()
        // TODO: 从 Worker 数据中提取群组信息
        // 实际应该从专门的群组 API 获取
      }
      
      // 從 Worker 数据中提取群组信息（模擬数据）
      // 實際應該從專門的群组 API 獲取
      const mockGroups: GroupInfo[] = [
        {
          id: "group_1",
          title: "红包遊戲群 1",
          member_count: 8,
          ai_accounts: 6,
          real_users: 2,
          message_count: 156,
          last_activity: new Date().toISOString(),
          status: "active",
          auto_chat: true,
          redpacket: true
        },
        {
          id: "group_2", 
          title: "AI 聊天测试群",
          member_count: 6,
          ai_accounts: 6,
          real_users: 0,
          message_count: 89,
          last_activity: new Date(Date.now() - 3600000).toISOString(),
          status: "idle",
          auto_chat: true,
          redpacket: false
        }
      ]
      
      setGroups(mockGroups)
    } catch (error) {
      console.error("獲取群组失败:", error)
      const errorMessage = error instanceof Error ? error.message : "未知错误"
      if (!errorMessage.includes("401")) {
        toast({ title: "错误", description: `獲取群组数据失败: ${errorMessage}`, variant: "destructive" })
      }
      // 使用模拟数据作为降级方案
      setGroups([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchGroups()
    const interval = setInterval(fetchGroups, 30000)
    return () => clearInterval(interval)
  }, [])

  const filteredGroups = groups.filter(g => 
    g.title.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const stats = {
    total: groups.length,
    active: groups.filter(g => g.status === "active").length,
    totalMessages: groups.reduce((sum, g) => sum + g.message_count, 0),
    totalMembers: groups.reduce((sum, g) => sum + g.member_count, 0)
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "active":
        return <Badge className="bg-green-500">活跃</Badge>
      case "idle":
        return <Badge variant="secondary">空閒</Badge>
      case "paused":
        return <Badge variant="destructive">已暂停</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* 標題 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Users className="h-6 w-6" />
            群组监控
          </h1>
          <p className="text-sm text-muted-foreground">监控和管理所有 Telegram 群组</p>
        </div>
        <Button onClick={fetchGroups} variant="outline" size="sm" disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          刷新
        </Button>
      </div>

      {/* 統計卡片 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/10">
                <Users className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <div className="text-2xl font-bold">{stats.total}</div>
                <p className="text-xs text-muted-foreground">總群组數</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-500/10">
                <Activity className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <div className="text-2xl font-bold">{stats.active}</div>
                <p className="text-xs text-muted-foreground">活跃群组</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/10">
                <MessageSquare className="h-5 w-5 text-purple-500" />
              </div>
              <div>
                <div className="text-2xl font-bold">{stats.totalMessages}</div>
                <p className="text-xs text-muted-foreground">總消息数</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-orange-500/10">
                <UserPlus className="h-5 w-5 text-orange-500" />
              </div>
              <div>
                <div className="text-2xl font-bold">{stats.totalMembers}</div>
                <p className="text-xs text-muted-foreground">總成员数</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 搜索 */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索群组名称..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* 群组列表 */}
      <Card>
        <CardHeader className="py-4">
          <CardTitle className="text-base">群组列表</CardTitle>
          <CardDescription>共 {filteredGroups.length} 个群组</CardDescription>
        </CardHeader>
        <CardContent>
          {filteredGroups.length === 0 ? (
            <div className="text-center py-12">
              <Users className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-medium mb-2">暫无群组</h3>
              <p className="text-muted-foreground text-sm mb-4">
                在节点管理页面创建新群组
              </p>
              <Button variant="outline" asChild>
                <a href="/group-ai/nodes">前往节点管理</a>
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredGroups.map((group) => (
                <div key={group.id} className="border rounded-lg p-4 hover:bg-muted/30 transition-colors">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-primary/10">
                        <Users className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <h4 className="font-medium">{group.title}</h4>
                        <p className="text-xs text-muted-foreground">ID: {group.id}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(group.status)}
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <Settings className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground text-xs">成员数</p>
                      <p className="font-medium">{group.member_count}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-xs">AI 账号</p>
                      <p className="font-medium text-blue-500">{group.ai_accounts}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-xs">真实用户</p>
                      <p className="font-medium text-green-500">{group.real_users}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-xs">消息数</p>
                      <p className="font-medium">{group.message_count}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-xs">最后活动</p>
                      <p className="font-medium flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(group.last_activity).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-3 pt-3 border-t">
                    <div className="flex gap-2">
                      <Badge variant={group.auto_chat ? "default" : "outline"} className="text-xs">
                        {group.auto_chat ? "✓ 自动聊天" : "✗ 自动聊天"}
                      </Badge>
                      <Badge variant={group.redpacket ? "default" : "outline"} className="text-xs">
                        {group.redpacket ? "✓ 红包遊戲" : "✗ 红包遊戲"}
                      </Badge>
                    </div>
                    {/* 群組鏈接 */}
                    {(group.username || group.invite_link || group.group_id) && (
                      <div className="flex gap-2">
                        {group.username && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-7 text-xs"
                            onClick={() => {
                              // 嘗試打開 Telegram 客戶端
                              if (!group.username) return
                              const username = (group.username || '').replace('@', '')
                              if (!username) return
                              const telegramUrl = `tg://resolve?domain=${username}`
                              const webUrl = `https://t.me/${username}`
                              
                              // 嘗試打開客戶端，如果失敗則打開網頁
                              window.open(telegramUrl, '_blank')
                              setTimeout(() => {
                                // 如果客戶端沒有打開，則打開網頁
                                window.open(webUrl, '_blank')
                              }, 500)
                            }}
                          >
                            <Link2 className="h-3 w-3 mr-1" />
                            打開群組
                          </Button>
                        )}
                        {group.invite_link && !group.username && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-7 text-xs"
                            onClick={() => {
                              // 嘗試打開 Telegram 客戶端
                              const telegramUrl = group.invite_link!.replace('https://t.me/', 'tg://join?invite=')
                              const webUrl = group.invite_link
                              
                              window.open(telegramUrl, '_blank')
                              setTimeout(() => {
                                window.open(webUrl, '_blank')
                              }, 500)
                            }}
                          >
                            <ExternalLink className="h-3 w-3 mr-1" />
                            加入群組
                          </Button>
                        )}
                        {group.group_id && !group.username && !group.invite_link && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-7 text-xs"
                            onClick={async () => {
                              try {
                                const { fetchWithAuth } = await import("@/lib/api/client")
                                const res = await fetchWithAuth(`${API_BASE}/group-ai/groups/${group.group_id}/invite-link`)
                                if (res.ok) {
                                  const data = await res.json()
                                  if (data.success && data.invite_link) {
                                    // 嘗試打開 Telegram 客戶端
                                    if (data.telegram_link) {
                                      window.open(data.telegram_link, '_blank')
                                    }
                                    // 打開網頁鏈接
                                    setTimeout(() => {
                                      if (data.web_link) {
                                        window.open(data.web_link, '_blank')
                                      }
                                    }, 500)
                                  } else if (data.requires_auth) {
                                    toast({
                                      title: "需要授權",
                                      description: data.message || "請先啟動賬號以獲取邀請鏈接",
                                      variant: "destructive"
                                    })
                                  }
                                } else {
                                  throw new Error("獲取邀請鏈接失敗")
                                }
                              } catch (error) {
                                toast({
                                  title: "錯誤",
                                  description: "無法獲取群組邀請鏈接",
                                  variant: "destructive"
                                })
                              }
                            }}
                          >
                            <Link2 className="h-3 w-3 mr-1" />
                            獲取鏈接
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

