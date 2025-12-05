"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Progress } from "@/components/ui/progress"
import { useToast } from "@/hooks/use-toast"
import { 
  Users, MessageSquare, UserPlus, Send, Clock, Target,
  Play, Square, RefreshCw, Loader2, ArrowRight, Check,
  Calendar, TrendingUp, Gift, Zap, Heart, Star
} from "lucide-react"

import { getApiBaseUrl } from "@/lib/api/config"

const API_BASE = getApiBaseUrl()

// 階段配置
const STAGES = [
  { id: "new_friend", name: "新好友", icon: "👋", color: "bg-blue-100" },
  { id: "greeting", name: "打招呼", icon: "💬", color: "bg-green-100" },
  { id: "warming_up", name: "升溫中", icon: "🔥", color: "bg-yellow-100" },
  { id: "building_trust", name: "建立信任", icon: "🤝", color: "bg-orange-100" },
  { id: "ready_to_invite", name: "準備邀請", icon: "🎯", color: "bg-purple-100" },
  { id: "invited", name: "已邀請", icon: "📨", color: "bg-pink-100" },
  { id: "joined_group", name: "已進群", icon: "✅", color: "bg-emerald-100" },
  { id: "converted", name: "已轉化", icon: "🎉", color: "bg-red-100" },
]

export default function PrivateFunnelPage() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState("overview")
  
  // 配置狀態
  const [config, setConfig] = useState({
    enabled: true,
    auto_accept_friend: true,
    greeting_delay_seconds: 60,
    chat_interval_min: 1800,
    chat_interval_max: 7200,
    daily_message_limit: 10,
    reply_delay_min: 3,
    reply_delay_max: 30,
    invite_after_days: 3.0,
    min_messages_before_invite: 10,
    target_group_ids: [] as number[],
    invite_message_template: "最近群裡在玩紅包遊戲，挺有意思的，要不要一起來玩？",
  })
  
  // 用戶列表
  const [users, setUsers] = useState<any[]>([])
  const [usersByStage, setUsersByStage] = useState<Record<string, number>>({})
  
  // 統計數據
  const [stats, setStats] = useState<any>(null)
  
  // 準備邀請的用戶
  const [readyUsers, setReadyUsers] = useState<any[]>([])
  
  // 新增目標群組
  const [newGroupId, setNewGroupId] = useState("")

  // 獲取配置
  const fetchConfig = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/private-funnel/config`)
      if (res.ok) {
        const data = await res.json()
        if (data.config) setConfig(data.config)
      }
    } catch (error) {
      console.error("獲取配置失敗:", error)
    }
  }

  // 更新配置
  const updateConfig = async () => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/private-funnel/config`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      })
      if (res.ok) {
        toast({ title: "配置已更新" })
      }
    } catch (error) {
      toast({ title: "更新失敗", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 啟用/禁用漏斗
  const toggleFunnel = async (enable: boolean) => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/private-funnel/${enable ? "enable" : "disable"}`, {
        method: "POST",
      })
      if (res.ok) {
        setConfig({ ...config, enabled: enable })
        toast({ title: enable ? "私聊轉化已啟用" : "私聊轉化已禁用" })
      }
    } catch (error) {
      toast({ title: "操作失敗", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 獲取用戶列表
  const fetchUsers = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/private-funnel/users`)
      if (res.ok) {
        const data = await res.json()
        setUsers(data.users || [])
        setUsersByStage(data.by_stage || {})
      }
    } catch (error) {
      console.error("獲取用戶失敗:", error)
    }
  }

  // 獲取統計
  const fetchStats = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/private-funnel/stats`)
      if (res.ok) {
        const data = await res.json()
        setStats(data)
      }
    } catch (error) {
      console.error("獲取統計失敗:", error)
    }
  }

  // 獲取準備邀請的用戶
  const fetchReadyUsers = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/private-funnel/ready-to-invite`)
      if (res.ok) {
        const data = await res.json()
        setReadyUsers(data.users || [])
      }
    } catch (error) {
      console.error("獲取準備用戶失敗:", error)
    }
  }

  // 邀請用戶進群
  const inviteUser = async (userId: number) => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/private-funnel/users/${userId}/invite`, {
        method: "POST",
      })
      if (res.ok) {
        toast({ title: "邀請已發送" })
        fetchUsers()
        fetchReadyUsers()
      }
    } catch (error) {
      toast({ title: "邀請失敗", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 批量邀請
  const batchInvite = async () => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/private-funnel/batch-invite`, {
        method: "POST",
      })
      if (res.ok) {
        const data = await res.json()
        toast({ title: `已邀請 ${data.count} 個用戶` })
        fetchUsers()
        fetchReadyUsers()
      }
    } catch (error) {
      toast({ title: "批量邀請失敗", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 設置目標群組
  const addTargetGroup = async () => {
    if (!newGroupId) return
    const groupId = parseInt(newGroupId)
    if (isNaN(groupId)) return
    
    const newGroups = [...config.target_group_ids, groupId]
    setConfig({ ...config, target_group_ids: newGroups })
    
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      await fetchWithAuth(`${API_BASE}/group-ai/private-funnel/set-target-groups`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newGroups),
      })
      setNewGroupId("")
      toast({ title: "目標群組已添加" })
    } catch (error) {
      console.error("設置群組失敗:", error)
    }
  }

  useEffect(() => {
    fetchConfig()
    fetchUsers()
    fetchStats()
    fetchReadyUsers()
  }, [])

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 頁面標題 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Heart className="h-8 w-8 text-pink-500" />
            私聊轉化漏斗
          </h1>
          <p className="text-muted-foreground mt-1">
            用戶添加好友 → 自動聊天培養 → 3天後邀請進群玩紅包
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant={config.enabled ? "destructive" : "default"}
            onClick={() => toggleFunnel(!config.enabled)}
            disabled={loading}
          >
            {config.enabled ? <Square className="h-4 w-4 mr-2" /> : <Play className="h-4 w-4 mr-2" />}
            {config.enabled ? "停止" : "啟動"}
          </Button>
          <Button variant="outline" onClick={() => { fetchUsers(); fetchStats(); fetchReadyUsers(); }}>
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
        </div>
      </div>

      {/* 流程說明 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            {STAGES.slice(0, 6).map((stage, index) => (
              <div key={stage.id} className="flex items-center">
                <div className="text-center">
                  <div className={`w-12 h-12 rounded-full ${stage.color} flex items-center justify-center text-2xl mb-1`}>
                    {stage.icon}
                  </div>
                  <p className="text-xs font-medium">{stage.name}</p>
                  <p className="text-lg font-bold">{usersByStage[stage.id] || 0}</p>
                </div>
                {index < 5 && (
                  <ArrowRight className="h-5 w-5 text-muted-foreground mx-2" />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 快速統計 */}
      <div className="grid grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">總好友數</p>
                <p className="text-2xl font-bold">{stats?.stats?.total_friends || 0}</p>
              </div>
              <Users className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">待邀請</p>
                <p className="text-2xl font-bold">{readyUsers.length}</p>
              </div>
              <Target className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">已邀請</p>
                <p className="text-2xl font-bold">{stats?.stats?.invites_sent || 0}</p>
              </div>
              <Send className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">已進群</p>
                <p className="text-2xl font-bold">{usersByStage["joined_group"] || 0}</p>
              </div>
              <Check className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">轉化率</p>
                <p className="text-2xl font-bold">{stats?.stats?.overall_conversion || 0}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 主要內容 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">總覽</TabsTrigger>
          <TabsTrigger value="users">用戶列表</TabsTrigger>
          <TabsTrigger value="ready">待邀請</TabsTrigger>
          <TabsTrigger value="config">配置</TabsTrigger>
        </TabsList>

        {/* 總覽 */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {/* 轉化漏斗 */}
            <Card>
              <CardHeader>
                <CardTitle>轉化漏斗</CardTitle>
                <CardDescription>各階段用戶分布</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {stats?.funnel?.map((stage: any, index: number) => {
                    const maxCount = Math.max(...(stats?.funnel?.map((s: any) => s.count) || [1]))
                    const percentage = maxCount > 0 ? (stage.count / maxCount) * 100 : 0
                    return (
                      <div key={index} className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>{stage.stage}</span>
                          <span className="text-muted-foreground">{stage.count} 人</span>
                        </div>
                        <Progress value={percentage} className="h-2" />
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>

            {/* 流程說明 */}
            <Card>
              <CardHeader>
                <CardTitle>自動轉化流程</CardTitle>
                <CardDescription>用戶添加好友後的自動處理流程</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">1</div>
                    <div>
                      <h4 className="font-medium">自動接受好友</h4>
                      <p className="text-sm text-muted-foreground">用戶發送好友請求，AI 自動接受</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">2</div>
                    <div>
                      <h4 className="font-medium">自動問候</h4>
                      <p className="text-sm text-muted-foreground">{config.greeting_delay_seconds}秒後發送問候消息</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-yellow-100 flex items-center justify-center">3</div>
                    <div>
                      <h4 className="font-medium">持續聊天培養</h4>
                      <p className="text-sm text-muted-foreground">每天主動發送 {config.daily_message_limit} 條消息</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center">4</div>
                    <div>
                      <h4 className="font-medium">話題進階</h4>
                      <p className="text-sm text-muted-foreground">日常→興趣→娛樂→遊戲→紅包</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">5</div>
                    <div>
                      <h4 className="font-medium">{config.invite_after_days} 天後邀請進群</h4>
                      <p className="text-sm text-muted-foreground">滿足 {config.min_messages_before_invite} 條消息後自動邀請</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 用戶列表 */}
        <TabsContent value="users" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>私聊用戶</CardTitle>
              <CardDescription>所有添加 AI 好友的用戶</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="space-y-2">
                  {users.length > 0 ? users.map((user: any) => (
                    <div key={user.user_id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                          {STAGES.find(s => s.id === user.stage)?.icon || "👤"}
                        </div>
                        <div>
                          <h4 className="font-medium">
                            {user.username || user.first_name || `用戶 ${user.user_id}`}
                          </h4>
                          <p className="text-sm text-muted-foreground">
                            ID: {user.user_id} · 消息: {user.message_count || 0} 條
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">
                          {STAGES.find(s => s.id === user.stage)?.name || user.stage}
                        </Badge>
                        {user.stage === "ready_to_invite" && (
                          <Button size="sm" onClick={() => inviteUser(user.user_id)}>
                            邀請進群
                          </Button>
                        )}
                      </div>
                    </div>
                  )) : (
                    <p className="text-center text-muted-foreground py-8">暫無用戶數據</p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 待邀請 */}
        <TabsContent value="ready" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>準備邀請的用戶</CardTitle>
                  <CardDescription>已達到邀請條件的用戶</CardDescription>
                </div>
                <Button onClick={batchInvite} disabled={loading || readyUsers.length === 0}>
                  {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Send className="h-4 w-4 mr-2" />}
                  批量邀請 ({readyUsers.length})
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-80">
                <div className="space-y-2">
                  {readyUsers.length > 0 ? readyUsers.map((user: any) => (
                    <div key={user.user_id} className="flex items-center justify-between p-3 border rounded-lg bg-purple-50">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-purple-200 flex items-center justify-center">
                          🎯
                        </div>
                        <div>
                          <h4 className="font-medium">
                            {user.username || user.first_name || `用戶 ${user.user_id}`}
                          </h4>
                          <p className="text-sm text-muted-foreground">
                            {user.ready_reason}
                          </p>
                        </div>
                      </div>
                      <Button size="sm" onClick={() => inviteUser(user.user_id)}>
                        <Send className="h-4 w-4 mr-1" />
                        邀請
                      </Button>
                    </div>
                  )) : (
                    <p className="text-center text-muted-foreground py-8">
                      暫無準備好的用戶
                      <br />
                      <span className="text-sm">需要添加好友 {config.invite_after_days} 天且交流 {config.min_messages_before_invite} 條消息</span>
                    </p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 配置 */}
        <TabsContent value="config" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>基本配置</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>啟用私聊轉化</Label>
                  <Switch 
                    checked={config.enabled}
                    onCheckedChange={(checked) => setConfig({...config, enabled: checked})}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>自動接受好友</Label>
                  <Switch 
                    checked={config.auto_accept_friend}
                    onCheckedChange={(checked) => setConfig({...config, auto_accept_friend: checked})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>問候延遲（秒）</Label>
                  <Input 
                    type="number"
                    value={config.greeting_delay_seconds}
                    onChange={(e) => setConfig({...config, greeting_delay_seconds: parseInt(e.target.value)})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>每日消息上限</Label>
                  <Input 
                    type="number"
                    value={config.daily_message_limit}
                    onChange={(e) => setConfig({...config, daily_message_limit: parseInt(e.target.value)})}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>邀請配置</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>幾天後邀請進群</Label>
                  <Input 
                    type="number"
                    step="0.5"
                    value={config.invite_after_days}
                    onChange={(e) => setConfig({...config, invite_after_days: parseFloat(e.target.value)})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>邀請前最少消息數</Label>
                  <Input 
                    type="number"
                    value={config.min_messages_before_invite}
                    onChange={(e) => setConfig({...config, min_messages_before_invite: parseInt(e.target.value)})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>目標群組</Label>
                  <div className="flex gap-2">
                    <Input 
                      placeholder="群組 ID"
                      value={newGroupId}
                      onChange={(e) => setNewGroupId(e.target.value)}
                    />
                    <Button onClick={addTargetGroup}>添加</Button>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {config.target_group_ids.map(gid => (
                      <Badge key={gid} variant="secondary">
                        {gid}
                        <button 
                          className="ml-1 hover:text-destructive"
                          onClick={() => setConfig({
                            ...config,
                            target_group_ids: config.target_group_ids.filter(g => g !== gid)
                          })}
                        >×</button>
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>邀請話術</Label>
                  <Textarea 
                    value={config.invite_message_template}
                    onChange={(e) => setConfig({...config, invite_message_template: e.target.value})}
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          <Button onClick={updateConfig} disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            保存配置
          </Button>
        </TabsContent>
      </Tabs>
    </div>
  )
}
