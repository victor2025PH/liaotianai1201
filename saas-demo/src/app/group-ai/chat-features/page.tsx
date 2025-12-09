"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { useToast } from "@/hooks/use-toast"
import { 
  MessageSquare, Play, Square, Settings, Users, Clock, 
  Gamepad2, FileText, BarChart3, Target, Sparkles, 
  RefreshCw, Send, Dice5, HelpCircle, Gift, Loader2,
  User, Smile, TrendingUp, Zap, Calendar, Bot
} from "lucide-react"

import { getApiBaseUrl } from "@/lib/api/config"

const API_BASE = getApiBaseUrl()

// 人設列表
const DEFAULT_PERSONAS = [
  { id: "cheerful_girl", name: "小美", avatar: "👧", personality: "開朗活潑", emoji_frequency: "high" },
  { id: "professional_guy", name: "老張", avatar: "👨‍💼", personality: "理性穩重", emoji_frequency: "low" },
  { id: "funny_brother", name: "杰哥", avatar: "🎮", personality: "搞笑幽默", emoji_frequency: "medium" },
  { id: "gentle_sister", name: "小雅", avatar: "👩", personality: "溫柔體貼", emoji_frequency: "medium" },
  { id: "tech_geek", name: "小K", avatar: "🤓", personality: "技術宅", emoji_frequency: "low" },
  { id: "enthusiastic_auntie", name: "王姐", avatar: "👩‍🦱", personality: "熱心腸", emoji_frequency: "medium" },
]

// 排程任務
const DEFAULT_SCHEDULES = [
  { id: "morning_greeting", name: "早安問候", time: "09:00", emoji: "☀️", enabled: true },
  { id: "lunch_topic", name: "午餐話題", time: "12:00", emoji: "🍱", enabled: true },
  { id: "afternoon_tea", name: "下午茶時間", time: "15:00", emoji: "☕", enabled: true },
  { id: "evening_redpacket", name: "晚間紅包", time: "18:30", emoji: "🧧", enabled: true },
  { id: "night_chat", name: "晚間閒聊", time: "21:00", emoji: "🌙", enabled: true },
  { id: "goodnight", name: "晚安", time: "23:00", emoji: "💤", enabled: true },
]

// 遊戲列表
const DEFAULT_GAMES = [
  { type: "dice", name: "骰子遊戲", emoji: "🎲", description: "擲骰子比大小", enabled: true },
  { type: "quiz", name: "問答搶答", emoji: "❓", description: "搶答贏紅包", enabled: true },
  { type: "guess", name: "猜數字", emoji: "🔢", description: "猜1-100的數字", enabled: true },
  { type: "lucky", name: "幸運抽獎", emoji: "🎰", description: "隨機抽獎", enabled: true },
]

export default function ChatFeaturesPage() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState("settings")
  
  // 設置狀態
  const [settings, setSettings] = useState({
    auto_chat_enabled: true,
    games_enabled: true,
    scripts_enabled: true,
    scheduler_enabled: true,
    chat_interval_min: 30,
    chat_interval_max: 120,
    redpacket_enabled: true,
    redpacket_interval: 300,
    emoji_frequency: "medium",
  })
  
  // 人設狀態
  const [personas, setPersonas] = useState(DEFAULT_PERSONAS)
  
  // 排程狀態
  const [schedules, setSchedules] = useState(DEFAULT_SCHEDULES)
  
  // 遊戲狀態
  const [games, setGames] = useState(DEFAULT_GAMES)
  
  // 分析數據
  const [analytics, setAnalytics] = useState({
    total_messages: 0,
    active_users: 0,
    games_played: 0,
    conversion_rate: 0,
  })
  
  // 轉化漏斗
  const [funnel, setFunnel] = useState([
    { name: "加入群組", count: 100, rate: 100 },
    { name: "首次發言", count: 75, rate: 75 },
    { name: "活躍聊天", count: 45, rate: 60 },
    { name: "參與遊戲", count: 30, rate: 66.7 },
    { name: "搶紅包", count: 25, rate: 83.3 },
    { name: "轉化", count: 12, rate: 48 },
  ])

  // 獲取設置
  const fetchSettings = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/chat-features/settings`)
      if (res.ok) {
        const data = await res.json()
        if (data.settings) {
          setSettings(data.settings)
        }
      }
    } catch (error) {
      console.warn("獲取設置失敗:", error)
    }
  }

  // 更新設置
  const updateSettings = async () => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/chat-features/settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      })
      
      if (res.ok) {
        toast({ title: "設置已更新", description: "配置已同步到所有節點" })
      } else {
        throw new Error("更新失敗")
      }
    } catch (error) {
      toast({ title: "更新失敗", description: String(error), variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 啟動聊天
  const startChat = async () => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/chat-features/chat/start`, {
        method: "POST",
      })
      
      if (res.ok) {
        toast({ title: "聊天已啟動", description: "AI 開始自動聊天" })
      } else {
        throw new Error("啟動失敗")
      }
    } catch (error) {
      toast({ title: "啟動失敗", description: String(error), variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 停止聊天
  const stopChat = async () => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/chat-features/chat/stop`, {
        method: "POST",
      })
      
      if (res.ok) {
        toast({ title: "聊天已停止" })
      } else {
        throw new Error("停止失敗")
      }
    } catch (error) {
      toast({ title: "停止失敗", description: String(error), variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 啟動遊戲
  const startGame = async (gameType: string) => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/chat-features/games/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_type: gameType }),
      })
      
      if (res.ok) {
        toast({ title: "遊戲已啟動", description: `${gameType} 遊戲開始！` })
      } else {
        throw new Error("啟動失敗")
      }
    } catch (error) {
      toast({ title: "啟動失敗", description: String(error), variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 切換排程任務
  const toggleSchedule = async (taskId: string, enabled: boolean) => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      await fetchWithAuth(`${API_BASE}/group-ai/chat-features/schedules/${taskId}/toggle?enabled=${enabled}`, {
        method: "PUT",
      })
      
      setSchedules(schedules.map(s => 
        s.id === taskId ? { ...s, enabled } : s
      ))
      
      toast({ title: enabled ? "任務已啟用" : "任務已禁用" })
    } catch (error) {
      console.error("切換失敗:", error)
    }
  }

  useEffect(() => {
    fetchSettings()
  }, [])

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 頁面標題 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Sparkles className="h-8 w-8 text-primary" />
            智能聊天控制台
          </h1>
          <p className="text-muted-foreground mt-1">
            管理人設、排程、遊戲和數據分析
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={startChat} disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Play className="h-4 w-4 mr-2" />}
            啟動聊天
          </Button>
          <Button variant="outline" onClick={stopChat} disabled={loading}>
            <Square className="h-4 w-4 mr-2" />
            停止
          </Button>
        </div>
      </div>

      {/* 快速統計 */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">在線節點</p>
                <p className="text-2xl font-bold">2</p>
              </div>
              <Bot className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">活躍帳號</p>
                <p className="text-2xl font-bold">6</p>
              </div>
              <Users className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">今日消息</p>
                <p className="text-2xl font-bold">{analytics.total_messages || 0}</p>
              </div>
              <MessageSquare className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">轉化率</p>
                <p className="text-2xl font-bold">{analytics.conversion_rate || 12}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 主要內容區 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="settings" className="flex items-center gap-1">
            <Settings className="h-4 w-4" />
            基本設置
          </TabsTrigger>
          <TabsTrigger value="personas" className="flex items-center gap-1">
            <User className="h-4 w-4" />
            人設管理
          </TabsTrigger>
          <TabsTrigger value="schedules" className="flex items-center gap-1">
            <Calendar className="h-4 w-4" />
            排程任務
          </TabsTrigger>
          <TabsTrigger value="games" className="flex items-center gap-1">
            <Gamepad2 className="h-4 w-4" />
            互動遊戲
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-1">
            <BarChart3 className="h-4 w-4" />
            數據分析
          </TabsTrigger>
          <TabsTrigger value="optimize" className="flex items-center gap-1">
            <Zap className="h-4 w-4" />
            自動優化
          </TabsTrigger>
        </TabsList>

        {/* 基本設置 */}
        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>聊天設置</CardTitle>
              <CardDescription>配置自動聊天行為</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex flex-row justify-start gap-10">
                {/* 功能開關 */}
                <div className="space-y-4 flex-shrink-0 min-w-[200px]">
                  <h3 className="font-semibold">功能開關</h3>
                  <div className="flex items-center gap-4">
                    <Label htmlFor="auto_chat" className="min-w-[100px]">自動聊天</Label>
                    <Switch 
                      id="auto_chat"
                      checked={settings.auto_chat_enabled}
                      onCheckedChange={(checked) => setSettings({...settings, auto_chat_enabled: checked})}
                    />
                  </div>
                  <div className="flex items-center gap-4">
                    <Label htmlFor="games" className="min-w-[100px]">遊戲功能</Label>
                    <Switch 
                      id="games"
                      checked={settings.games_enabled}
                      onCheckedChange={(checked) => setSettings({...settings, games_enabled: checked})}
                    />
                  </div>
                  <div className="flex items-center gap-4">
                    <Label htmlFor="scripts" className="min-w-[100px]">劇本功能</Label>
                    <Switch 
                      id="scripts"
                      checked={settings.scripts_enabled}
                      onCheckedChange={(checked) => setSettings({...settings, scripts_enabled: checked})}
                    />
                  </div>
                  <div className="flex items-center gap-4">
                    <Label htmlFor="scheduler" className="min-w-[100px]">排程功能</Label>
                    <Switch 
                      id="scheduler"
                      checked={settings.scheduler_enabled}
                      onCheckedChange={(checked) => setSettings({...settings, scheduler_enabled: checked})}
                    />
                  </div>
                  <div className="flex items-center gap-4">
                    <Label htmlFor="redpacket" className="min-w-[100px]">紅包功能</Label>
                    <Switch 
                      id="redpacket"
                      checked={settings.redpacket_enabled}
                      onCheckedChange={(checked) => setSettings({...settings, redpacket_enabled: checked})}
                    />
                  </div>
                </div>

                {/* 參數設置 */}
                <div className="space-y-4 flex-shrink-0">
                  <h3 className="font-semibold">參數設置</h3>
                  <div className="space-y-1.5">
                    <Label className="text-sm">聊天間隔（秒）</Label>
                    <div className="flex items-center gap-2">
                      <Input 
                        type="number" 
                        value={settings.chat_interval_min}
                        onChange={(e) => setSettings({...settings, chat_interval_min: parseInt(e.target.value)})}
                        className="w-20 h-9"
                      />
                      <span className="text-muted-foreground">-</span>
                      <Input 
                        type="number" 
                        value={settings.chat_interval_max}
                        onChange={(e) => setSettings({...settings, chat_interval_max: parseInt(e.target.value)})}
                        className="w-20 h-9"
                      />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-sm">紅包間隔（秒）</Label>
                    <Input 
                      type="number" 
                      value={settings.redpacket_interval}
                      onChange={(e) => setSettings({...settings, redpacket_interval: parseInt(e.target.value)})}
                      className="w-28 h-9"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-sm">表情頻率</Label>
                    <div className="flex gap-2">
                      {["low", "medium", "high"].map((freq) => (
                        <Button
                          key={freq}
                          variant={settings.emoji_frequency === freq ? "default" : "outline"}
                          size="sm"
                          className="h-9"
                          onClick={() => setSettings({...settings, emoji_frequency: freq})}
                        >
                          {freq === "low" ? "低" : freq === "medium" ? "中" : "高"}
                        </Button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
              
              <Separator />
              
              <Button onClick={updateSettings} disabled={loading}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                保存設置
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 人設管理 */}
        <TabsContent value="personas" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AI 人設管理</CardTitle>
              <CardDescription>管理 AI 賬號的人設和個性</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                {personas.map((persona) => (
                  <Card key={persona.id} className="cursor-pointer hover:border-primary transition-colors">
                    <CardContent className="pt-4">
                      <div className="flex items-start gap-3">
                        <div className="text-4xl">{persona.avatar}</div>
                        <div className="flex-1">
                          <h4 className="font-semibold">{persona.name}</h4>
                          <p className="text-sm text-muted-foreground">{persona.personality}</p>
                          <div className="flex items-center gap-2 mt-2">
                            <Smile className="h-4 w-4" />
                            <span className="text-xs">
                              表情: {persona.emoji_frequency === "high" ? "高" : persona.emoji_frequency === "medium" ? "中" : "低"}
                            </span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 排程任務 */}
        <TabsContent value="schedules" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>每日排程任務</CardTitle>
              <CardDescription>配置自動執行的每日任務</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {schedules.map((schedule) => (
                  <div 
                    key={schedule.id} 
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="text-2xl">{schedule.emoji}</div>
                      <div>
                        <h4 className="font-medium">{schedule.name}</h4>
                        <p className="text-sm text-muted-foreground">每日 {schedule.time}</p>
                      </div>
                    </div>
                    <Switch 
                      checked={schedule.enabled}
                      onCheckedChange={(checked) => toggleSchedule(schedule.id, checked)}
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 互動遊戲 */}
        <TabsContent value="games" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>互動遊戲</CardTitle>
              <CardDescription>啟動群組互動遊戲</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                {games.map((game) => (
                  <Card key={game.type} className="overflow-hidden">
                    <CardContent className="pt-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <div className="text-4xl">{game.emoji}</div>
                          <div>
                            <h4 className="font-semibold">{game.name}</h4>
                            <p className="text-sm text-muted-foreground">{game.description}</p>
                          </div>
                        </div>
                        <Button 
                          size="sm" 
                          onClick={() => startGame(game.type)}
                          disabled={loading}
                        >
                          <Play className="h-4 w-4 mr-1" />
                          啟動
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 數據分析 */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {/* 轉化漏斗 */}
            <Card>
              <CardHeader>
                <CardTitle>轉化漏斗</CardTitle>
                <CardDescription>用戶轉化各階段數據</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {funnel.map((stage, index) => (
                    <div key={stage.name} className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span>{stage.name}</span>
                        <span className="text-muted-foreground">{stage.count} ({stage.rate}%)</span>
                      </div>
                      <div className="h-3 bg-muted rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-primary transition-all"
                          style={{ width: `${stage.rate}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* 活躍度統計 */}
            <Card>
              <CardHeader>
                <CardTitle>活躍時段</CardTitle>
                <CardDescription>用戶活躍時間分布</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-6 gap-2">
                  {[9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24].slice(0, 12).map((hour) => (
                    <div key={hour} className="text-center">
                      <div 
                        className="h-16 bg-primary/20 rounded mx-auto w-full relative"
                        style={{ backgroundColor: `rgba(var(--primary), ${Math.random() * 0.5 + 0.2})` }}
                      >
                        <div 
                          className="absolute bottom-0 w-full bg-primary rounded-b transition-all"
                          style={{ height: `${Math.random() * 80 + 20}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">{hour}時</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 自動優化 */}
        <TabsContent value="optimize" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>自動優化建議</CardTitle>
              <CardDescription>基於數據分析的優化建議</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 border rounded-lg bg-yellow-50 dark:bg-yellow-950">
                <div className="flex items-start gap-3">
                  <TrendingUp className="h-5 w-5 text-yellow-600" />
                  <div>
                    <h4 className="font-medium">提高參與度</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      當前參與度 45%，建議增加遊戲頻率和紅包活動
                    </p>
                    <Button size="sm" variant="outline" className="mt-2">
                      應用建議
                    </Button>
                  </div>
                </div>
              </div>
              
              <div className="p-4 border rounded-lg bg-blue-50 dark:bg-blue-950">
                <div className="flex items-start gap-3">
                  <Target className="h-5 w-5 text-blue-600" />
                  <div>
                    <h4 className="font-medium">優化轉化劇本</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      轉化率 12%，建議優化轉化階段的對話劇本
                    </p>
                    <Button size="sm" variant="outline" className="mt-2">
                      應用建議
                    </Button>
                  </div>
                </div>
              </div>
              
              <div className="p-4 border rounded-lg bg-green-50 dark:bg-green-950">
                <div className="flex items-start gap-3">
                  <Clock className="h-5 w-5 text-green-600" />
                  <div>
                    <h4 className="font-medium">調整活躍時段</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      高峰時段為 19:00-22:00，建議在此時段增加互動
                    </p>
                    <Button size="sm" variant="outline" className="mt-2">
                      應用建議
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
