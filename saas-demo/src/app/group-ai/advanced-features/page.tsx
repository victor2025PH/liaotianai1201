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
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog"
import { useToast } from "@/hooks/use-toast"
import { 
  Mic, Image, Link2, Bell, FileText, Shield, Globe, Webhook,
  Play, Plus, Trash2, Edit, RefreshCw, Send, Loader2, Check,
  Volume2, Wand2, Users, Languages, AlertTriangle, Copy,
  CheckCircle, XCircle, Clock, Zap
} from "lucide-react"

import { getApiBaseUrl } from "@/lib/api/config"

const API_BASE = getApiBaseUrl()

// TTS 語音列表
const TTS_VOICES = [
  { id: "zh-CN-XiaoxiaoNeural", name: "曉曉（女）", lang: "zh-CN" },
  { id: "zh-CN-YunxiNeural", name: "雲希（男）", lang: "zh-CN" },
  { id: "zh-TW-HsiaoChenNeural", name: "曉臻（女）", lang: "zh-TW" },
  { id: "zh-TW-YunJheNeural", name: "雲哲（男）", lang: "zh-TW" },
  { id: "en-US-JennyNeural", name: "Jenny", lang: "en-US" },
  { id: "ja-JP-NanamiNeural", name: "七海", lang: "ja-JP" },
]

// 語言列表
const LANGUAGES = [
  { code: "zh-CN", name: "简体中文", flag: "🇨🇳" },
  { code: "zh-TW", name: "繁體中文", flag: "🇹🇼" },
  { code: "en", name: "English", flag: "🇺🇸" },
  { code: "ja", name: "日本語", flag: "🇯🇵" },
  { code: "ko", name: "한국어", flag: "🇰🇷" },
  { code: "vi", name: "Tiếng Việt", flag: "🇻🇳" },
  { code: "th", name: "ภาษาไทย", flag: "🇹🇭" },
]

// Webhook 事件
const WEBHOOK_EVENTS = [
  { id: "message.received", name: "收到消息" },
  { id: "message.sent", name: "發送消息" },
  { id: "user.joined", name: "用戶加入" },
  { id: "user.left", name: "用戶離開" },
  { id: "game.started", name: "遊戲開始" },
  { id: "redpacket.sent", name: "發送紅包" },
  { id: "alert.triggered", name: "告警觸發" },
]

export default function AdvancedFeaturesPage() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState("tts")
  
  // TTS 狀態
  const [ttsConfig, setTtsConfig] = useState({
    enabled: true,
    provider: "edge_tts",
    default_voice: "zh-CN-XiaoxiaoNeural",
    auto_voice_enabled: false,
    auto_voice_probability: 0.1,
  })
  const [ttsText, setTtsText] = useState("")
  
  // 圖片生成狀態
  const [imageConfig, setImageConfig] = useState({
    enabled: true,
    provider: "dalle",
    daily_limit: 50,
  })
  const [imagePrompt, setImagePrompt] = useState("")
  
  // 跨群聯動狀態
  const [crossgroupConfig, setCrossgroupConfig] = useState({
    enabled: true,
    linked_groups: [] as number[],
    delay_between_groups: 30,
  })
  const [newGroupId, setNewGroupId] = useState("")
  
  // 告警狀態
  const [alertRules, setAlertRules] = useState<any[]>([])
  const [alertConfig, setAlertConfig] = useState({
    enabled: true,
    telegram_chat_id: "",
    webhook_url: "",
  })
  
  // 消息模板狀態
  const [templates, setTemplates] = useState<any[]>([])
  const [selectedCategory, setSelectedCategory] = useState("")
  const [newTemplate, setNewTemplate] = useState({ name: "", content: "", category: "general" })
  
  // 黑白名單狀態
  const [whitelist, setWhitelist] = useState<any[]>([])
  const [blacklist, setBlacklist] = useState<any[]>([])
  const [newUserId, setNewUserId] = useState("")
  const [newUserReason, setNewUserReason] = useState("")
  
  // 多語言狀態
  const [languageConfig, setLanguageConfig] = useState({
    enabled: true,
    default_language: "zh-CN",
    auto_detect: true,
    translate_incoming: false,
  })
  
  // Webhook 狀態
  const [webhooks, setWebhooks] = useState<any[]>([])
  const [newWebhook, setNewWebhook] = useState({
    name: "",
    url: "",
    events: [] as string[],
  })

  // 功能總覽
  const [overview, setOverview] = useState<any>(null)

  // 獲取功能總覽
  const fetchOverview = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/advanced/overview`)
      if (res.ok) {
        const data = await res.json()
        setOverview(data.features)
      }
    } catch (error) {
      console.error("獲取總覽失敗:", error)
    }
  }

  // 獲取 TTS 配置
  const fetchTtsConfig = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/advanced/tts/config`)
      if (res.ok) {
        const data = await res.json()
        if (data.config) setTtsConfig(data.config)
      }
    } catch (error) {
      console.error("獲取 TTS 配置失敗:", error)
    }
  }

  // 更新 TTS 配置
  const updateTtsConfig = async () => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/advanced/tts/config`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(ttsConfig),
      })
      if (res.ok) {
        toast({ title: "TTS 配置已更新" })
      }
    } catch (error) {
      toast({ title: "更新失敗", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 發送語音
  const sendVoice = async () => {
    if (!ttsText.trim()) return
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/advanced/tts/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: ttsText }),
      })
      if (res.ok) {
        toast({ title: "語音已發送" })
        setTtsText("")
      }
    } catch (error) {
      toast({ title: "發送失敗", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 生成圖片
  const generateImage = async () => {
    if (!imagePrompt.trim()) return
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/advanced/image/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: imagePrompt }),
      })
      if (res.ok) {
        toast({ title: "圖片生成任務已發送" })
        setImagePrompt("")
      }
    } catch (error) {
      toast({ title: "生成失敗", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 獲取消息模板
  const fetchTemplates = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/advanced/templates`)
      if (res.ok) {
        const data = await res.json()
        if (data.categories) setTemplates(data.categories)
      }
    } catch (error) {
      console.error("獲取模板失敗:", error)
    }
  }

  // 獲取告警規則
  const fetchAlertRules = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/advanced/alerts/rules`)
      if (res.ok) {
        const data = await res.json()
        if (data.rules) setAlertRules(data.rules)
      }
    } catch (error) {
      console.error("獲取告警規則失敗:", error)
    }
  }

  // 切換告警規則
  const toggleAlertRule = async (ruleId: string, enabled: boolean) => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      await fetchWithAuth(`${API_BASE}/group-ai/advanced/alerts/rules/${ruleId}/toggle?enabled=${enabled}`, {
        method: "PUT",
      })
      setAlertRules(alertRules.map(r => r.rule_id === ruleId ? { ...r, enabled } : r))
      toast({ title: enabled ? "規則已啟用" : "規則已禁用" })
    } catch (error) {
      toast({ title: "操作失敗", variant: "destructive" })
    }
  }

  // 獲取黑白名單
  const fetchUserLists = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const [whiteRes, blackRes] = await Promise.all([
        fetchWithAuth(`${API_BASE}/group-ai/advanced/userlist/whitelist`),
        fetchWithAuth(`${API_BASE}/group-ai/advanced/userlist/blacklist`),
      ])
      if (whiteRes.ok) {
        const data = await whiteRes.json()
        setWhitelist(data.users || [])
      }
      if (blackRes.ok) {
        const data = await blackRes.json()
        setBlacklist(data.users || [])
      }
    } catch (error) {
      console.error("獲取名單失敗:", error)
    }
  }

  // 添加到名單
  const addToList = async (listType: "whitelist" | "blacklist") => {
    if (!newUserId) return
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/advanced/userlist/${listType}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: parseInt(newUserId),
          list_type: listType,
          reason: newUserReason,
        }),
      })
      if (res.ok) {
        toast({ title: `已添加到${listType === "whitelist" ? "白" : "黑"}名單` })
        setNewUserId("")
        setNewUserReason("")
        fetchUserLists()
      }
    } catch (error) {
      toast({ title: "添加失敗", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 從名單移除
  const removeFromList = async (listType: "whitelist" | "blacklist", userId: number) => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      await fetchWithAuth(`${API_BASE}/group-ai/advanced/userlist/${listType}/${userId}`, {
        method: "DELETE",
      })
      toast({ title: "已移除" })
      fetchUserLists()
    } catch (error) {
      toast({ title: "移除失敗", variant: "destructive" })
    }
  }

  // 獲取 Webhook
  const fetchWebhooks = async () => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/advanced/webhooks`)
      if (res.ok) {
        const data = await res.json()
        setWebhooks(data.webhooks || [])
      }
    } catch (error) {
      console.error("獲取 Webhook 失敗:", error)
    }
  }

  // 創建 Webhook
  const createWebhook = async () => {
    if (!newWebhook.name || !newWebhook.url) return
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/advanced/webhooks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          webhook_id: `wh_${Date.now()}`,
          ...newWebhook,
          enabled: true,
        }),
      })
      if (res.ok) {
        toast({ title: "Webhook 已創建" })
        setNewWebhook({ name: "", url: "", events: [] })
        fetchWebhooks()
      }
    } catch (error) {
      toast({ title: "創建失敗", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  // 關聯群組
  const linkGroup = async () => {
    if (!newGroupId) return
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/group-ai/advanced/crossgroup/link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify([parseInt(newGroupId)]),
      })
      if (res.ok) {
        const data = await res.json()
        setCrossgroupConfig({ ...crossgroupConfig, linked_groups: data.linked_groups })
        setNewGroupId("")
        toast({ title: "群組已關聯" })
      }
    } catch (error) {
      toast({ title: "關聯失敗", variant: "destructive" })
    }
  }

  useEffect(() => {
    fetchOverview()
    fetchTtsConfig()
    fetchTemplates()
    fetchAlertRules()
    fetchUserLists()
    fetchWebhooks()
  }, [])

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 頁面標題 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Zap className="h-8 w-8 text-primary" />
            高級功能
          </h1>
          <p className="text-muted-foreground mt-1">
            語音、圖片、跨群、告警、模板、名單、多語言、Webhook
          </p>
        </div>
        <Button variant="outline" onClick={fetchOverview}>
          <RefreshCw className="h-4 w-4 mr-2" />
          刷新
        </Button>
      </div>

      {/* 功能卡片概覽 */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Mic className="h-5 w-5 text-blue-500" />
                <span className="font-medium">TTS 語音</span>
              </div>
              <Badge variant={overview?.tts?.enabled ? "default" : "secondary"}>
                {overview?.tts?.enabled ? "已啟用" : "已禁用"}
              </Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Image className="h-5 w-5 text-purple-500" />
                <span className="font-medium">AI 圖片</span>
              </div>
              <Badge variant={overview?.image?.enabled ? "default" : "secondary"}>
                {overview?.image?.enabled ? "已啟用" : "已禁用"}
              </Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-orange-500" />
                <span className="font-medium">告警規則</span>
              </div>
              <Badge>{overview?.alerts?.active_rules || 0} 條</Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Webhook className="h-5 w-5 text-green-500" />
                <span className="font-medium">Webhook</span>
              </div>
              <Badge>{overview?.webhooks?.active || 0} 個</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 主要內容 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-8">
          <TabsTrigger value="tts" className="flex items-center gap-1">
            <Mic className="h-4 w-4" />
            語音
          </TabsTrigger>
          <TabsTrigger value="image" className="flex items-center gap-1">
            <Image className="h-4 w-4" />
            圖片
          </TabsTrigger>
          <TabsTrigger value="crossgroup" className="flex items-center gap-1">
            <Link2 className="h-4 w-4" />
            跨群
          </TabsTrigger>
          <TabsTrigger value="alerts" className="flex items-center gap-1">
            <Bell className="h-4 w-4" />
            告警
          </TabsTrigger>
          <TabsTrigger value="templates" className="flex items-center gap-1">
            <FileText className="h-4 w-4" />
            模板
          </TabsTrigger>
          <TabsTrigger value="userlist" className="flex items-center gap-1">
            <Shield className="h-4 w-4" />
            名單
          </TabsTrigger>
          <TabsTrigger value="language" className="flex items-center gap-1">
            <Globe className="h-4 w-4" />
            語言
          </TabsTrigger>
          <TabsTrigger value="webhook" className="flex items-center gap-1">
            <Webhook className="h-4 w-4" />
            Hook
          </TabsTrigger>
        </TabsList>

        {/* TTS 語音 */}
        <TabsContent value="tts" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>TTS 配置</CardTitle>
                <CardDescription>文字轉語音設置</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>啟用 TTS</Label>
                  <Switch 
                    checked={ttsConfig.enabled}
                    onCheckedChange={(checked) => setTtsConfig({...ttsConfig, enabled: checked})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>默認語音</Label>
                  <Select 
                    value={ttsConfig.default_voice}
                    onValueChange={(value) => setTtsConfig({...ttsConfig, default_voice: value})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TTS_VOICES.map(voice => (
                        <SelectItem key={voice.id} value={voice.id}>
                          {voice.name} ({voice.lang})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center justify-between">
                  <Label>自動發送語音</Label>
                  <Switch 
                    checked={ttsConfig.auto_voice_enabled}
                    onCheckedChange={(checked) => setTtsConfig({...ttsConfig, auto_voice_enabled: checked})}
                  />
                </div>
                <Button onClick={updateTtsConfig} disabled={loading}>
                  保存配置
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>發送語音</CardTitle>
                <CardDescription>輸入文字生成並發送語音</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea 
                  placeholder="輸入要轉換的文字..."
                  value={ttsText}
                  onChange={(e) => setTtsText(e.target.value)}
                  rows={4}
                />
                <Button onClick={sendVoice} disabled={loading || !ttsText.trim()}>
                  {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Volume2 className="h-4 w-4 mr-2" />}
                  發送語音
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* AI 圖片生成 */}
        <TabsContent value="image" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>圖片生成配置</CardTitle>
                <CardDescription>AI 圖片生成設置</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>啟用圖片生成</Label>
                  <Switch 
                    checked={imageConfig.enabled}
                    onCheckedChange={(checked) => setImageConfig({...imageConfig, enabled: checked})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>服務商</Label>
                  <Select 
                    value={imageConfig.provider}
                    onValueChange={(value) => setImageConfig({...imageConfig, provider: value})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="dalle">DALL-E (OpenAI)</SelectItem>
                      <SelectItem value="stable_diffusion">Stable Diffusion</SelectItem>
                      <SelectItem value="midjourney">Midjourney</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>每日限額</Label>
                  <Input 
                    type="number"
                    value={imageConfig.daily_limit}
                    onChange={(e) => setImageConfig({...imageConfig, daily_limit: parseInt(e.target.value)})}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>生成圖片</CardTitle>
                <CardDescription>輸入提示詞生成圖片</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea 
                  placeholder="描述你想要的圖片..."
                  value={imagePrompt}
                  onChange={(e) => setImagePrompt(e.target.value)}
                  rows={4}
                />
                <Button onClick={generateImage} disabled={loading || !imagePrompt.trim()}>
                  {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Wand2 className="h-4 w-4 mr-2" />}
                  生成圖片
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 跨群聯動 */}
        <TabsContent value="crossgroup" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>跨群聯動</CardTitle>
              <CardDescription>關聯多個群組實現同步操作</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>啟用跨群聯動</Label>
                <Switch 
                  checked={crossgroupConfig.enabled}
                  onCheckedChange={(checked) => setCrossgroupConfig({...crossgroupConfig, enabled: checked})}
                />
              </div>
              
              <Separator />
              
              <div className="space-y-2">
                <Label>已關聯群組</Label>
                <div className="flex flex-wrap gap-2">
                  {crossgroupConfig.linked_groups.map(groupId => (
                    <Badge key={groupId} variant="secondary" className="flex items-center gap-1">
                      {groupId}
                      <button 
                        className="ml-1 hover:text-destructive"
                        onClick={() => setCrossgroupConfig({
                          ...crossgroupConfig,
                          linked_groups: crossgroupConfig.linked_groups.filter(g => g !== groupId)
                        })}
                      >
                        <XCircle className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                  {crossgroupConfig.linked_groups.length === 0 && (
                    <span className="text-muted-foreground text-sm">暫無關聯群組</span>
                  )}
                </div>
              </div>
              
              <div className="flex gap-2">
                <Input 
                  placeholder="輸入群組 ID"
                  value={newGroupId}
                  onChange={(e) => setNewGroupId(e.target.value)}
                />
                <Button onClick={linkGroup} disabled={!newGroupId}>
                  <Plus className="h-4 w-4 mr-1" />
                  添加
                </Button>
              </div>
              
              <div className="space-y-2">
                <Label>群間延遲（秒）</Label>
                <Input 
                  type="number"
                  value={crossgroupConfig.delay_between_groups}
                  onChange={(e) => setCrossgroupConfig({...crossgroupConfig, delay_between_groups: parseInt(e.target.value)})}
                  className="w-32"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 告警系統 */}
        <TabsContent value="alerts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>告警規則</CardTitle>
              <CardDescription>配置監控告警</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {alertRules.map(rule => (
                  <div key={rule.rule_id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <AlertTriangle className={`h-5 w-5 ${
                        rule.level === "critical" ? "text-red-500" :
                        rule.level === "error" ? "text-orange-500" :
                        rule.level === "warning" ? "text-yellow-500" : "text-blue-500"
                      }`} />
                      <div>
                        <h4 className="font-medium">{rule.name}</h4>
                        <p className="text-sm text-muted-foreground">{rule.condition}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={rule.level === "critical" ? "destructive" : "secondary"}>
                        {rule.level}
                      </Badge>
                      <Switch 
                        checked={rule.enabled}
                        onCheckedChange={(checked) => toggleAlertRule(rule.rule_id, checked)}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 消息模板 */}
        <TabsContent value="templates" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>消息模板</CardTitle>
              <CardDescription>預設消息快速發送</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {templates.map(category => (
                  <div key={category.category} className="space-y-2">
                    <h4 className="font-medium flex items-center gap-2">
                      <span>{category.icon}</span>
                      {category.name}
                    </h4>
                    <div className="grid grid-cols-3 gap-2">
                      {category.templates?.map((template: any) => (
                        <div key={template.id} className="p-3 border rounded-lg hover:border-primary cursor-pointer">
                          <p className="font-medium text-sm">{template.name}</p>
                          <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{template.content}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 黑白名單 */}
        <TabsContent value="userlist" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  白名單
                </CardTitle>
                <CardDescription>VIP 用戶優先處理</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ScrollArea className="h-48">
                  {whitelist.length > 0 ? (
                    <div className="space-y-2">
                      {whitelist.map((user: any) => (
                        <div key={user.user_id} className="flex items-center justify-between p-2 border rounded">
                          <span>{user.user_id}</span>
                          <Button size="sm" variant="ghost" onClick={() => removeFromList("whitelist", user.user_id)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-8">暫無白名單用戶</p>
                  )}
                </ScrollArea>
                <div className="flex gap-2">
                  <Input 
                    placeholder="用戶 ID"
                    value={newUserId}
                    onChange={(e) => setNewUserId(e.target.value)}
                  />
                  <Button onClick={() => addToList("whitelist")} disabled={!newUserId}>
                    添加
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <XCircle className="h-5 w-5 text-red-500" />
                  黑名單
                </CardTitle>
                <CardDescription>禁止互動用戶</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ScrollArea className="h-48">
                  {blacklist.length > 0 ? (
                    <div className="space-y-2">
                      {blacklist.map((user: any) => (
                        <div key={user.user_id} className="flex items-center justify-between p-2 border rounded">
                          <div>
                            <span>{user.user_id}</span>
                            {user.reason && <p className="text-xs text-muted-foreground">{user.reason}</p>}
                          </div>
                          <Button size="sm" variant="ghost" onClick={() => removeFromList("blacklist", user.user_id)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-8">暫無黑名單用戶</p>
                  )}
                </ScrollArea>
                <div className="space-y-2">
                  <Input 
                    placeholder="用戶 ID"
                    value={newUserId}
                    onChange={(e) => setNewUserId(e.target.value)}
                  />
                  <Input 
                    placeholder="原因（可選）"
                    value={newUserReason}
                    onChange={(e) => setNewUserReason(e.target.value)}
                  />
                  <Button onClick={() => addToList("blacklist")} disabled={!newUserId} variant="destructive">
                    添加到黑名單
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 多語言 */}
        <TabsContent value="language" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>多語言配置</CardTitle>
              <CardDescription>自動檢測和翻譯</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>啟用多語言</Label>
                <Switch 
                  checked={languageConfig.enabled}
                  onCheckedChange={(checked) => setLanguageConfig({...languageConfig, enabled: checked})}
                />
              </div>
              <div className="space-y-2">
                <Label>默認語言</Label>
                <Select 
                  value={languageConfig.default_language}
                  onValueChange={(value) => setLanguageConfig({...languageConfig, default_language: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {LANGUAGES.map(lang => (
                      <SelectItem key={lang.code} value={lang.code}>
                        {lang.flag} {lang.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center justify-between">
                <Label>自動檢測語言</Label>
                <Switch 
                  checked={languageConfig.auto_detect}
                  onCheckedChange={(checked) => setLanguageConfig({...languageConfig, auto_detect: checked})}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label>翻譯收到的消息</Label>
                <Switch 
                  checked={languageConfig.translate_incoming}
                  onCheckedChange={(checked) => setLanguageConfig({...languageConfig, translate_incoming: checked})}
                />
              </div>
              
              <Separator />
              
              <div className="grid grid-cols-4 gap-2">
                {LANGUAGES.map(lang => (
                  <div key={lang.code} className="p-3 border rounded-lg text-center">
                    <span className="text-2xl">{lang.flag}</span>
                    <p className="text-sm mt-1">{lang.name}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Webhook */}
        <TabsContent value="webhook" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Webhook 管理</CardTitle>
              <CardDescription>接收事件通知</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* 現有 Webhook */}
              <div className="space-y-3">
                {webhooks.map(webhook => (
                  <div key={webhook.webhook_id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <h4 className="font-medium">{webhook.name}</h4>
                      <p className="text-sm text-muted-foreground">{webhook.url}</p>
                      <div className="flex gap-1 mt-1">
                        {webhook.events?.slice(0, 3).map((event: string) => (
                          <Badge key={event} variant="outline" className="text-xs">{event}</Badge>
                        ))}
                        {webhook.events?.length > 3 && (
                          <Badge variant="outline" className="text-xs">+{webhook.events.length - 3}</Badge>
                        )}
                      </div>
                    </div>
                    <Switch checked={webhook.enabled} />
                  </div>
                ))}
                {webhooks.length === 0 && (
                  <p className="text-muted-foreground text-center py-8">暫無 Webhook</p>
                )}
              </div>
              
              <Separator />
              
              {/* 創建新 Webhook */}
              <div className="space-y-4">
                <h4 className="font-medium">創建新 Webhook</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>名稱</Label>
                    <Input 
                      placeholder="Webhook 名稱"
                      value={newWebhook.name}
                      onChange={(e) => setNewWebhook({...newWebhook, name: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>URL</Label>
                    <Input 
                      placeholder="https://..."
                      value={newWebhook.url}
                      onChange={(e) => setNewWebhook({...newWebhook, url: e.target.value})}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>事件</Label>
                  <div className="flex flex-wrap gap-2">
                    {WEBHOOK_EVENTS.map(event => (
                      <Badge 
                        key={event.id}
                        variant={newWebhook.events.includes(event.id) ? "default" : "outline"}
                        className="cursor-pointer"
                        onClick={() => {
                          if (newWebhook.events.includes(event.id)) {
                            setNewWebhook({...newWebhook, events: newWebhook.events.filter(e => e !== event.id)})
                          } else {
                            setNewWebhook({...newWebhook, events: [...newWebhook.events, event.id]})
                          }
                        }}
                      >
                        {event.name}
                      </Badge>
                    ))}
                  </div>
                </div>
                <Button onClick={createWebhook} disabled={!newWebhook.name || !newWebhook.url}>
                  <Plus className="h-4 w-4 mr-2" />
                  創建 Webhook
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
