"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useToast } from "@/hooks/use-toast"
import { ArrowLeft, Save } from "lucide-react"
import { getAccountParams, updateAccountParams, type AccountParams } from "@/lib/api/group-ai"

export default function AccountParamsPage() {
  const routeParams = useParams()
  const router = useRouter()
  const accountId = routeParams.accountId as string
  
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [accountParams, setAccountParams] = useState<AccountParams>({
    reply_rate: 0.5,
    redpacket_enabled: true,
    redpacket_probability: 0.5,
    max_replies_per_hour: 100,
    min_reply_interval: 5,
    active: true,
    work_hours_start: 9,
    work_hours_end: 18,
    work_days: [0, 1, 2, 3, 4, 5, 6],
    keyword_whitelist: [],
    keyword_blacklist: [],
    ai_temperature: 0.7,
    ai_max_tokens: 500,
    reply_priority: 5,
  })
  
  const { toast } = useToast()

  useEffect(() => {
    fetchParams()
  }, [accountId])

  const fetchParams = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getAccountParams(accountId)
      setAccountParams(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "加載失敗")
      toast({
        title: "錯誤",
        description: "無法加載賬號參數",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      await updateAccountParams(accountId, accountParams)
      toast({
        title: "成功",
        description: "參數已更新",
      })
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "更新失敗",
        variant: "destructive",
      })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          返回
        </Button>
        <div>
          <h1 className="text-3xl font-bold">賬號參數調整</h1>
          <p className="text-muted-foreground mt-2">調整賬號 {accountId} 的行為參數</p>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>回復參數</CardTitle>
          <CardDescription>控制 AI 賬號的回復行為</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="active">啟用狀態</Label>
              <p className="text-sm text-muted-foreground">是否啟用此賬號</p>
            </div>
            <Switch
              id="active"
              checked={accountParams.active ?? true}
              onCheckedChange={(checked) => setAccountParams({ ...accountParams, active: checked })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="reply_rate">回復頻率</Label>
            <p className="text-sm text-muted-foreground">
              回復概率 (0-1)，當前: {accountParams.reply_rate ?? 0.5}
            </p>
            <Input
              id="reply_rate"
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={accountParams.reply_rate ?? 0.5}
              onChange={(e) =>
                setAccountParams({ ...accountParams, reply_rate: parseFloat(e.target.value) })
              }
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="max_replies_per_hour">每小時最大回復數</Label>
            <p className="text-sm text-muted-foreground">
              限制每小時最多回復的次數，當前: {accountParams.max_replies_per_hour ?? 100}
            </p>
            <Input
              id="max_replies_per_hour"
              type="number"
              min="0"
              value={accountParams.max_replies_per_hour ?? 100}
              onChange={(e) =>
                setAccountParams({ ...accountParams, max_replies_per_hour: parseInt(e.target.value) })
              }
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="min_reply_interval">最小回復間隔（秒）</Label>
            <p className="text-sm text-muted-foreground">
              兩次回復之間的最小間隔時間，當前: {accountParams.min_reply_interval ?? 5} 秒
            </p>
            <Input
              id="min_reply_interval"
              type="number"
              min="0"
              value={accountParams.min_reply_interval ?? 5}
              onChange={(e) =>
                setAccountParams({ ...accountParams, min_reply_interval: parseInt(e.target.value) })
              }
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>紅包參數</CardTitle>
          <CardDescription>控制 AI 賬號的紅包參與行為</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="redpacket_enabled">啟用紅包</Label>
              <p className="text-sm text-muted-foreground">是否啟用紅包參與功能</p>
            </div>
            <Switch
              id="redpacket_enabled"
              checked={accountParams.redpacket_enabled ?? true}
              onCheckedChange={(checked) =>
                setAccountParams({ ...accountParams, redpacket_enabled: checked })
              }
            />
          </div>

          {accountParams.redpacket_enabled && (
            <div className="space-y-2">
              <Label htmlFor="redpacket_probability">紅包參與概率</Label>
              <p className="text-sm text-muted-foreground">
                參與紅包的概率 (0-1)，當前: {accountParams.redpacket_probability ?? 0.5}
              </p>
              <Input
                id="redpacket_probability"
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={accountParams.redpacket_probability ?? 0.5}
                onChange={(e) =>
                  setAccountParams({
                    ...accountParams,
                    redpacket_probability: parseFloat(e.target.value),
                  })
                }
              />
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>時間段控制</CardTitle>
          <CardDescription>設置賬號的工作時間和日期</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="work_hours_start">工作時間開始</Label>
              <p className="text-sm text-muted-foreground">小時 (0-23)</p>
              <Input
                id="work_hours_start"
                type="number"
                min="0"
                max="23"
                value={accountParams.work_hours_start ?? 9}
                onChange={(e) =>
                  setAccountParams({
                    ...accountParams,
                    work_hours_start: parseInt(e.target.value),
                  })
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="work_hours_end">工作時間結束</Label>
              <p className="text-sm text-muted-foreground">小時 (0-23)</p>
              <Input
                id="work_hours_end"
                type="number"
                min="0"
                max="23"
                value={accountParams.work_hours_end ?? 18}
                onChange={(e) =>
                  setAccountParams({
                    ...accountParams,
                    work_hours_end: parseInt(e.target.value),
                  })
                }
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>關鍵詞過濾</CardTitle>
          <CardDescription>設置關鍵詞白名單和黑名單</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="keyword_whitelist">關鍵詞白名單</Label>
            <p className="text-sm text-muted-foreground">
              僅回復包含這些關鍵詞的消息（用逗號分隔）
            </p>
            <Input
              id="keyword_whitelist"
              placeholder="關鍵詞1,關鍵詞2,關鍵詞3"
              value={accountParams.keyword_whitelist?.join(", ") ?? ""}
              onChange={(e) =>
                setAccountParams({
                  ...accountParams,
                  keyword_whitelist: e.target.value
                    ? e.target.value.split(",").map((k) => k.trim()).filter(Boolean)
                    : [],
                })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="keyword_blacklist">關鍵詞黑名單</Label>
            <p className="text-sm text-muted-foreground">
              不回復包含這些關鍵詞的消息（用逗號分隔）
            </p>
            <Input
              id="keyword_blacklist"
              placeholder="關鍵詞1,關鍵詞2,關鍵詞3"
              value={accountParams.keyword_blacklist?.join(", ") ?? ""}
              onChange={(e) =>
                setAccountParams({
                  ...accountParams,
                  keyword_blacklist: e.target.value
                    ? e.target.value.split(",").map((k) => k.trim()).filter(Boolean)
                    : [],
                })
              }
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>AI 生成參數</CardTitle>
          <CardDescription>控制 AI 生成回復的參數</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="ai_temperature">AI 溫度</Label>
            <p className="text-sm text-muted-foreground">
              控制生成文本的隨機性 (0-2)，當前: {accountParams.ai_temperature ?? 0.7}
            </p>
            <Input
              id="ai_temperature"
              type="number"
              min="0"
              max="2"
              step="0.1"
              value={accountParams.ai_temperature ?? 0.7}
              onChange={(e) =>
                setAccountParams({
                  ...accountParams,
                  ai_temperature: parseFloat(e.target.value),
                })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="ai_max_tokens">最大 Token 數</Label>
            <p className="text-sm text-muted-foreground">
              限制生成文本的最大長度，當前: {accountParams.ai_max_tokens ?? 500}
            </p>
            <Input
              id="ai_max_tokens"
              type="number"
              min="1"
              max="4000"
              value={accountParams.ai_max_tokens ?? 500}
              onChange={(e) =>
                setAccountParams({
                  ...accountParams,
                  ai_max_tokens: parseInt(e.target.value),
                })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="reply_priority">回復優先級</Label>
            <p className="text-sm text-muted-foreground">
              設置回復的優先級 (1-10)，數字越大優先級越高，當前: {accountParams.reply_priority ?? 5}
            </p>
            <Input
              id="reply_priority"
              type="number"
              min="1"
              max="10"
              value={accountParams.reply_priority ?? 5}
              onChange={(e) =>
                setAccountParams({
                  ...accountParams,
                  reply_priority: parseInt(e.target.value),
                })
              }
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={() => router.back()}>
          取消
        </Button>
        <Button onClick={handleSave} disabled={saving}>
          <Save className="h-4 w-4 mr-2" />
          {saving ? "保存中..." : "保存"}
        </Button>
      </div>
    </div>
  )
}

