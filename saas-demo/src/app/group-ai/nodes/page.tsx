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
  Zap, Wifi, WifiOff, MessageSquare, Gift, Loader2, Plus
} from "lucide-react"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://jblt.usdt2026.cc/api/v1"

interface Worker {
  status: string
  account_count: number
  last_heartbeat: string
  accounts: any[]
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

  const fetchWorkers = async () => {
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE.replace('/api/v1', '')}/api/workers/`)
      const data = await res.json()
      setWorkers(data.workers || {})
    } catch (error) {
      console.error("獲取節點失敗:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWorkers()
    const interval = setInterval(fetchWorkers, 10000)
    return () => clearInterval(interval)
  }, [])

  const sendCommand = async (computerId: string, action: string, params: any = {}) => {
    try {
      const res = await fetch(`${API_BASE.replace('/api/v1', '')}/api/workers/${computerId}/commands`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, params }),
      })
      const data = await res.json()
      return data.success
    } catch (error) {
      console.error("發送命令失敗:", error)
      return false
    }
  }

  const broadcastCommand = async (action: string, params: any = {}) => {
    try {
      const res = await fetch(`${API_BASE.replace('/api/v1', '')}/api/workers/broadcast`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, params }),
      })
      const data = await res.json()
      if (data.success) {
        toast({ title: "成功", description: `命令已廣播到所有節點` })
      }
      return data.success
    } catch (error) {
      toast({ title: "錯誤", description: "廣播命令失敗", variant: "destructive" })
      return false
    }
  }

  const handleCreateGroup = async () => {
    if (!groupTitle || !selectedCreator) {
      toast({ title: "錯誤", description: "請填寫群組名稱並選擇創建者", variant: "destructive" })
      return
    }
    setLoading(true)
    const [computerId, phone] = selectedCreator.split(":")
    const success = await sendCommand(computerId, "create_group", {
      creator_phone: phone,
      title: groupTitle,
      description: "AI 自動聊天群組",
    })
    if (success) {
      toast({ title: "成功", description: "創建群組命令已發送" })
      setGroupTitle("")
      setSelectedCreator("")
    } else {
      toast({ title: "失敗", description: "發送命令失敗", variant: "destructive" })
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
  const localNodes = workerList.filter(([id]) => !id.startsWith("server_"))
  const serverNodes = workerList.filter(([id]) => id.startsWith("server_"))
  const onlineNodes = workerList.filter(([, w]) => w.status === "online").length
  const totalAccounts = workerList.reduce((sum, [, w]) => sum + (w.accounts?.length || 0), 0)

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
            節點管理
          </h1>
          <p className="text-sm text-muted-foreground">管理本地電腦和遠程服務器</p>
        </div>
        <Button onClick={fetchWorkers} variant="outline" size="sm" disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          刷新
        </Button>
      </div>

      {/* 統計 + 創建群組 */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card className="md:col-span-1">
          <CardContent className="pt-4">
            <div className="text-2xl font-bold">{workerList.length}</div>
            <p className="text-xs text-muted-foreground">{onlineNodes} 在線</p>
            <p className="text-xs font-medium mt-1">總節點</p>
          </CardContent>
        </Card>
        <Card className="md:col-span-1">
          <CardContent className="pt-4">
            <div className="text-2xl font-bold flex items-center gap-1">
              <Laptop className="h-4 w-4 text-blue-500" />
              {localNodes.length}
            </div>
            <p className="text-xs text-muted-foreground">{localNodes.filter(([,w]) => w.status === "online").length} 在線</p>
            <p className="text-xs font-medium mt-1">本地電腦</p>
          </CardContent>
        </Card>
        <Card className="md:col-span-1">
          <CardContent className="pt-4">
            <div className="text-2xl font-bold flex items-center gap-1">
              <Cloud className="h-4 w-4 text-purple-500" />
              {serverNodes.length}
            </div>
            <p className="text-xs text-muted-foreground">{serverNodes.filter(([,w]) => w.status === "online").length} 在線</p>
            <p className="text-xs font-medium mt-1">服務器</p>
          </CardContent>
        </Card>
        <Card className="md:col-span-1">
          <CardContent className="pt-4">
            <div className="text-2xl font-bold flex items-center gap-1">
              <Users className="h-4 w-4 text-green-500" />
              {totalAccounts}
            </div>
            <p className="text-xs text-muted-foreground">分布 {onlineNodes} 節點</p>
            <p className="text-xs font-medium mt-1">總賬號</p>
          </CardContent>
        </Card>
        {/* 快速創建群組 */}
        <Card className="md:col-span-1 border-blue-500/30">
          <CardContent className="pt-4 space-y-2">
            <Input
              value={groupTitle}
              onChange={(e) => setGroupTitle(e.target.value)}
              placeholder="群組名稱"
              className="h-8 text-sm"
            />
            <Select value={selectedCreator} onValueChange={setSelectedCreator}>
              <SelectTrigger className="h-8 text-xs">
                <SelectValue placeholder="選擇創建者" />
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
              創建群組
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* 自動化控制 - 緊湊版 */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Zap className="h-4 w-4 text-yellow-500" />
              自動化控制
            </CardTitle>
            <div className="flex gap-2">
              <Button onClick={handleStartAutoChat} size="sm" className="h-7 bg-green-600 hover:bg-green-700">
                <Play className="mr-1 h-3 w-3" /> 啟動
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
              <Label className="text-xs whitespace-nowrap">聊天間隔</Label>
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
              <Label className="text-xs whitespace-nowrap">紅包間隔</Label>
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
                <Label className="text-xs">紅包</Label>
              </div>
            </div>
            <Button onClick={handleUpdateConfig} size="sm" variant="outline" className="h-7">
              應用配置
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 節點列表 */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">節點列表</CardTitle>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="h-7">
                <TabsTrigger value="all" className="text-xs h-6 px-2">全部 ({workerList.length})</TabsTrigger>
                <TabsTrigger value="local" className="text-xs h-6 px-2">
                  <Laptop className="mr-1 h-3 w-3" />本地 ({localNodes.length})
                </TabsTrigger>
                <TabsTrigger value="server" className="text-xs h-6 px-2">
                  <Cloud className="mr-1 h-3 w-3" />服務器 ({serverNodes.length})
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {filteredNodes.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-sm">暫無節點</div>
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
                        最後心跳: {worker.last_heartbeat ? new Date(worker.last_heartbeat).toLocaleTimeString() : "N/A"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={worker.status === "online" ? "default" : "destructive"} className={`text-xs ${worker.status === "online" ? "bg-green-500" : ""}`}>
                        {worker.status === "online" ? <Wifi className="mr-1 h-3 w-3" /> : <WifiOff className="mr-1 h-3 w-3" />}
                        {worker.status === "online" ? "在線" : "離線"}
                      </Badge>
                      <Badge variant="outline" className="text-xs">{worker.accounts?.length || 0} 賬號</Badge>
                    </div>
                  </div>
                  {worker.accounts && worker.accounts.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {worker.accounts.map((acc: any, idx: number) => (
                        <div key={idx} className="flex items-center gap-1 px-2 py-1 bg-muted/50 rounded text-xs">
                          <span className="font-medium">{acc.first_name || acc.phone}</span>
                          {acc.role_name && <span className="text-muted-foreground">({acc.role_name})</span>}
                          <Badge variant="secondary" className="text-[10px] px-1 py-0 h-4">{acc.status || "online"}</Badge>
                        </div>
                      ))}
                    </div>
                  )}
                  {/* 節點操作 */}
                  <div className="flex gap-2 mt-2 pt-2 border-t">
                    <Button 
                      size="sm" 
                      variant="outline"
                      className="h-6 text-xs"
                      onClick={() => sendCommand(nodeId, "start_auto_chat", { group_id: 0 })}
                    >
                      <Play className="mr-1 h-3 w-3" /> 啟動聊天
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      className="h-6 text-xs"
                      onClick={() => sendCommand(nodeId, "stop_auto_chat", {})}
                    >
                      <Square className="mr-1 h-3 w-3" /> 停止
                    </Button>
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
