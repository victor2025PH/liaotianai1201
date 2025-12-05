"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"
import { 
  Monitor, Play, Square, RefreshCw, Users, Laptop, Cloud, 
  Zap, Wifi, WifiOff, MessageSquare, Gift, Loader2, Plus,
  Trash2, AlertTriangle, CheckCircle2, Search
} from "lucide-react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"

import { getApiBaseUrl } from "@/lib/api/config"
import { useI18n } from "@/lib/i18n"

const API_BASE = getApiBaseUrl()

interface Worker {
  status: string
  account_count: number
  last_heartbeat: string
  accounts: any[]
  metadata?: {
    total_friends?: number
    total_groups?: number
    new_contacts_24h?: number
    [key: string]: any
  }
}

interface AutomationConfig {
  chat_interval_min: number
  chat_interval_max: number
  auto_chat_enabled: boolean
  redpacket_enabled: boolean
  redpacket_interval: number
}

export default function NodesPage() {
  const { toast } = useToast()
  const { t } = useI18n()
  const [workers, setWorkers] = useState<Record<string, Worker>>({})
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState("all")
  const [groupTitle, setGroupTitle] = useState("")
  const [selectedCreator, setSelectedCreator] = useState("")
  
  const [config, setConfig] = useState<AutomationConfig>({
    chat_interval_min: 30,
    chat_interval_max: 120,
    auto_chat_enabled: true,
    redpacket_enabled: true,
    redpacket_interval: 300,
  })
  
  // 重複帳號檢測
  const [duplicates, setDuplicates] = useState<any[]>([])
  const [showDuplicateAlert, setShowDuplicateAlert] = useState(false)

  const fetchWorkers = async () => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/workers/`)
      if (!res.ok) {
        if (res.status === 404) {
          // 端点不存在，使用空数据
          console.warn("Workers API 端点不存在，使用空数据")
          setWorkers({})
          return
        }
        if (res.status === 401) {
          console.warn("未授权，可能需要登录")
          setWorkers({})
          return
        }
        throw new Error(`HTTP ${res.status}`)
      }
      const data = await res.json()
      setWorkers(data.workers || {})
    } catch (error) {
      console.warn("獲取节点失败（端点可能未实现）:", error)
      setWorkers({})
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWorkers()
    checkDuplicates()
    // 优化：延長輪詢間隔到 30 秒
    const interval = setInterval(fetchWorkers, 30000)
    return () => clearInterval(interval)
  }, [])

  // 檢測重複帳號
  const checkDuplicates = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/workers/check/duplicates`)
      if (res.ok) {
        const data = await res.json()
        if (data.has_duplicates) {
          setDuplicates(data.duplicates || [])
          setShowDuplicateAlert(true)
        }
      }
    } catch (error) {
      console.warn("檢測重複帳號失敗:", error)
    }
  }

  // 刪除節點
  const deleteNode = async (nodeId: string) => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/workers/${nodeId}`, {
        method: "DELETE"
      })
      if (res.ok) {
        toast({ title: "✅ 節點已刪除", description: `${nodeId} 已從列表中移除` })
        fetchWorkers()
      } else {
        const data = await res.json()
        toast({ title: "❌ 刪除失敗", description: data.detail, variant: "destructive" })
      }
    } catch (error) {
      toast({ title: "❌ 刪除失敗", description: String(error), variant: "destructive" })
    }
  }

  // 檢測節點狀態
  const checkNodesStatus = async () => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/workers/check/status`, {
        method: "POST"
      })
      if (res.ok) {
        const data = await res.json()
        toast({ 
          title: "節點狀態檢測完成", 
          description: `在線: ${data.summary.online} | 離線: ${data.summary.offline} | 錯誤: ${data.summary.error}` 
        })
        fetchWorkers()
      }
    } catch (error) {
      toast({ title: "❌ 檢測失敗", description: String(error), variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  const sendCommand = async (computerId: string, action: string, params: any = {}) => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/workers/${computerId}/commands`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, params }),
      })
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      const data = await res.json()
      return data.success
    } catch (error) {
      console.error("發送命令失败:", error)
      toast({ title: "错误", description: "發送命令失败", variant: "destructive" })
      return false
    }
  }

  const broadcastCommand = async (action: string, params: any = {}) => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/workers/broadcast`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, params }),
      })
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      const data = await res.json()
      if (data.success) {
        toast({ title: "成功", description: `命令已廣播到 ${data.nodes_count || 0} 个节点` })
      }
      return data.success
    } catch (error) {
      toast({ title: "错误", description: "廣播命令失败", variant: "destructive" })
      return false
    }
  }

  const handleCreateGroup = async () => {
    if (!groupTitle || !selectedCreator) {
      toast({ title: "错误", description: "請填寫群组名称並选择创建者", variant: "destructive" })
      return
    }
    setLoading(true)
    const [computerId, phone] = selectedCreator.split(":")
    const success = await sendCommand(computerId, "create_group", {
      creator_phone: phone,
      title: groupTitle,
      description: "AI 自动聊天群组",
    })
    if (success) {
      toast({ title: "成功", description: "创建群组命令已發送" })
      setGroupTitle("")
      setSelectedCreator("")
    } else {
      toast({ title: "失败", description: "發送命令失败", variant: "destructive" })
    }
    setLoading(false)
  }

  const handleStartAutoChat = () => broadcastCommand("start_auto_chat", { group_id: 0 })
  const handleStopAutoChat = () => broadcastCommand("stop_auto_chat", {})
  const handleUpdateConfig = () => broadcastCommand("set_config", {
    chat_interval_min: config.chat_interval_min,
    chat_interval_max: config.chat_interval_max,
    auto_chat_enabled: config.auto_chat_enabled,
    redpacket_enabled: config.redpacket_enabled,
    redpacket_interval: config.redpacket_interval,
  })

  // 統計
  const workerList = Object.entries(workers)
  // 识别本地电脑：不是以"server_"开头的都是本地电脑
  // 包括：computer_xxx, 计算机_xxx, computer-xxx 等格式
  const localNodes = workerList.filter(([id]) => {
    const lowerId = id.toLowerCase()
    return !lowerId.startsWith("server_") && !lowerId.startsWith("server-")
  })
  const serverNodes = workerList.filter(([id]) => {
    const lowerId = id.toLowerCase()
    return lowerId.startsWith("server_") || lowerId.startsWith("server-")
  })
  const onlineNodes = workerList.filter(([, w]) => w.status === "online").length
  const onlineLocalNodes = localNodes.filter(([, w]) => w.status === "online").length
  const onlineServerNodes = serverNodes.filter(([, w]) => w.status === "online").length
  const totalAccounts = workerList.reduce((sum, [, w]) => sum + (w.accounts?.length || 0), 0)
  const onlineAccounts = workerList.reduce((sum, [, w]) => {
    if (w.status === "online" && w.accounts) {
      return sum + w.accounts.filter((acc: any) => acc.status === "online").length
    }
    return sum
  }, 0)

  const filteredNodes = activeTab === "all" ? workerList 
    : activeTab === "local" ? localNodes 
    : serverNodes

  const allAccounts = workerList.flatMap(([computerId, worker]) =>
    (worker.accounts || []).map((acc: any) => ({
      ...acc,
      computerId,
      key: `${computerId}:${acc.phone}`,
    }))
  )

  return (
    <div className="container mx-auto py-6 space-y-4">
      {/* 標題 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Monitor className="h-6 w-6" />
            节点管理
          </h1>
          <p className="text-sm text-muted-foreground">管理本地电脑和远程服务器</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={checkNodesStatus} variant="outline" size="sm" disabled={loading}>
            <Search className="mr-2 h-4 w-4" />
            檢測狀態
          </Button>
          <Button onClick={checkDuplicates} variant="outline" size="sm" disabled={loading}>
            <AlertTriangle className="mr-2 h-4 w-4" />
            檢測重複
          </Button>
          <Button onClick={fetchWorkers} variant="outline" size="sm" disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>
      </div>

      {/* 重複帳號提醒 */}
      {showDuplicateAlert && duplicates.length > 0 && (
        <Card className="border-yellow-500 bg-yellow-500/10">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
                <span className="font-medium text-yellow-500">發現 {duplicates.length} 個重複帳號</span>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setShowDuplicateAlert(false)}>✕</Button>
            </div>
            <div className="mt-2 space-y-1 text-sm">
              {duplicates.slice(0, 5).map((dup, idx) => (
                <div key={idx} className="text-muted-foreground">
                  帳號 <span className="font-mono text-yellow-500">{dup.account_id}</span> 在 {dup.count} 個節點上重複：
                  <span className="font-mono ml-1">{dup.nodes.join(", ")}</span>
                </div>
              ))}
              {duplicates.length > 5 && (
                <div className="text-muted-foreground">還有 {duplicates.length - 5} 個重複帳號...</div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 統計 + 创建群组 */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card className="md:col-span-1">
          <CardContent className="pt-4">
            <div className="text-2xl font-bold">{workerList.length}</div>
            <p className="text-xs text-muted-foreground">{onlineNodes} {t.common.online}</p>
            <p className="text-xs font-medium mt-1">{t.nodes.totalNodes}</p>
          </CardContent>
        </Card>
        <Card className="md:col-span-1">
          <CardContent className="pt-4">
            <div className="text-2xl font-bold flex items-center gap-1">
              <Laptop className="h-4 w-4 text-blue-500" />
              {localNodes.length}
            </div>
            <p className="text-xs text-muted-foreground">{onlineLocalNodes} {t.common.online}</p>
            <p className="text-xs font-medium mt-1">{t.nodes.localComputers}</p>
          </CardContent>
        </Card>
        <Card className="md:col-span-1">
          <CardContent className="pt-4">
            <div className="text-2xl font-bold flex items-center gap-1">
              <Cloud className="h-4 w-4 text-purple-500" />
              {serverNodes.length}
            </div>
            <p className="text-xs text-muted-foreground">{onlineServerNodes} {t.common.online}</p>
            <p className="text-xs font-medium mt-1">{t.nodes.servers}</p>
          </CardContent>
        </Card>
        <Card className="md:col-span-1">
          <CardContent className="pt-4">
            <div className="text-2xl font-bold flex items-center gap-1">
              <Users className="h-4 w-4 text-green-500" />
              {totalAccounts}
            </div>
            <p className="text-xs text-muted-foreground">{onlineAccounts} {t.common.online} / {t.nodes.distributed} {onlineNodes} {t.nodes.totalNodes}</p>
            <p className="text-xs font-medium mt-1">{t.nodes.totalAccounts}</p>
          </CardContent>
        </Card>
        {/* 快速创建群组 */}
        <Card className="md:col-span-1 border-blue-500/30">
          <CardContent className="pt-4 space-y-2">
            <Input
              value={groupTitle}
              onChange={(e) => setGroupTitle(e.target.value)}
              placeholder="群组名称"
              className="h-8 text-sm"
            />
            <Select value={selectedCreator} onValueChange={setSelectedCreator}>
              <SelectTrigger className="h-8 text-xs">
                <SelectValue placeholder="选择创建者" />
              </SelectTrigger>
              <SelectContent>
                {allAccounts.map((acc) => (
                  <SelectItem key={acc.key} value={acc.key} className="text-xs">
                    {acc.first_name || acc.phone} ({acc.computerId})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button onClick={handleCreateGroup} disabled={loading} size="sm" className="w-full h-8">
              <Plus className="mr-1 h-3 w-3" />
              创建群组
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* 自动化控制 - 緊湊版 */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Zap className="h-4 w-4 text-yellow-500" />
              自动化控制
            </CardTitle>
            <div className="flex gap-2">
              <Button onClick={handleStartAutoChat} size="sm" className="h-7 bg-green-600 hover:bg-green-700">
                <Play className="mr-1 h-3 w-3" /> 启动
              </Button>
              <Button onClick={handleStopAutoChat} size="sm" variant="destructive" className="h-7">
                <Square className="mr-1 h-3 w-3" /> 停止
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0 pb-3">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <Label className="text-xs whitespace-nowrap">聊天间隔</Label>
              <Input
                type="number"
                value={config.chat_interval_min}
                onChange={(e) => setConfig({ ...config, chat_interval_min: parseInt(e.target.value) || 30 })}
                className="w-16 h-7 text-xs"
              />
              <span className="text-xs">-</span>
              <Input
                type="number"
                value={config.chat_interval_max}
                onChange={(e) => setConfig({ ...config, chat_interval_max: parseInt(e.target.value) || 120 })}
                className="w-16 h-7 text-xs"
              />
              <span className="text-xs text-muted-foreground">秒</span>
            </div>
            <div className="flex items-center gap-2">
              <Label className="text-xs whitespace-nowrap">红包间隔</Label>
              <Input
                type="number"
                value={config.redpacket_interval}
                onChange={(e) => setConfig({ ...config, redpacket_interval: parseInt(e.target.value) || 300 })}
                className="w-20 h-7 text-xs"
              />
              <span className="text-xs text-muted-foreground">秒</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1">
                <Switch
                  checked={config.auto_chat_enabled}
                  onCheckedChange={(v) => setConfig({ ...config, auto_chat_enabled: v })}
                  className="scale-75"
                />
                <Label className="text-xs">聊天</Label>
              </div>
              <div className="flex items-center gap-1">
                <Switch
                  checked={config.redpacket_enabled}
                  onCheckedChange={(v) => setConfig({ ...config, redpacket_enabled: v })}
                  className="scale-75"
                />
                <Label className="text-xs">红包</Label>
              </div>
            </div>
            <Button onClick={handleUpdateConfig} size="sm" variant="outline" className="h-7">
              应用配置
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 节点列表 */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">节点列表</CardTitle>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="h-7">
                <TabsTrigger value="all" className="text-xs h-6 px-2">全部 ({workerList.length})</TabsTrigger>
                <TabsTrigger value="local" className="text-xs h-6 px-2">
                  <Laptop className="mr-1 h-3 w-3" />本地 ({localNodes.length})
                </TabsTrigger>
                <TabsTrigger value="server" className="text-xs h-6 px-2">
                  <Cloud className="mr-1 h-3 w-3" />服务器 ({serverNodes.length})
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {filteredNodes.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-sm">暫无节点</div>
          ) : (
            <div className="space-y-3">
              {filteredNodes.map(([nodeId, worker]) => (
                <div key={nodeId} className="border rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {nodeId.startsWith("server_") ? (
                        <Cloud className="h-4 w-4 text-purple-500" />
                      ) : (
                        <Laptop className="h-4 w-4 text-blue-500" />
                      )}
                      <span className="font-medium">{nodeId}</span>
                      <span className="text-xs text-muted-foreground">
                        最后心跳: {worker.last_heartbeat ? new Date(worker.last_heartbeat).toLocaleTimeString() : "N/A"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={worker.status === "online" ? "default" : "destructive"} className={`text-xs ${worker.status === "online" ? "bg-green-500" : ""}`}>
                        {worker.status === "online" ? <Wifi className="mr-1 h-3 w-3" /> : <WifiOff className="mr-1 h-3 w-3" />}
                        {worker.status === "online" ? "在線" : "离线"}
                      </Badge>
                      <Badge variant="outline" className="text-xs">{worker.accounts?.length || 0} 账号</Badge>
                    </div>
                  </div>
                  {/* 節點統計摘要 */}
                  {worker.metadata && ((worker.metadata?.total_friends ?? 0) > 0 || (worker.metadata?.total_groups ?? 0) > 0) && (
                    <div className="flex gap-4 mb-2 text-xs text-muted-foreground">
                      <span>👥 好友: {worker.metadata?.total_friends ?? 0}</span>
                      <span>💬 群組: {worker.metadata?.total_groups ?? 0}</span>
                      {(worker.metadata?.new_contacts_24h ?? 0) > 0 && (
                        <span className="text-green-500">📈 今日+{worker.metadata?.new_contacts_24h ?? 0}</span>
                      )}
                    </div>
                  )}
                  
                  {/* 帳號列表 */}
                  {worker.accounts && worker.accounts.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {worker.accounts.map((acc: any, idx: number) => (
                        <div key={idx} className="flex items-center gap-2 px-3 py-2 bg-muted/50 rounded-lg text-xs border hover:border-blue-500/50 transition-colors">
                          <div className="flex flex-col min-w-0">
                            <span className="font-medium truncate">
                              {acc.excel_name || acc.name || acc.username || acc.phone || acc.account_id || `Account ${idx + 1}`}
                            </span>
                            {/* Telegram ID - 重要！紅包系統需要 */}
                            {(acc.user_id || acc.tg_id) && (
                              <span className="text-[10px] font-mono text-purple-400">
                                🆔 {acc.user_id || acc.tg_id}
                              </span>
                            )}
                            {(acc.phone || acc.username) && (
                              <span className="text-[10px] text-muted-foreground truncate">
                                {acc.phone && `📱 ${acc.phone}`}
                                {acc.phone && acc.username && " · "}
                                {acc.username && `@${acc.username}`}
                              </span>
                            )}
                            {/* Excel 分組和備註 */}
                            {(acc.excel_group || acc.excel_remark) && (
                              <span className="text-[10px] text-blue-400 truncate">
                                {acc.excel_group && `📁 ${acc.excel_group}`}
                                {acc.excel_group && acc.excel_remark && " · "}
                                {acc.excel_remark && `📝 ${acc.excel_remark}`}
                              </span>
                            )}
                            {/* 帳號統計 */}
                            {(acc.friends_count !== undefined || acc.groups_count !== undefined) && (
                              <div className="flex gap-2 text-[10px] text-muted-foreground mt-0.5">
                                {acc.friends_count !== undefined && (
                                  <span>👥 {acc.friends_count}</span>
                                )}
                                {acc.groups_count !== undefined && (
                                  <span>💬 {acc.groups_count}</span>
                                )}
                                {acc.channels_count !== undefined && acc.channels_count > 0 && (
                                  <span>📢 {acc.channels_count}</span>
                                )}
                                {acc.new_contacts_24h !== undefined && acc.new_contacts_24h > 0 && (
                                  <span className="text-green-500">+{acc.new_contacts_24h}</span>
                                )}
                              </div>
                            )}
                          </div>
                          <div className="flex flex-col gap-1">
                            {/* Telegram ID 徽章 */}
                            {(acc.user_id || acc.tg_id) && (
                              <Badge variant="outline" className="text-[10px] px-1 py-0 h-4 bg-purple-500/10 text-purple-400 font-mono">
                                TG: {acc.user_id || acc.tg_id}
                              </Badge>
                            )}
                            {acc.excel_group && (
                              <Badge variant="outline" className="text-[10px] px-1 py-0 h-4 bg-blue-500/10">{acc.excel_group}</Badge>
                            )}
                            {acc.role_name && (
                              <Badge variant="outline" className="text-[10px] px-1 py-0 h-4">{acc.role_name}</Badge>
                            )}
                            <Badge 
                              variant={acc.status === "available" ? "default" : "secondary"} 
                              className={`text-[10px] px-1 py-0 h-4 ${acc.status === "available" ? "bg-green-500" : ""}`}
                            >
                              {acc.status === "available" ? "可用" : acc.status || "未知"}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  {/* 节点操作 */}
                  <div className="flex flex-wrap gap-2 mt-2 pt-2 border-t">
                    <Button 
                      size="sm" 
                      variant="outline"
                      className="h-6 text-xs"
                      onClick={() => sendCommand(nodeId, "start_auto_chat", { group_id: 0 })}
                    >
                      <Play className="mr-1 h-3 w-3" /> 启动聊天
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      className="h-6 text-xs"
                      onClick={() => sendCommand(nodeId, "stop_auto_chat", {})}
                    >
                      <Square className="mr-1 h-3 w-3" /> 停止
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      className="h-6 text-xs text-blue-500 border-blue-500/50"
                      onClick={() => {
                        sendCommand(nodeId, "update_excel", {})
                        toast({ title: "已發送更新 Excel 命令", description: "帳號詳情將自動填入 Excel 文件" })
                      }}
                    >
                      <RefreshCw className="mr-1 h-3 w-3" /> 更新Excel
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      className="h-6 text-xs text-green-500 border-green-500/50"
                      onClick={() => {
                        sendCommand(nodeId, "export_accounts", {})
                        toast({ title: "已發送導出命令", description: "帳號將導出到 sessions 目錄的新 Excel 文件" })
                      }}
                    >
                      <MessageSquare className="mr-1 h-3 w-3" /> 導出帳號
                    </Button>
                    {/* 刪除節點按鈕 */}
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button 
                          size="sm" 
                          variant="outline"
                          className="h-6 text-xs text-red-500 border-red-500/50 hover:bg-red-500/10"
                        >
                          <Trash2 className="mr-1 h-3 w-3" /> 刪除
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>確認刪除節點</AlertDialogTitle>
                          <AlertDialogDescription>
                            確定要刪除節點 <span className="font-mono font-bold">{nodeId}</span> 嗎？
                            <br />
                            此操作會將節點從列表中移除，但不會影響實際運行的 Worker 程序。
                            {worker.status === "online" && (
                              <span className="text-yellow-500 block mt-2">
                                ⚠️ 此節點目前在線，刪除後如果 Worker 程序仍在運行，節點會在下次心跳時重新出現。
                              </span>
                            )}
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>取消</AlertDialogCancel>
                          <AlertDialogAction 
                            onClick={() => deleteNode(nodeId)}
                            className="bg-red-500 hover:bg-red-600"
                          >
                            確認刪除
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
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
