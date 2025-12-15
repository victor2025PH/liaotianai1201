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
  User, Smile, TrendingUp, Zap, Calendar, Bot, Key,
  CheckCircle, XCircle, AlertCircle, Brain
} from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
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
  const [failedAccountsDialogOpen, setFailedAccountsDialogOpen] = useState(false)
  const [failedAccountsList, setFailedAccountsList] = useState<Array<{account_id: string, error: string}>>([])
  const [successfulAccountsDialogOpen, setSuccessfulAccountsDialogOpen] = useState(false)
  const [successfulAccountsList, setSuccessfulAccountsList] = useState<Array<{account_id: string, phone?: string, username?: string, server_id?: string}>>([])
  
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
  
  // 排程狀態（确保所有 enabled 都是 boolean）
  const [schedules, setSchedules] = useState(DEFAULT_SCHEDULES.map(s => ({ ...s, enabled: Boolean(s.enabled) })))
  
  // 遊戲狀態
  const [games, setGames] = useState(DEFAULT_GAMES)
  
  // 分析數據
  const [analytics, setAnalytics] = useState({
    total_messages: 0,
    active_users: 0,
    games_played: 0,
    conversion_rate: 0,
  })
  
  // AI 提供商狀態
  const [aiProvider, setAiProvider] = useState({
    current: "openai",
    providers: [] as any[],
    apiKeys: {
      openai: "",
      gemini: "",
      grok: "",
    },
    keyList: {
      openai: [] as any[],
      gemini: [] as any[],
      grok: [] as any[],
    },
    selectedKeys: {
      openai: "",
      gemini: "",
      grok: "",
    },
    testing: {
      openai: false,
      gemini: false,
      grok: false,
    },
    autoFailover: false, // 默认值改为 false，避免未定义
    failoverProviders: [] as string[],
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
          // 确保所有布尔值都是明确的，避免 undefined
          setSettings({
            auto_chat_enabled: data.settings.auto_chat_enabled ?? true,
            games_enabled: data.settings.games_enabled ?? true,
            scripts_enabled: data.settings.scripts_enabled ?? true,
            scheduler_enabled: data.settings.scheduler_enabled ?? true,
            chat_interval_min: data.settings.chat_interval_min ?? 30,
            chat_interval_max: data.settings.chat_interval_max ?? 120,
            redpacket_enabled: data.settings.redpacket_enabled ?? true,
            redpacket_interval: data.settings.redpacket_interval ?? 300,
            emoji_frequency: data.settings.emoji_frequency ?? "medium",
          })
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

  // 啟動聊天（所有節點）
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

  // 一鍵啟動所有賬號聊天
  const startAllAccountsChat = async () => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/chat-features/chat/start-all-accounts`, {
        method: "POST",
      })
      
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          // 設置成功和失敗的賬號列表
          if (data.successful_accounts && data.successful_accounts.length > 0) {
            setSuccessfulAccountsList(data.successful_accounts)
          }
          if (data.failed_accounts && data.failed_accounts.length > 0) {
            setFailedAccountsList(data.failed_accounts)
          }
          
          if (data.failed_accounts && data.failed_accounts.length > 0) {
            // 有部分失敗，顯示詳細信息
            setFailedAccountsDialogOpen(true)
            if (data.successful_accounts && data.successful_accounts.length > 0) {
              setSuccessfulAccountsDialogOpen(true)
            }
            toast({ 
              title: "部分成功", 
              description: `已啟動 ${data.accounts_started}/${data.accounts_total} 個賬號，${data.failed_accounts.length} 個失敗，${data.successful_accounts?.length || 0} 個成功。點擊查看詳情。`,
              variant: "default"
            })
          } else {
            // 全部成功
            if (data.successful_accounts && data.successful_accounts.length > 0) {
              setSuccessfulAccountsDialogOpen(true)
            }
            toast({ 
              title: "啟動成功", 
              description: `已啟動 ${data.accounts_started}/${data.accounts_total} 個賬號的聊天功能` 
            })
          }
        } else {
          // 完全失敗或沒有找到賬號
          if (data.diagnostics) {
            const diag = data.diagnostics
            toast({ 
              title: "啟動失敗", 
              description: `${data.message || "啟動失敗"}\n數據庫賬號: ${diag.active_accounts_in_db || 0}, 在線節點: ${diag.online_workers || 0}`, 
              variant: "destructive" 
            })
          } else {
            toast({ title: "啟動失敗", description: data.message || "啟動失敗", variant: "destructive" })
          }
        }
      } else {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.detail || "啟動失敗")
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

  // 獲取 AI 提供商狀態
  const fetchAIProviderStatus = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/ai-provider/providers`)
      if (res.ok) {
        const data = await res.json()
        
        // 从后端返回的数据中提取 key 列表
        const providersData = data.providers || {}
        const keyList = {
          openai: providersData.openai?.keys || [],
          gemini: providersData.gemini?.keys || [],
          grok: providersData.grok?.keys || [],
        }
        
        // 提取当前激活的 key ID
        const selectedKeys = {
          openai: providersData.openai?.active_key_id || null,
          gemini: providersData.gemini?.active_key_id || null,
          grok: providersData.grok?.active_key_id || null,
        }
        
        setAiProvider(prev => ({
          ...prev,
          current: data.current_provider || "openai",
          providers: Object.values(providersData), // 转换为数组格式，用于兼容旧代码
          apiKeys: {
            openai: providersData.openai?.api_key_preview || "",
            gemini: providersData.gemini?.api_key_preview || "",
            grok: providersData.grok?.api_key_preview || "",
          },
          keyList: keyList, // 更新 key 列表
          selectedKeys: selectedKeys, // 更新选中的 key
          testing: {
            openai: false,
            gemini: false,
            grok: false,
          },
          autoFailover: Boolean(data.auto_failover_enabled),
          failoverProviders: data.failover_providers || [],
        }))
      }
    } catch (error) {
      console.warn("獲取 AI 提供商狀態失敗:", error)
    }
  }

  // 切換 AI 提供商
  const switchAIProvider = async (provider: string) => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/ai-provider/switch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider,
          auto_failover_enabled: aiProvider.autoFailover,
          failover_providers: aiProvider.failoverProviders,
        }),
      })
      
      if (res.ok) {
        toast({ title: "切換成功", description: `已切換到 ${provider}` })
        await fetchAIProviderStatus()
      } else {
        throw new Error("切換失敗")
      }
    } catch (error) {
      toast({ title: "切換失敗", description: String(error), variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 更新 API Key（保存到当前激活的 Key）
  const updateAPIKey = async (provider: string, apiKey: string) => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const keyId = aiProvider.selectedKeys[provider as keyof typeof aiProvider.selectedKeys]
      const url = keyId 
        ? `${API_BASE}/group-ai/ai-provider/update-key?provider=${provider}&api_key=${encodeURIComponent(apiKey)}&key_id=${keyId}`
        : `${API_BASE}/group-ai/ai-provider/update-key?provider=${provider}&api_key=${encodeURIComponent(apiKey)}`
      
      const res = await fetchWithAuth(url, {
        method: "POST",
      })
      
      if (res.ok) {
        toast({ title: "更新成功", description: `${provider} API Key 已更新` })
        await fetchAIProviderStatus()
      } else {
        throw new Error("更新失敗")
      }
    } catch (error) {
      toast({ title: "更新失敗", description: String(error), variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 添加新 API Key
  const addAPIKey = async (provider: string, apiKey: string, keyName: string) => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(
        `${API_BASE}/group-ai/ai-provider/keys/add?provider=${provider}&api_key=${encodeURIComponent(apiKey)}&key_name=${encodeURIComponent(keyName)}`,
        { method: "POST" }
      )
      
      if (res.ok) {
        toast({ title: "添加成功", description: `${provider} 的新 Key 已添加` })
        await fetchAIProviderStatus()
      } else {
        const error = await res.json()
        throw new Error(error.detail || "添加失敗")
      }
    } catch (error) {
      toast({ title: "添加失敗", description: String(error), variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 删除 API Key
  const deleteAPIKey = async (keyId: string, provider: string, keyName: string) => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(
        `${API_BASE}/group-ai/ai-provider/keys/${keyId}`,
        { method: "DELETE" }
      )
      
      if (res.ok) {
        toast({ title: "删除成功", description: `${provider} 的 Key "${keyName}" 已删除` })
        await fetchAIProviderStatus()
      } else {
        throw new Error("删除失敗")
      }
    } catch (error) {
      toast({ title: "删除失敗", description: String(error), variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 激活 API Key
  const activateAPIKey = async (keyId: string) => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(
        `${API_BASE}/group-ai/ai-provider/keys/${keyId}/activate`,
        { method: "POST" }
      )
      
      if (res.ok) {
        toast({ title: "激活成功", description: "已切换到选中的 Key" })
        await fetchAIProviderStatus()
      } else {
        throw new Error("激活失敗")
      }
    } catch (error) {
      toast({ title: "激活失敗", description: String(error), variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 測試 API Key
  const testAPIKey = async (provider: string, apiKey: string) => {
    try {
      setAiProvider(prev => ({
        ...prev,
        testing: { ...prev.testing, [provider]: true }
      }))
      
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/ai-provider/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, api_key: apiKey }),
      })
      
      const data = await res.json()
      
      if (data.success) {
        toast({ title: "測試成功", description: data.message })
        await fetchAIProviderStatus()
      } else {
        toast({ title: "測試失敗", description: data.message, variant: "destructive" })
      }
    } catch (error) {
      toast({ title: "測試失敗", description: String(error), variant: "destructive" })
    } finally {
      setAiProvider(prev => ({
        ...prev,
        testing: { ...prev.testing, [provider]: false }
      }))
    }
  }

  useEffect(() => {
    fetchSettings()
    fetchAIProviderStatus()
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
          <Button variant="default" onClick={startAllAccountsChat} disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Users className="h-4 w-4 mr-2" />}
            一鍵啟動所有賬號
          </Button>
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
                      checked={Boolean(settings.auto_chat_enabled)}
                      onCheckedChange={(checked) => setSettings({...settings, auto_chat_enabled: Boolean(checked)})}
                    />
                  </div>
                  <div className="flex items-center gap-4">
                    <Label htmlFor="games" className="min-w-[100px]">遊戲功能</Label>
                    <Switch 
                      id="games"
                      checked={Boolean(settings.games_enabled)}
                      onCheckedChange={(checked) => setSettings({...settings, games_enabled: Boolean(checked)})}
                    />
                  </div>
                  <div className="flex items-center gap-4">
                    <Label htmlFor="scripts" className="min-w-[100px]">劇本功能</Label>
                    <Switch 
                      id="scripts"
                      checked={Boolean(settings.scripts_enabled)}
                      onCheckedChange={(checked) => setSettings({...settings, scripts_enabled: Boolean(checked)})}
                    />
                  </div>
                  <div className="flex items-center gap-4">
                    <Label htmlFor="scheduler" className="min-w-[100px]">排程功能</Label>
                    <Switch 
                      id="scheduler"
                      checked={Boolean(settings.scheduler_enabled)}
                      onCheckedChange={(checked) => setSettings({...settings, scheduler_enabled: Boolean(checked)})}
                    />
                  </div>
                  <div className="flex items-center gap-4">
                    <Label htmlFor="redpacket" className="min-w-[100px]">紅包功能</Label>
                    <Switch 
                      id="redpacket"
                      checked={Boolean(settings.redpacket_enabled)}
                      onCheckedChange={(checked) => setSettings({...settings, redpacket_enabled: Boolean(checked)})}
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

          {/* AI 提供商管理 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                AI 提供商管理
              </CardTitle>
              <CardDescription>切換 AI 提供商並管理 API Key</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* 當前提供商 */}
              <div className="space-y-2">
                <Label>當前使用的 AI 提供商</Label>
                <div className="flex items-center gap-3 flex-wrap">
                  <Select value={aiProvider.current} onValueChange={switchAIProvider}>
                    <SelectTrigger className="w-[200px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="openai">OpenAI</SelectItem>
                      <SelectItem value="gemini">Google Gemini</SelectItem>
                      <SelectItem value="grok">xAI Grok</SelectItem>
                    </SelectContent>
                  </Select>
                  {aiProvider.providers.find((p: any) => p.name === aiProvider.current)?.is_valid ? (
                    <Badge variant="default" className="gap-1">
                      <CheckCircle className="h-3 w-3" />
                      已驗證
                    </Badge>
                  ) : (
                    <Badge variant="destructive" className="gap-1">
                      <XCircle className="h-3 w-3" />
                      未驗證
                    </Badge>
                  )}
                </div>
                {/* 显示当前激活的 Key 信息 */}
                {(() => {
                  const currentProviderData = aiProvider.providers.find((p: any) => p.name === aiProvider.current)
                  const currentKeyId = aiProvider.selectedKeys[aiProvider.current as keyof typeof aiProvider.selectedKeys]
                  const currentKeyList = aiProvider.keyList[aiProvider.current as keyof typeof aiProvider.keyList]
                  const activeKey = currentKeyList?.find((k: any) => k.id === currentKeyId || k.is_active)
                  
                  if (activeKey) {
                    return (
                      <div className="mt-2 p-3 bg-primary/10 border border-primary/20 rounded-lg">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-primary">當前使用的 Key:</span>
                          <Badge variant="default" className="gap-1 bg-primary text-primary-foreground">
                            <span className="w-2 h-2 bg-primary-foreground rounded-full animate-pulse"></span>
                            {activeKey.key_name}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            ({activeKey.api_key_preview})
                          </span>
                          {activeKey.is_valid ? (
                            <Badge variant="outline" className="gap-1 text-green-600 border-green-600">
                              <CheckCircle className="h-3 w-3" />
                              有效
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="gap-1 text-red-600 border-red-600">
                              <XCircle className="h-3 w-3" />
                              无效
                            </Badge>
                          )}
                        </div>
                      </div>
                    )
                  }
                  return null
                })()}
              </div>

              <Separator />

              {/* API Key 配置 */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">API Key 配置</h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchAIProviderStatus}
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    刷新列表
                  </Button>
                </div>
                
                {/* OpenAI */}
                <div className={`space-y-3 p-4 border-2 rounded-lg transition-all ${
                  aiProvider.current === "openai" 
                    ? "bg-primary/5 border-primary shadow-md" 
                    : "border-border"
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Label htmlFor="openai-key">OpenAI API Key</Label>
                      {aiProvider.current === "openai" && (
                        <Badge variant="default" className="gap-1 bg-primary text-primary-foreground">
                          <span className="w-2 h-2 bg-primary-foreground rounded-full animate-pulse"></span>
                          當前使用
                        </Badge>
                      )}
                    </div>
                    {aiProvider.providers.find((p: any) => p.name === "openai")?.is_valid && (
                      <Badge variant="outline" className="gap-1">
                        <CheckCircle className="h-3 w-3" />
                        有效
                      </Badge>
                    )}
                  </div>
                  
                  {/* Key 列表和选择 */}
                  {aiProvider.keyList.openai.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-sm text-muted-foreground">已保存的 Key</Label>
                      <div className="space-y-2">
                        {aiProvider.keyList.openai.map((key: any) => (
                          <div 
                            key={key.id} 
                            className={`flex items-center gap-2 p-2 rounded border-2 transition-all ${
                              key.is_active 
                                ? "bg-primary/10 border-primary shadow-md" 
                                : "bg-muted border-transparent"
                            }`}
                          >
                            <Select
                              value={aiProvider.selectedKeys.openai || ""}
                              onValueChange={(value) => {
                                activateAPIKey(value)
                              }}
                            >
                              <SelectTrigger className={`flex-1 ${key.is_active ? "font-semibold" : ""}`}>
                                <SelectValue>
                                  <span className="flex items-center gap-2">
                                    {key.is_active && (
                                      <span className="inline-flex items-center gap-1 text-primary font-bold">
                                        <span className="w-2 h-2 bg-primary rounded-full animate-pulse"></span>
                                        当前使用
                                      </span>
                                    )}
                                    <span className={key.is_active ? "text-primary" : ""}>
                                      {key.key_name}
                                    </span>
                                  </span>
                                </SelectValue>
                              </SelectTrigger>
                              <SelectContent>
                                {aiProvider.keyList.openai.map((k: any) => (
                                  <SelectItem key={k.id} value={k.id}>
                                    <span className="flex items-center gap-2">
                                      {k.is_active && (
                                        <span className="text-primary font-bold">● 当前使用</span>
                                      )}
                                      {k.key_name}
                                    </span>
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <Badge 
                              variant={key.is_valid ? (key.is_active ? "default" : "outline") : "destructive"}
                              className={key.is_active ? "ring-2 ring-primary" : ""}
                            >
                              {key.is_valid ? "有效" : "无效"}
                            </Badge>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                if (confirm(`确定要删除 Key "${key.key_name}" 吗？`)) {
                                  deleteAPIKey(key.id, "openai", key.key_name)
                                }
                              }}
                              disabled={loading}
                            >
                              <XCircle className="h-4 w-4 text-destructive" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* 添加新 Key */}
                  <div className="flex gap-2">
                    <Input
                      id="openai-key"
                      type="password"
                      placeholder="輸入新的 OpenAI API Key"
                      className="flex-1"
                    />
                    <Input
                      id="openai-key-name"
                      type="text"
                      placeholder="Key 名稱（可選）"
                      className="w-32"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const key = (document.getElementById("openai-key") as HTMLInputElement)?.value
                        const keyName = (document.getElementById("openai-key-name") as HTMLInputElement)?.value || "default"
                        if (key) {
                          addAPIKey("openai", key, keyName)
                          // 清空输入框
                          ;(document.getElementById("openai-key") as HTMLInputElement).value = ""
                          ;(document.getElementById("openai-key-name") as HTMLInputElement).value = ""
                        } else {
                          toast({ title: "請先輸入 API Key", variant: "destructive" })
                        }
                      }}
                      disabled={loading}
                    >
                      添加
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const key = (document.getElementById("openai-key") as HTMLInputElement)?.value
                        if (key) {
                          testAPIKey("openai", key)
                        } else {
                          toast({ title: "請先輸入 API Key", variant: "destructive" })
                        }
                      }}
                      disabled={loading || aiProvider.testing.openai}
                    >
                      {aiProvider.testing.openai ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        "測試"
                      )}
                    </Button>
                  </div>
                </div>

                {/* Gemini */}
                <div className={`space-y-3 p-4 border-2 rounded-lg transition-all ${
                  aiProvider.current === "gemini" 
                    ? "bg-primary/5 border-primary shadow-md" 
                    : "border-border"
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Label htmlFor="gemini-key">Google Gemini API Key</Label>
                      {aiProvider.current === "gemini" && (
                        <Badge variant="default" className="gap-1 bg-primary text-primary-foreground">
                          <span className="w-2 h-2 bg-primary-foreground rounded-full animate-pulse"></span>
                          當前使用
                        </Badge>
                      )}
                    </div>
                    {aiProvider.providers.find((p: any) => p.name === "gemini")?.is_valid && (
                      <Badge variant="outline" className="gap-1">
                        <CheckCircle className="h-3 w-3" />
                        有效
                      </Badge>
                    )}
                  </div>
                  
                  {/* Key 列表和选择 */}
                  {aiProvider.keyList.gemini.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-sm text-muted-foreground">已保存的 Key</Label>
                      <div className="space-y-2">
                        {aiProvider.keyList.gemini.map((key: any) => (
                          <div 
                            key={key.id} 
                            className={`flex items-center gap-2 p-2 rounded border-2 transition-all ${
                              key.is_active 
                                ? "bg-primary/10 border-primary shadow-md" 
                                : "bg-muted border-transparent"
                            }`}
                          >
                            <Select
                              value={aiProvider.selectedKeys.gemini || ""}
                              onValueChange={(value) => {
                                activateAPIKey(value)
                              }}
                            >
                              <SelectTrigger className={`flex-1 ${key.is_active ? "font-semibold" : ""}`}>
                                <SelectValue>
                                  <span className="flex items-center gap-2">
                                    {key.is_active && (
                                      <span className="inline-flex items-center gap-1 text-primary font-bold">
                                        <span className="w-2 h-2 bg-primary rounded-full animate-pulse"></span>
                                        当前使用
                                      </span>
                                    )}
                                    <span className={key.is_active ? "text-primary" : ""}>
                                      {key.key_name}
                                    </span>
                                  </span>
                                </SelectValue>
                              </SelectTrigger>
                              <SelectContent>
                                {aiProvider.keyList.gemini.map((k: any) => (
                                  <SelectItem key={k.id} value={k.id}>
                                    <span className="flex items-center gap-2">
                                      {k.is_active && (
                                        <span className="text-primary font-bold">● 当前使用</span>
                                      )}
                                      {k.key_name}
                                    </span>
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <Badge 
                              variant={key.is_valid ? (key.is_active ? "default" : "outline") : "destructive"}
                              className={key.is_active ? "ring-2 ring-primary" : ""}
                            >
                              {key.is_valid ? "有效" : "无效"}
                            </Badge>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                if (confirm(`确定要删除 Key "${key.key_name}" 吗？`)) {
                                  deleteAPIKey(key.id, "gemini", key.key_name)
                                }
                              }}
                              disabled={loading}
                            >
                              <XCircle className="h-4 w-4 text-destructive" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* 添加新 Key */}
                  <div className="flex gap-2">
                    <Input
                      id="gemini-key"
                      type="password"
                      placeholder="輸入新的 Gemini API Key"
                      className="flex-1"
                    />
                    <Input
                      id="gemini-key-name"
                      type="text"
                      placeholder="Key 名稱（可選）"
                      className="w-32"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const key = (document.getElementById("gemini-key") as HTMLInputElement)?.value
                        const keyName = (document.getElementById("gemini-key-name") as HTMLInputElement)?.value || "default"
                        if (key) {
                          addAPIKey("gemini", key, keyName)
                          ;(document.getElementById("gemini-key") as HTMLInputElement).value = ""
                          ;(document.getElementById("gemini-key-name") as HTMLInputElement).value = ""
                        } else {
                          toast({ title: "請先輸入 API Key", variant: "destructive" })
                        }
                      }}
                      disabled={loading}
                    >
                      添加
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const key = (document.getElementById("gemini-key") as HTMLInputElement)?.value
                        if (key) {
                          testAPIKey("gemini", key)
                        } else {
                          toast({ title: "請先輸入 API Key", variant: "destructive" })
                        }
                      }}
                      disabled={loading || aiProvider.testing.gemini}
                    >
                      {aiProvider.testing.gemini ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        "測試"
                      )}
                    </Button>
                  </div>
                </div>

                {/* Grok */}
                <div className={`space-y-3 p-4 border-2 rounded-lg transition-all ${
                  aiProvider.current === "grok" 
                    ? "bg-primary/5 border-primary shadow-md" 
                    : "border-border"
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Label htmlFor="grok-key">xAI Grok API Key</Label>
                      {aiProvider.current === "grok" && (
                        <Badge variant="default" className="gap-1 bg-primary text-primary-foreground">
                          <span className="w-2 h-2 bg-primary-foreground rounded-full animate-pulse"></span>
                          當前使用
                        </Badge>
                      )}
                    </div>
                    {aiProvider.providers.find((p: any) => p.name === "grok")?.is_valid && (
                      <Badge variant="outline" className="gap-1">
                        <CheckCircle className="h-3 w-3" />
                        有效
                      </Badge>
                    )}
                  </div>
                  
                  {/* Key 列表和选择 */}
                  {aiProvider.keyList.grok.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-sm text-muted-foreground">已保存的 Key</Label>
                      <div className="space-y-2">
                        {aiProvider.keyList.grok.map((key: any) => (
                          <div 
                            key={key.id} 
                            className={`flex items-center gap-2 p-2 rounded border-2 transition-all ${
                              key.is_active 
                                ? "bg-primary/10 border-primary shadow-md" 
                                : "bg-muted border-transparent"
                            }`}
                          >
                            <Select
                              value={aiProvider.selectedKeys.grok || ""}
                              onValueChange={(value) => {
                                activateAPIKey(value)
                              }}
                            >
                              <SelectTrigger className={`flex-1 ${key.is_active ? "font-semibold" : ""}`}>
                                <SelectValue>
                                  <span className="flex items-center gap-2">
                                    {key.is_active && (
                                      <span className="inline-flex items-center gap-1 text-primary font-bold">
                                        <span className="w-2 h-2 bg-primary rounded-full animate-pulse"></span>
                                        当前使用
                                      </span>
                                    )}
                                    <span className={key.is_active ? "text-primary" : ""}>
                                      {key.key_name}
                                    </span>
                                  </span>
                                </SelectValue>
                              </SelectTrigger>
                              <SelectContent>
                                {aiProvider.keyList.grok.map((k: any) => (
                                  <SelectItem key={k.id} value={k.id}>
                                    <span className="flex items-center gap-2">
                                      {k.is_active && (
                                        <span className="text-primary font-bold">● 当前使用</span>
                                      )}
                                      {k.key_name}
                                    </span>
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <Badge 
                              variant={key.is_valid ? (key.is_active ? "default" : "outline") : "destructive"}
                              className={key.is_active ? "ring-2 ring-primary" : ""}
                            >
                              {key.is_valid ? "有效" : "无效"}
                            </Badge>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                if (confirm(`确定要删除 Key "${key.key_name}" 吗？`)) {
                                  deleteAPIKey(key.id, "grok", key.key_name)
                                }
                              }}
                              disabled={loading}
                            >
                              <XCircle className="h-4 w-4 text-destructive" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* 添加新 Key */}
                  <div className="flex gap-2">
                    <Input
                      id="grok-key"
                      type="password"
                      placeholder="輸入新的 Grok API Key"
                      className="flex-1"
                    />
                    <Input
                      id="grok-key-name"
                      type="text"
                      placeholder="Key 名稱（可選）"
                      className="w-32"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const key = (document.getElementById("grok-key") as HTMLInputElement)?.value
                        const keyName = (document.getElementById("grok-key-name") as HTMLInputElement)?.value || "default"
                        if (key) {
                          addAPIKey("grok", key, keyName)
                          ;(document.getElementById("grok-key") as HTMLInputElement).value = ""
                          ;(document.getElementById("grok-key-name") as HTMLInputElement).value = ""
                        } else {
                          toast({ title: "請先輸入 API Key", variant: "destructive" })
                        }
                      }}
                      disabled={loading}
                    >
                      添加
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const key = (document.getElementById("grok-key") as HTMLInputElement)?.value
                        if (key) {
                          testAPIKey("grok", key)
                        } else {
                          toast({ title: "請先輸入 API Key", variant: "destructive" })
                        }
                      }}
                      disabled={loading || aiProvider.testing.grok}
                    >
                      {aiProvider.testing.grok ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        "測試"
                      )}
                    </Button>
                  </div>
                </div>
              </div>

              <Separator />

              {/* 自動故障切換 */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>自動故障切換</Label>
                    <p className="text-sm text-muted-foreground">當當前 AI 提供商失敗時，自動切換到備用提供商</p>
                  </div>
                  <Switch
                    checked={Boolean(aiProvider.autoFailover)}
                    onCheckedChange={(checked) => {
                      setAiProvider(prev => ({ ...prev, autoFailover: Boolean(checked) }))
                    }}
                  />
                </div>
              </div>

              {/* 使用統計 */}
              {aiProvider.providers.length > 0 && (
                <>
                  <Separator />
                  <div className="space-y-2">
                    <Label>使用統計</Label>
                    <div className="grid grid-cols-3 gap-4">
                      {aiProvider.providers.map((provider: any) => (
                        <Card key={provider.name} className="p-3">
                          <div className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium capitalize">{provider.name}</span>
                              {provider.is_current && (
                                <Badge variant="default" className="text-xs">當前</Badge>
                              )}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              請求: {provider.usage_stats?.total_requests || 0}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              成功: {provider.usage_stats?.successful_requests || 0}
                            </div>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </div>
                </>
              )}
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
                    checked={Boolean(schedule.enabled)}
                    onCheckedChange={(checked) => toggleSchedule(schedule.id, Boolean(checked))}
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

      {/* 成功賬號對話框 */}
      <AlertDialog open={successfulAccountsDialogOpen} onOpenChange={setSuccessfulAccountsDialogOpen}>
        <AlertDialogContent className="max-w-2xl max-h-[80vh]">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              成功啟動的賬號
            </AlertDialogTitle>
            <AlertDialogDescription>
              以下 {successfulAccountsList.length} 個賬號已成功啟動：
            </AlertDialogDescription>
          </AlertDialogHeader>
          <ScrollArea className="max-h-[50vh] pr-4">
            <div className="space-y-3">
              {successfulAccountsList.map((item, index) => (
                <div key={index} className="p-3 border rounded-lg bg-green-50 dark:bg-green-950">
                  <div className="flex items-start gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm break-all">{item.account_id}</p>
                      {item.phone && <p className="text-xs text-muted-foreground mt-1">電話: {item.phone}</p>}
                      {item.username && <p className="text-xs text-muted-foreground">用戶名: @{item.username}</p>}
                      {item.server_id && <p className="text-xs text-muted-foreground">節點: {item.server_id}</p>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
          <AlertDialogFooter>
            <AlertDialogAction onClick={() => setSuccessfulAccountsDialogOpen(false)}>
              關閉
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 失败账号详情对话框 */}
      <AlertDialog open={failedAccountsDialogOpen} onOpenChange={setFailedAccountsDialogOpen}>
        <AlertDialogContent className="max-w-2xl max-h-[80vh]">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-destructive" />
              部分賬號啟動失敗
            </AlertDialogTitle>
            <AlertDialogDescription>
              以下 {failedAccountsList.length} 個賬號啟動失敗，請查看詳細錯誤信息：
            </AlertDialogDescription>
          </AlertDialogHeader>
          <ScrollArea className="max-h-[50vh] pr-4">
            <div className="space-y-3">
              {failedAccountsList.map((item, index) => (
                <div key={index} className="p-3 border rounded-lg bg-destructive/5">
                  <div className="flex items-start gap-2">
                    <XCircle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm break-all">{item.account_id}</p>
                      <p className="text-sm text-muted-foreground mt-1 break-all">{item.error}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
          <AlertDialogFooter>
            <AlertDialogAction onClick={() => setFailedAccountsDialogOpen(false)}>
              關閉
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
