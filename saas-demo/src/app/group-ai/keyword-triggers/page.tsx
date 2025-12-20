"use client"

import { useState, useEffect } from "react"
import dynamic from "next/dynamic"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useToast } from "@/hooks/use-toast"
import { Plus, Edit, Trash2, RefreshCw, Zap, CheckCircle2, XCircle, Loader2 } from "lucide-react"

const Table = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.Table })), { ssr: false })
const TableBody = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableBody })), { ssr: false })
const TableCell = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableCell })), { ssr: false })
const TableHead = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableHead })), { ssr: false })
const TableHeader = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableHeader })), { ssr: false })
const TableRow = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableRow })), { ssr: false })
const Dialog = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.Dialog })), { ssr: false })
const DialogContent = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogContent })), { ssr: false })
const DialogDescription = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogDescription })), { ssr: false })
const DialogHeader = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogHeader })), { ssr: false })
const DialogTitle = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogTitle })), { ssr: false })
const Textarea = dynamic(() => import("@/components/ui/textarea").then(mod => ({ default: mod.Textarea })), { ssr: false })
const Select = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.Select })), { ssr: false })
const SelectContent = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectContent })), { ssr: false })
const SelectItem = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectItem })), { ssr: false })
const SelectTrigger = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectTrigger })), { ssr: false })
const SelectValue = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectValue })), { ssr: false })
const AlertDialog = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialog })), { ssr: false })
const AlertDialogAction = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogAction })), { ssr: false })
const AlertDialogCancel = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogCancel })), { ssr: false })
const AlertDialogContent = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogContent })), { ssr: false })
const AlertDialogDescription = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogDescription })), { ssr: false })
const AlertDialogFooter = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogFooter })), { ssr: false })
const AlertDialogHeader = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogHeader })), { ssr: false })
const AlertDialogTitle = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogTitle })), { ssr: false })
const Switch = dynamic(() => import("@/components/ui/switch").then(mod => ({ default: mod.Switch })), { ssr: false })

import {
  listKeywordTriggers,
  createKeywordTrigger,
  updateKeywordTrigger,
  deleteKeywordTrigger,
  type KeywordTriggerRule,
  type KeywordTriggerCreate,
  type KeywordTriggerUpdate,
} from "@/lib/api/group-ai"

export default function KeywordTriggersPage() {
  const { toast } = useToast()
  const [rules, setRules] = useState<KeywordTriggerRule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<KeywordTriggerRule | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deletingRuleId, setDeletingRuleId] = useState<string | null>(null)

  const [formData, setFormData] = useState<KeywordTriggerCreate>({
    rule_id: "",
    name: "",
    enabled: true,
    keywords: [],
    match_type: "any",
    case_sensitive: false,
    sender_ids: [],
    sender_blacklist: [],
    weekdays: [],
    group_ids: [],
    condition_logic: "AND",
    actions: [],
    priority: 0,
    context_window: 0,
  })
  const [keywordInput, setKeywordInput] = useState("")
  const [actionType, setActionType] = useState("send_message")
  const [actionMessage, setActionMessage] = useState("")

  const fetchRules = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await listKeywordTriggers()
      setRules(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "加載失敗")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRules()
  }, [])

  const handleCreate = async () => {
    try {
      if (!formData.rule_id || !formData.name) {
        toast({
          title: "驗證失敗",
          description: "請填寫規則 ID 和名稱",
          variant: "destructive",
        })
        return
      }
      await createKeywordTrigger(formData)
      toast({
        title: "成功",
        description: "關鍵詞觸發規則已創建",
      })
      setDialogOpen(false)
      resetForm()
      await fetchRules()
    } catch (err) {
      toast({
        title: "創建失敗",
        description: err instanceof Error ? err.message : "無法創建規則",
        variant: "destructive",
      })
    }
  }

  const handleUpdate = async () => {
    if (!editingRule) return

    try {
      const update: KeywordTriggerUpdate = {
        name: formData.name,
        enabled: formData.enabled,
        keywords: formData.keywords,
        match_type: formData.match_type,
        actions: formData.actions,
        priority: formData.priority,
      }
      await updateKeywordTrigger(editingRule.rule_id, update)
      toast({
        title: "成功",
        description: "規則已更新",
      })
      setDialogOpen(false)
      resetForm()
      await fetchRules()
    } catch (err) {
      toast({
        title: "更新失敗",
        description: err instanceof Error ? err.message : "無法更新規則",
        variant: "destructive",
      })
    }
  }

  const handleDelete = async () => {
    if (!deletingRuleId) return

    try {
      await deleteKeywordTrigger(deletingRuleId)
      toast({
        title: "成功",
        description: "規則已刪除",
      })
      setDeleteDialogOpen(false)
      setDeletingRuleId(null)
      await fetchRules()
    } catch (err) {
      toast({
        title: "刪除失敗",
        description: err instanceof Error ? err.message : "無法刪除規則",
        variant: "destructive",
      })
    }
  }

  const openEditDialog = (rule: KeywordTriggerRule) => {
    setEditingRule(rule)
    setFormData({
      rule_id: rule.rule_id,
      name: rule.name,
      enabled: rule.enabled,
      keywords: rule.keywords,
      match_type: rule.match_type,
      case_sensitive: rule.case_sensitive,
      sender_ids: rule.sender_ids,
      sender_blacklist: rule.sender_blacklist,
      weekdays: rule.weekdays,
      group_ids: rule.group_ids,
      condition_logic: rule.condition_logic,
      actions: rule.actions,
      priority: rule.priority,
      context_window: rule.context_window,
    })
    setDialogOpen(true)
  }

  const resetForm = () => {
    setFormData({
      rule_id: "",
      name: "",
      enabled: true,
      keywords: [],
      match_type: "any",
      case_sensitive: false,
      sender_ids: [],
      sender_blacklist: [],
      weekdays: [],
      group_ids: [],
      condition_logic: "AND",
      actions: [],
      priority: 0,
      context_window: 0,
    })
    setEditingRule(null)
    setKeywordInput("")
    setActionMessage("")
  }

  const addKeyword = () => {
    if (keywordInput.trim()) {
      setFormData({
        ...formData,
        keywords: [...formData.keywords, keywordInput.trim()],
      })
      setKeywordInput("")
    }
  }

  const removeKeyword = (index: number) => {
    setFormData({
      ...formData,
      keywords: formData.keywords.filter((_, i) => i !== index),
    })
  }

  const addAction = () => {
    if (actionMessage.trim()) {
      setFormData({
        ...formData,
        actions: [
          ...formData.actions,
          {
            type: actionType,
            params: { message: actionMessage },
            delay_min: 1,
            delay_max: 3,
          },
        ],
      })
      setActionMessage("")
    }
  }

  const removeAction = (index: number) => {
    setFormData({
      ...formData,
      actions: formData.actions.filter((_, i) => i !== index),
    })
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-4">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">關鍵詞觸發規則</h1>
          <p className="text-muted-foreground">配置關鍵詞觸發規則，自動執行動作</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchRules}>
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
          <Button onClick={() => { resetForm(); setDialogOpen(true) }}>
            <Plus className="h-4 w-4 mr-2" />
            創建規則
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>規則列表</CardTitle>
          <CardDescription>共 {rules.length} 個規則</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>規則 ID</TableHead>
                <TableHead>名稱</TableHead>
                <TableHead>關鍵詞</TableHead>
                <TableHead>匹配類型</TableHead>
                <TableHead>動作</TableHead>
                <TableHead>優先級</TableHead>
                <TableHead>觸發次數</TableHead>
                <TableHead>狀態</TableHead>
                <TableHead>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rules.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center text-muted-foreground">
                    暫無規則，點擊「創建規則」開始
                  </TableCell>
                </TableRow>
              ) : (
                rules.map((rule) => (
                  <TableRow key={rule.id}>
                    <TableCell className="font-mono text-sm">{rule.rule_id}</TableCell>
                    <TableCell>{rule.name}</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {rule.keywords.slice(0, 3).map((kw, i) => (
                          <Badge key={i} variant="secondary">{kw}</Badge>
                        ))}
                        {rule.keywords.length > 3 && (
                          <Badge variant="outline">+{rule.keywords.length - 3}</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{rule.match_type}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{rule.actions.length} 個動作</Badge>
                    </TableCell>
                    <TableCell>{rule.priority}</TableCell>
                    <TableCell>{rule.trigger_count}</TableCell>
                    <TableCell>
                      {rule.enabled ? (
                        <Badge variant="default" className="bg-green-500">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          啟用
                        </Badge>
                      ) : (
                        <Badge variant="secondary">
                          <XCircle className="h-3 w-3 mr-1" />
                          停用
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditDialog(rule)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setDeletingRuleId(rule.rule_id)
                            setDeleteDialogOpen(true)
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 創建/編輯對話框 */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingRule ? "編輯規則" : "創建規則"}</DialogTitle>
            <DialogDescription>
              {editingRule ? "修改關鍵詞觸發規則配置" : "創建新的關鍵詞觸發規則"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {!editingRule && (
              <div>
                <Label htmlFor="rule_id">規則 ID *</Label>
                <Input
                  id="rule_id"
                  value={formData.rule_id}
                  onChange={(e) => setFormData({ ...formData, rule_id: e.target.value })}
                  placeholder="例如：rule_001"
                />
              </div>
            )}
            <div>
              <Label htmlFor="name">規則名稱 *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="例如：紅包提醒"
              />
            </div>
            <div>
              <Label htmlFor="match_type">匹配類型</Label>
              <Select
                value={formData.match_type}
                onValueChange={(value: any) => setFormData({ ...formData, match_type: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">任意關鍵詞 (OR)</SelectItem>
                  <SelectItem value="all">所有關鍵詞 (AND)</SelectItem>
                  <SelectItem value="regex">正則表達式</SelectItem>
                  <SelectItem value="simple">簡單匹配</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>關鍵詞列表</Label>
              <div className="flex gap-2">
                <Input
                  value={keywordInput}
                  onChange={(e) => setKeywordInput(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && addKeyword()}
                  placeholder="輸入關鍵詞後按 Enter"
                />
                <Button type="button" onClick={addKeyword}>添加</Button>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.keywords.map((kw, i) => (
                  <Badge key={i} variant="secondary" className="cursor-pointer" onClick={() => removeKeyword(i)}>
                    {kw} ×
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <Label>觸發動作</Label>
              <div className="space-y-2">
                <div className="flex gap-2">
                  <Select value={actionType} onValueChange={setActionType}>
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="send_message">發送消息</SelectItem>
                      <SelectItem value="grab_redpacket">搶紅包</SelectItem>
                    </SelectContent>
                  </Select>
                  <Input
                    value={actionMessage}
                    onChange={(e) => setActionMessage(e.target.value)}
                    placeholder="動作參數（如消息內容）"
                    className="flex-1"
                  />
                  <Button type="button" onClick={addAction}>添加動作</Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.actions.map((action, i) => (
                    <Badge key={i} variant="secondary" className="cursor-pointer" onClick={() => removeAction(i)}>
                      {action.type}: {JSON.stringify(action.params)} ×
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
            <div>
              <Label htmlFor="priority">優先級</Label>
              <Input
                id="priority"
                type="number"
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
              />
            </div>
            <div className="flex items-center gap-2">
              <Switch
                checked={formData.enabled}
                onCheckedChange={(checked) => setFormData({ ...formData, enabled: checked })}
              />
              <Label>啟用規則</Label>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => { setDialogOpen(false); resetForm() }}>
                取消
              </Button>
              <Button onClick={editingRule ? handleUpdate : handleCreate}>
                {editingRule ? "更新" : "創建"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 刪除確認對話框 */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>確認刪除</AlertDialogTitle>
            <AlertDialogDescription>
              確定要刪除規則 {deletingRuleId} 嗎？此操作無法撤銷。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
              刪除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
