"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"
import { Loader2, Play, Square, Users, MessageSquare, Gift, RefreshCw, Zap } from "lucide-react"
import { getApiBaseUrl } from "@/lib/api/config"

interface Worker {
  status: string
  account_count: number
  last_heartbeat: string
  accounts: any[]
}

interface GroupAutomationConfig {
  chat_interval_min: number
  chat_interval_max: number
  auto_chat_enabled: boolean
  redpacket_enabled: boolean
  redpacket_interval: number
}

const API_BASE = getApiBaseUrl()

export default function GroupAutomationPage() {
  const { toast } = useToast()
  const [workers, setWorkers] = useState<Record<string, Worker>>({})
  const [loading, setLoading] = useState(false)
  const [groupTitle, setGroupTitle] = useState("")
  const [selectedCreator, setSelectedCreator] = useState("")
  const [config, setConfig] = useState<GroupAutomationConfig>({
    chat_interval_min: 30,
    chat_interval_max: 120,
    auto_chat_enabled: true,
    redpacket_enabled: true,
    redpacket_interval: 300,
  })

  const fetchWorkers = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/workers/`)
      if (!res.ok) {
        if (res.status === 404) {
          console.warn("Workers API 端点不存在，使用空数据")
          setWorkers({})
          return
        }
        throw new Error(`HTTP ${res.status}`)
      }
      const data = await res.json()
      setWorkers(data.workers || {})
    } catch (error) {
      console.warn("获取节点失败（端点可能未实现）:", error)
      setWorkers({})
    }
  }

  useEffect(() => {
    fetchWorkers()
    const interval = setInterval(fetchWorkers, 30000) // 優化：減少 CPU 負載，延長到 30 秒
    return () => clearInterval(interval)
  }, [])

  const sendCommand = async (computerId: string, action: string, params: any) => {
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
      console.error("发送命令失败:", error)
      toast({ title: "错误", description: "发送命令失败", variant: "destructive" })
      return false
    }
  }

  const broadcastCommand = async (action: string, params: any) => {
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
        toast({ title: "成功", description: `命令已广播到 ${data.nodes_count || 0} 个节点` })
      }
      return data.success
    } catch (error) {
      console.error("广播命令失败:", error)
      toast({ title: "错误", description: "广播命令失败", variant: "destructive" })
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
    } else {
      toast({ title: "失敗", description: "發送命令失敗", variant: "destructive" })
    }
    setLoading(false)
  }

  const handleStartAutoChat = async () => {
    setLoading(true)
    const success = await broadcastCommand("start_auto_chat", { group_id: 0 })
    if (success) {
      toast({ title: "成功", description: "自動聊天已啟動" })
    }
    setLoading(false)
  }

  const handleStopAutoChat = async () => {
    setLoading(true)
    const success = await broadcastCommand("stop_auto_chat", {})
    if (success) {
      toast({ title: "成功", description: "自動聊天已停止" })
    }
    setLoading(false)
  }

  const handleUpdateConfig = async () => {
    setLoading(true)
    const success = await broadcastCommand("set_config", config)
    if (success) {
      toast({ title: "成功", description: "配置已更新" })
    }
    setLoading(false)
  }

  const allAccounts = Object.entries(workers).flatMap(([computerId, worker]) =>
    (worker.accounts || []).map((acc: any) => ({
      ...acc,
      computerId,
      key: `${computerId}:${acc.phone}`,
    }))
  )

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Zap className="h-8 w-8 text-yellow-500" />
            群組自動化管理
          </h1>
          <p className="text-muted-foreground">自動創建群組、AI 聊天、紅包遊戲</p>
        </div>
        <Button variant="outline" onClick={fetchWorkers}>
          <RefreshCw className="mr-2 h-4 w-4" />
          刷新
        </Button>
      </div>

      {/* Worker 狀態 */}
      <div className="grid gap-4 md:grid-cols-2">
        {Object.entries(workers).map(([computerId, worker]) => (
          <Card key={computerId} className="border-2 border-primary/20">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                {computerId}
                <span className={`ml-auto px-2 py-1 rounded text-xs ${
                  worker.status === "online" ? "bg-green-500/20 text-green-500" : "bg-red-500/20 text-red-500"
                }`}>
                  {worker.status === "online" ? "在線" : "離線"}
                </span>
              </CardTitle>
              <CardDescription>
                {worker.account_count} 個賬號 | 最後心跳: {new Date(worker.last_heartbeat).toLocaleTimeString()}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {(worker.accounts || []).map((acc: any, idx: number) => (
                  <span key={idx} className="px-3 py-1 bg-primary/10 rounded-full text-sm font-medium">
                    {acc.first_name || acc.phone}
                    <span className="text-muted-foreground ml-1">({acc.role_name})</span>
                  </span>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 創建群組 */}
      <Card className="border-2 border-blue-500/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5 text-blue-500" />
            創建新群組
          </CardTitle>
          <CardDescription>選擇一個賬號創建群組，所有 AI 賬號將自動加入並開始互動</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>群組名稱</Label>
              <Input
                value={groupTitle}
                onChange={(e) => setGroupTitle(e.target.value)}
                placeholder="例如: 紅包遊戲群"
                className="text-lg"
              />
            </div>
            <div className="space-y-2">
              <Label>創建者賬號</Label>
              <Select value={selectedCreator} onValueChange={setSelectedCreator}>
                <SelectTrigger className="text-lg">
                  <SelectValue placeholder="選擇創建群組的賬號" />
                </SelectTrigger>
                <SelectContent>
                  {allAccounts.map((acc) => (
                    <SelectItem key={acc.key} value={acc.key}>
                      <span className="flex items-center gap-2">
                        <span>{acc.first_name || acc.phone}</span>
                        <span className="text-muted-foreground">({acc.role_name})</span>
                        <span className="text-xs bg-primary/10 px-2 py-0.5 rounded">{acc.computerId}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <Button onClick={handleCreateGroup} disabled={loading} size="lg" className="w-full md:w-auto">
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Users className="mr-2 h-4 w-4" />
            創建群組並開始自動聊天
          </Button>
        </CardContent>
      </Card>

      {/* 自動聊天控制 */}
      <Card className="border-2 border-green-500/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-green-500" />
            自動聊天控制
          </CardTitle>
          <CardDescription>6 個 AI 角色將在群組中自動聊天互動，有真實用戶加入時會陪聊</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex flex-wrap gap-4">
            <Button onClick={handleStartAutoChat} disabled={loading} size="lg" className="bg-green-600 hover:bg-green-700">
              <Play className="mr-2 h-5 w-5" />
              啟動自動聊天
            </Button>
            <Button onClick={handleStopAutoChat} disabled={loading} size="lg" variant="destructive">
              <Square className="mr-2 h-5 w-5" />
              停止自動聊天
            </Button>
          </div>
          
          <div className="grid gap-6 md:grid-cols-3">
            <div className="space-y-2">
              <Label className="text-sm font-medium">最小聊天間隔 (秒)</Label>
              <Input
                type="number"
                value={config.chat_interval_min}
                onChange={(e) => setConfig({ ...config, chat_interval_min: parseInt(e.target.value) || 30 })}
                className="text-lg"
              />
              <p className="text-xs text-muted-foreground">AI 發送消息的最小間隔時間</p>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">最大聊天間隔 (秒)</Label>
              <Input
                type="number"
                value={config.chat_interval_max}
                onChange={(e) => setConfig({ ...config, chat_interval_max: parseInt(e.target.value) || 120 })}
                className="text-lg"
              />
              <p className="text-xs text-muted-foreground">AI 發送消息的最大間隔時間</p>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">紅包間隔 (秒)</Label>
              <Input
                type="number"
                value={config.redpacket_interval}
                onChange={(e) => setConfig({ ...config, redpacket_interval: parseInt(e.target.value) || 300 })}
                className="text-lg"
              />
              <p className="text-xs text-muted-foreground">自動發送紅包的間隔時間</p>
            </div>
          </div>

          <div className="flex items-center gap-8 p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center space-x-3">
              <Switch
                checked={Boolean(config.auto_chat_enabled ?? false)}
                onCheckedChange={(v) => setConfig({ ...config, auto_chat_enabled: Boolean(v) })}
              />
              <div>
                <Label className="font-medium">自動聊天</Label>
                <p className="text-xs text-muted-foreground">AI 之間自動對話互動</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Switch
                checked={Boolean(config.redpacket_enabled ?? false)}
                onCheckedChange={(v) => setConfig({ ...config, redpacket_enabled: Boolean(v) })}
              />
              <div>
                <Label className="font-medium">紅包遊戲</Label>
                <p className="text-xs text-muted-foreground">自動發送和搶紅包</p>
              </div>
            </div>
          </div>

          <Button onClick={handleUpdateConfig} disabled={loading} size="lg">
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            應用配置
          </Button>
        </CardContent>
      </Card>

      {/* 紅包遊戲說明 */}
      <Card className="border-2 border-yellow-500/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Gift className="h-5 w-5 text-yellow-500" />
            紅包遊戲
          </CardTitle>
          <CardDescription>AI 會自動發送和搶紅包，營造熱鬧氛圍</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="p-4 bg-yellow-500/10 rounded-lg">
              <h4 className="font-medium mb-2">發紅包</h4>
              <p className="text-sm text-muted-foreground">AI 會定期發送隨機金額的紅包，吸引用戶參與互動</p>
            </div>
            <div className="p-4 bg-green-500/10 rounded-lg">
              <h4 className="font-medium mb-2">搶紅包</h4>
              <p className="text-sm text-muted-foreground">當有紅包時，AI 會模擬搶紅包行為，營造競爭氛圍</p>
            </div>
          </div>
          <p className="text-sm">
            <span className="font-medium">當前設置：</span>
            每 <span className="text-yellow-500 font-bold">{config.redpacket_interval}</span> 秒自動發送一次紅包
            {!config.redpacket_enabled && <span className="text-red-500 ml-2">(已禁用)</span>}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

