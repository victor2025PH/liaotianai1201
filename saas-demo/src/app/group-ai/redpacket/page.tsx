"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useToast } from "@/hooks/use-toast"
import { 
  Gift, Settings, Play, Square, RefreshCw, 
  TrendingUp, Users, Wallet, History, Zap
} from "lucide-react"

// 紅包遊戲配置接口（等待 API 文檔後完善）
interface RedpacketConfig {
  api_url: string
  api_key: string
  enabled: boolean
  auto_grab: boolean
  grab_delay_min: number
  grab_delay_max: number
  auto_send: boolean
  send_interval: number
  send_amount_min: number
  send_amount_max: number
}

interface GameStats {
  total_sent: number
  total_grabbed: number
  total_amount_sent: number
  total_amount_grabbed: number
  today_sent: number
  today_grabbed: number
}

export default function RedpacketPage() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [connected, setConnected] = useState(false)
  
  const [config, setConfig] = useState<RedpacketConfig>({
    api_url: "",
    api_key: "",
    enabled: false,
    auto_grab: true,
    grab_delay_min: 1,
    grab_delay_max: 5,
    auto_send: false,
    send_interval: 300,
    send_amount_min: 1,
    send_amount_max: 10,
  })

  const [stats, setStats] = useState<GameStats>({
    total_sent: 0,
    total_grabbed: 0,
    total_amount_sent: 0,
    total_amount_grabbed: 0,
    today_sent: 0,
    today_grabbed: 0,
  })

  // 獲取 API 基礎地址
  const getApiBase = () => {
    if (typeof window !== 'undefined') {
      return `${window.location.protocol}//${window.location.host}/api/v1`
    }
    return '/api/v1'
  }

  // 加載配置
  const loadConfig = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${getApiBase()}/redpacket/config`)
      if (res.ok) {
        const data = await res.json()
        if (data.success && data.data) {
          setConfig(prev => ({ ...prev, ...data.data }))
          setConnected(!!data.data.api_url)
        }
      }
    } catch (error) {
      console.error("加載配置失敗:", error)
    }
  }

  // 加載統計
  const loadStats = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${getApiBase()}/redpacket/stats`)
      if (res.ok) {
        const data = await res.json()
        if (data.success && data.data) {
          setStats(data.data)
          setConnected(data.data.connected)
        }
      }
    } catch (error) {
      console.error("加載統計失敗:", error)
    }
  }

  useEffect(() => {
    loadConfig()
    loadStats()
  }, [])

  const testConnection = async () => {
    setLoading(true)
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${getApiBase()}/redpacket/test-connection`, {
        method: "POST"
      })
      const data = await res.json()
      
      if (data.success) {
        setConnected(true)
        toast({ title: "✅ 連接成功", description: "紅包遊戲 API 連接正常" })
      } else {
        setConnected(false)
        toast({ title: "❌ 連接失敗", description: data.message || data.detail, variant: "destructive" })
      }
    } catch (error) {
      setConnected(false)
      toast({ title: "❌ 連接失敗", description: String(error), variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  const saveConfig = async () => {
    setLoading(true)
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${getApiBase()}/redpacket/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config)
      })
      const data = await res.json()
      
      if (data.success) {
        toast({ title: "✅ 配置已保存" })
      } else {
        toast({ title: "❌ 保存失敗", description: data.detail, variant: "destructive" })
      }
    } catch (error) {
      toast({ title: "❌ 保存失敗", description: String(error), variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 標題 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Gift className="h-6 w-6 text-red-500" />
            🧧 紅包遊戲系統
          </h1>
          <p className="text-sm text-muted-foreground">對接紅包遊戲 API，讓 AI 帳號參與紅包互動</p>
        </div>
        <Badge variant={connected ? "default" : "secondary"} className={connected ? "bg-green-500" : ""}>
          {connected ? "已連接" : "未連接"}
        </Badge>
      </div>

      {/* 統計卡片 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Gift className="h-4 w-4 text-red-500" />
              <span className="text-sm text-muted-foreground">今日發出</span>
            </div>
            <div className="text-2xl font-bold mt-1">{stats.today_sent}</div>
            <p className="text-xs text-muted-foreground">累計: {stats.total_sent}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Wallet className="h-4 w-4 text-green-500" />
              <span className="text-sm text-muted-foreground">今日搶到</span>
            </div>
            <div className="text-2xl font-bold mt-1">{stats.today_grabbed}</div>
            <p className="text-xs text-muted-foreground">累計: {stats.total_grabbed}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-blue-500" />
              <span className="text-sm text-muted-foreground">發出金額</span>
            </div>
            <div className="text-2xl font-bold mt-1">¥{stats.total_amount_sent.toFixed(2)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-yellow-500" />
              <span className="text-sm text-muted-foreground">搶到金額</span>
            </div>
            <div className="text-2xl font-bold mt-1">¥{stats.total_amount_grabbed.toFixed(2)}</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="config" className="space-y-4">
        <TabsList>
          <TabsTrigger value="config">
            <Settings className="h-4 w-4 mr-2" />
            API 配置
          </TabsTrigger>
          <TabsTrigger value="auto">
            <Zap className="h-4 w-4 mr-2" />
            自動化設置
          </TabsTrigger>
          <TabsTrigger value="history">
            <History className="h-4 w-4 mr-2" />
            遊戲記錄
          </TabsTrigger>
        </TabsList>

        {/* API 配置 */}
        <TabsContent value="config">
          <Card>
            <CardHeader>
              <CardTitle>API 對接配置</CardTitle>
              <CardDescription>配置紅包遊戲系統的 API 連接信息</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>API 地址</Label>
                  <Input 
                    value={config.api_url}
                    onChange={(e) => setConfig({...config, api_url: e.target.value})}
                    placeholder="https://api.redpacket-game.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label>API 密鑰</Label>
                  <Input 
                    type="password"
                    value={config.api_key}
                    onChange={(e) => setConfig({...config, api_key: e.target.value})}
                    placeholder="輸入 API 密鑰"
                  />
                </div>
              </div>
              
              <div className="flex items-center gap-4 pt-4">
                <Button onClick={testConnection} disabled={loading}>
                  <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  測試連接
                </Button>
                <Button onClick={saveConfig} variant="outline" disabled={loading}>
                  保存配置
                </Button>
              </div>

              {/* API 文檔提示 */}
              <div className="mt-6 p-4 bg-muted/50 rounded-lg">
                <h4 className="font-medium mb-2">📋 待對接 API 接口</h4>
                <p className="text-sm text-muted-foreground mb-2">
                  請提供紅包遊戲系統的 API 文檔，包括以下接口：
                </p>
                <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                  <li>用戶認證接口</li>
                  <li>發送紅包接口</li>
                  <li>搶紅包接口</li>
                  <li>查詢餘額接口</li>
                  <li>遊戲記錄接口</li>
                  <li>Webhook 回調接口</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 自動化設置 */}
        <TabsContent value="auto">
          <Card>
            <CardHeader>
              <CardTitle>自動化設置</CardTitle>
              <CardDescription>配置 AI 帳號自動參與紅包遊戲的規則</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* 總開關 */}
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h4 className="font-medium">🎮 啟用紅包遊戲</h4>
                  <p className="text-sm text-muted-foreground">開啟後 AI 帳號將參與紅包互動</p>
                </div>
                <Switch 
                  checked={config.enabled}
                  onCheckedChange={(v) => setConfig({...config, enabled: v})}
                />
              </div>

              {/* 自動搶紅包 */}
              <div className="space-y-4 p-4 border rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">🎯 自動搶紅包</h4>
                    <p className="text-sm text-muted-foreground">AI 自動搶群內紅包</p>
                  </div>
                  <Switch 
                    checked={config.auto_grab}
                    onCheckedChange={(v) => setConfig({...config, auto_grab: v})}
                  />
                </div>
                {config.auto_grab && (
                  <div className="grid gap-4 md:grid-cols-2 pt-2">
                    <div className="space-y-2">
                      <Label>搶包延遲（最小秒）</Label>
                      <Input 
                        type="number"
                        value={config.grab_delay_min}
                        onChange={(e) => setConfig({...config, grab_delay_min: parseInt(e.target.value) || 1})}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>搶包延遲（最大秒）</Label>
                      <Input 
                        type="number"
                        value={config.grab_delay_max}
                        onChange={(e) => setConfig({...config, grab_delay_max: parseInt(e.target.value) || 5})}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* 自動發紅包 */}
              <div className="space-y-4 p-4 border rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">🧧 自動發紅包</h4>
                    <p className="text-sm text-muted-foreground">AI 定時發送紅包活躍氣氛</p>
                  </div>
                  <Switch 
                    checked={config.auto_send}
                    onCheckedChange={(v) => setConfig({...config, auto_send: v})}
                  />
                </div>
                {config.auto_send && (
                  <div className="grid gap-4 md:grid-cols-3 pt-2">
                    <div className="space-y-2">
                      <Label>發包間隔（秒）</Label>
                      <Input 
                        type="number"
                        value={config.send_interval}
                        onChange={(e) => setConfig({...config, send_interval: parseInt(e.target.value) || 300})}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>金額最小值</Label>
                      <Input 
                        type="number"
                        value={config.send_amount_min}
                        onChange={(e) => setConfig({...config, send_amount_min: parseFloat(e.target.value) || 1})}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>金額最大值</Label>
                      <Input 
                        type="number"
                        value={config.send_amount_max}
                        onChange={(e) => setConfig({...config, send_amount_max: parseFloat(e.target.value) || 10})}
                      />
                    </div>
                  </div>
                )}
              </div>

              <Button onClick={saveConfig} className="w-full">
                保存自動化設置
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 遊戲記錄 */}
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>遊戲記錄</CardTitle>
              <CardDescription>查看紅包收發記錄</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>暫無遊戲記錄</p>
                <p className="text-sm">連接 API 後將顯示紅包收發記錄</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
