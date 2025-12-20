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
import { Plus, Edit, Trash2, RefreshCw, Users, Activity, CheckCircle2, XCircle, Link2, Search } from "lucide-react"

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
const Tabs = dynamic(() => import("@/components/ui/tabs").then(mod => ({ default: mod.Tabs })), { ssr: false })
const TabsContent = dynamic(() => import("@/components/ui/tabs").then(mod => ({ default: mod.TabsContent })), { ssr: false })
const TabsList = dynamic(() => import("@/components/ui/tabs").then(mod => ({ default: mod.TabsList })), { ssr: false })
const TabsTrigger = dynamic(() => import("@/components/ui/tabs").then(mod => ({ default: mod.TabsTrigger })), { ssr: false })

import {
  listGroupJoinConfigs,
  createGroupJoinConfig,
  updateGroupJoinConfig,
  deleteGroupJoinConfig,
  getGroupActivityMetrics,
  type GroupJoinConfig,
  type GroupJoinConfigCreate,
  type GroupJoinConfigUpdate,
  type GroupActivityMetrics,
} from "@/lib/api/group-ai"

export default function GroupManagementPage() {
  const { toast } = useToast()
  const [configs, setConfigs] = useState<GroupJoinConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingConfig, setEditingConfig] = useState<GroupJoinConfig | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deletingConfigId, setDeletingConfigId] = useState<string | null>(null)
  const [metricsDialogOpen, setMetricsDialogOpen] = useState(false)
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null)
  const [groupMetrics, setGroupMetrics] = useState<GroupActivityMetrics[]>([])
  const [activeTab, setActiveTab] = useState<"configs" | "metrics">("configs")

  const [formData, setFormData] = useState<GroupJoinConfigCreate>({
    config_id: "",
    name: "",
    enabled: true,
    join_type: "invite_link",
    invite_link: "",
    account_ids: [],
    priority: 0,
  })
  const [accountInput, setAccountInput] = useState("")
  const [groupInput, setGroupInput] = useState("")

  const fetchConfigs = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await listGroupJoinConfigs()
      setConfigs(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "加載失敗")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConfigs()
  }, [])

  const handleCreate = async () => {
    try {
      if (!formData.config_id || !formData.name) {
        toast({
          title: "驗證失敗",
          description: "請填寫配置 ID 和名稱",
          variant: "destructive",
        })
        return
      }
      if (formData.join_type === "invite_link" && !formData.invite_link) {
        toast({
          title: "驗證失敗",
          description: "請填寫邀請鏈接",
          variant: "destructive",
        })
        return
      }
      await createGroupJoinConfig(formData)
      toast({
        title: "成功",
        description: "群組加入配置已創建",
      })
      setDialogOpen(false)
      resetForm()
      await fetchConfigs()
    } catch (err) {
      toast({
        title: "創建失敗",
        description: err instanceof Error ? err.message : "無法創建配置",
        variant: "destructive",
      })
    }
  }

  const handleUpdate = async () => {
    if (!editingConfig) return

    try {
      const update: GroupJoinConfigUpdate = {
        name: formData.name,
        enabled: formData.enabled,
        join_type: formData.join_type,
        invite_link: formData.invite_link,
        username: formData.username,
        group_id: formData.group_id,
        account_ids: formData.account_ids,
        priority: formData.priority,
      }
      await updateGroupJoinConfig(editingConfig.config_id, update)
      toast({
        title: "成功",
        description: "配置已更新",
      })
      setDialogOpen(false)
      resetForm()
      await fetchConfigs()
    } catch (err) {
      toast({
        title: "更新失敗",
        description: err instanceof Error ? err.message : "無法更新配置",
        variant: "destructive",
      })
    }
  }

  const handleDelete = async () => {
    if (!deletingConfigId) return

    try {
      await deleteGroupJoinConfig(deletingConfigId)
      toast({
        title: "成功",
        description: "配置已刪除",
      })
      setDeleteDialogOpen(false)
      setDeletingConfigId(null)
      await fetchConfigs()
    } catch (err) {
      toast({
        title: "刪除失敗",
        description: err instanceof Error ? err.message : "無法刪除配置",
        variant: "destructive",
      })
    }
  }

  const handleViewMetrics = async (groupId: number) => {
    try {
      setSelectedGroupId(groupId)
      const metrics = await getGroupActivityMetrics(groupId, { limit: 50 })
      setGroupMetrics(metrics)
      setMetricsDialogOpen(true)
    } catch (err) {
      toast({
        title: "加載指標失敗",
        description: err instanceof Error ? err.message : "無法加載群組活動指標",
        variant: "destructive",
      })
    }
  }

  const openEditDialog = (config: GroupJoinConfig) => {
    setEditingConfig(config)
    setFormData({
      config_id: config.config_id,
      name: config.name,
      enabled: config.enabled,
      join_type: config.join_type,
      invite_link: config.invite_link,
      username: config.username,
      group_id: config.group_id,
      account_ids: config.account_ids,
      priority: config.priority,
    })
    setDialogOpen(true)
  }

  const resetForm = () => {
    setFormData({
      config_id: "",
      name: "",
      enabled: true,
      join_type: "invite_link",
      invite_link: "",
      account_ids: [],
      priority: 0,
    })
    setEditingConfig(null)
    setAccountInput("")
    setGroupInput("")
  }

  const addAccount = () => {
    if (accountInput.trim() && !formData.account_ids.includes(accountInput.trim())) {
      setFormData({
        ...formData,
        account_ids: [...formData.account_ids, accountInput.trim()],
      })
      setAccountInput("")
    }
  }

  const removeAccount = (accountId: string) => {
    setFormData({
      ...formData,
      account_ids: formData.account_ids.filter((a) => a !== accountId),
    })
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return "-"
    return new Date(dateString).toLocaleString("zh-TW")
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
          <h1 className="text-3xl font-bold">群組管理</h1>
          <p className="text-muted-foreground">配置自動加入群組和查看群組活動指標</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchConfigs}>
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
          <Button onClick={() => { resetForm(); setDialogOpen(true) }}>
            <Plus className="h-4 w-4 mr-2" />
            創建配置
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "configs" | "metrics")}>
        <TabsList>
          <TabsTrigger value="configs">加入配置</TabsTrigger>
          <TabsTrigger value="metrics">活動指標</TabsTrigger>
        </TabsList>

        <TabsContent value="configs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>群組加入配置</CardTitle>
              <CardDescription>共 {configs.length} 個配置</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>配置 ID</TableHead>
                    <TableHead>名稱</TableHead>
                    <TableHead>加入類型</TableHead>
                    <TableHead>目標</TableHead>
                    <TableHead>賬號數</TableHead>
                    <TableHead>加入次數</TableHead>
                    <TableHead>優先級</TableHead>
                    <TableHead>狀態</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {configs.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center text-muted-foreground">
                        暫無配置，點擊「創建配置」開始
                      </TableCell>
                    </TableRow>
                  ) : (
                    configs.map((config) => (
                      <TableRow key={config.id}>
                        <TableCell className="font-mono text-sm">{config.config_id}</TableCell>
                        <TableCell>{config.name}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{config.join_type}</Badge>
                        </TableCell>
                        <TableCell>
                          {config.invite_link && (
                            <div className="flex items-center gap-1">
                              <Link2 className="h-3 w-3" />
                              <span className="text-xs truncate max-w-[100px]">{config.invite_link}</span>
                            </div>
                          )}
                          {config.username && <span>@{config.username}</span>}
                          {config.group_id && <span className="font-mono">{config.group_id}</span>}
                        </TableCell>
                        <TableCell>{config.account_ids.length}</TableCell>
                        <TableCell>{config.join_count}</TableCell>
                        <TableCell>{config.priority}</TableCell>
                        <TableCell>
                          {config.enabled ? (
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
                              onClick={() => openEditDialog(config)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setDeletingConfigId(config.config_id)
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
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>群組活動指標</CardTitle>
              <CardDescription>查看群組活動數據和健康度</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    type="number"
                    value={groupInput}
                    onChange={(e) => setGroupInput(e.target.value)}
                    placeholder="輸入群組 ID"
                    className="max-w-xs"
                  />
                  <Button onClick={() => {
                    const groupId = parseInt(groupInput)
                    if (!isNaN(groupId)) {
                      handleViewMetrics(groupId)
                    }
                  }}>
                    <Search className="h-4 w-4 mr-2" />
                    查詢
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground">
                  輸入群組 ID 查看該群組的活動指標歷史記錄
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 創建/編輯對話框 */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingConfig ? "編輯配置" : "創建配置"}</DialogTitle>
            <DialogDescription>
              {editingConfig ? "修改群組加入配置" : "創建新的群組加入配置"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {!editingConfig && (
              <div>
                <Label htmlFor="config_id">配置 ID *</Label>
                <Input
                  id="config_id"
                  value={formData.config_id}
                  onChange={(e) => setFormData({ ...formData, config_id: e.target.value })}
                  placeholder="例如：join_001"
                />
              </div>
            )}
            <div>
              <Label htmlFor="name">配置名稱 *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="例如：示例群組"
              />
            </div>
            <div>
              <Label htmlFor="join_type">加入類型</Label>
              <Select
                value={formData.join_type}
                onValueChange={(value: any) => setFormData({ ...formData, join_type: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="invite_link">邀請鏈接</SelectItem>
                  <SelectItem value="username">用戶名</SelectItem>
                  <SelectItem value="group_id">群組 ID</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {formData.join_type === "invite_link" && (
              <div>
                <Label htmlFor="invite_link">邀請鏈接 *</Label>
                <Input
                  id="invite_link"
                  value={formData.invite_link || ""}
                  onChange={(e) => setFormData({ ...formData, invite_link: e.target.value })}
                  placeholder="https://t.me/joinchat/xxx"
                />
              </div>
            )}
            {formData.join_type === "username" && (
              <div>
                <Label htmlFor="username">用戶名 *</Label>
                <Input
                  id="username"
                  value={formData.username || ""}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  placeholder="@example_group"
                />
              </div>
            )}
            {formData.join_type === "group_id" && (
              <div>
                <Label htmlFor="group_id">群組 ID *</Label>
                <Input
                  id="group_id"
                  type="number"
                  value={formData.group_id || ""}
                  onChange={(e) => setFormData({ ...formData, group_id: parseInt(e.target.value) || undefined })}
                  placeholder="-1001234567890"
                />
              </div>
            )}
            <div>
              <Label>目標賬號</Label>
              <div className="flex gap-2">
                <Input
                  value={accountInput}
                  onChange={(e) => setAccountInput(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && addAccount()}
                  placeholder="輸入賬號 ID 後按 Enter"
                />
                <Button type="button" onClick={addAccount}>添加</Button>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.account_ids.map((accountId) => (
                  <Badge key={accountId} variant="secondary" className="cursor-pointer" onClick={() => removeAccount(accountId)}>
                    {accountId} ×
                  </Badge>
                ))}
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
              <Label>啟用配置</Label>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => { setDialogOpen(false); resetForm() }}>
                取消
              </Button>
              <Button onClick={editingConfig ? handleUpdate : handleCreate}>
                {editingConfig ? "更新" : "創建"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 活動指標對話框 */}
      <Dialog open={metricsDialogOpen} onOpenChange={setMetricsDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>群組活動指標 - {selectedGroupId}</DialogTitle>
            <DialogDescription>查看群組活動歷史記錄</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            {groupMetrics.length === 0 ? (
              <p className="text-center text-muted-foreground">暫無指標數據</p>
            ) : (
              groupMetrics.map((metric) => (
                <Card key={metric.id}>
                  <CardContent className="p-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">24小時消息數</p>
                        <p className="text-2xl font-bold">{metric.message_count_24h}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">活躍成員</p>
                        <p className="text-2xl font-bold">{metric.active_members_24h}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">新成員</p>
                        <p className="text-2xl font-bold">{metric.new_members_24h}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">健康度</p>
                        <p className="text-2xl font-bold">{Math.round(metric.health_score * 100)}%</p>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground mt-2">
                      記錄時間: {formatDate(metric.recorded_at)}
                    </p>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* 刪除確認對話框 */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>確認刪除</AlertDialogTitle>
            <AlertDialogDescription>
              確定要刪除配置 {deletingConfigId} 嗎？此操作無法撤銷。
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
