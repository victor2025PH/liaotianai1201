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
import { Plus, Edit, Trash2, RefreshCw, Clock, CheckCircle2, XCircle, Loader2, Calendar, FileText } from "lucide-react"

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
  listScheduledMessages,
  createScheduledMessage,
  updateScheduledMessage,
  deleteScheduledMessage,
  getScheduledMessageLogs,
  type ScheduledMessageTask,
  type ScheduledMessageCreate,
  type ScheduledMessageUpdate,
  type ScheduledMessageLog,
} from "@/lib/api/group-ai"

export default function ScheduledMessagesPage() {
  const { toast } = useToast()
  const [tasks, setTasks] = useState<ScheduledMessageTask[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingTask, setEditingTask] = useState<ScheduledMessageTask | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deletingTaskId, setDeletingTaskId] = useState<string | null>(null)
  const [logsDialogOpen, setLogsDialogOpen] = useState(false)
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [taskLogs, setTaskLogs] = useState<ScheduledMessageLog[]>([])

  const [formData, setFormData] = useState<ScheduledMessageCreate>({
    task_id: "",
    name: "",
    enabled: true,
    schedule_type: "cron",
    cron_expression: "",
    groups: [],
    accounts: [],
    message_template: "",
    rotation: false,
    timezone: "Asia/Shanghai",
  })
  const [scheduleType, setScheduleType] = useState<"cron" | "interval" | "once">("cron")
  const [groupInput, setGroupInput] = useState("")
  const [accountInput, setAccountInput] = useState("")

  const fetchTasks = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await listScheduledMessages()
      setTasks(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "加載失敗")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
  }, [])

  const handleCreate = async () => {
    try {
      if (!formData.task_id || !formData.name || !formData.message_template) {
        toast({
          title: "驗證失敗",
          description: "請填寫任務 ID、名稱和消息模板",
          variant: "destructive",
        })
        return
      }
      await createScheduledMessage(formData)
      toast({
        title: "成功",
        description: "定時消息任務已創建",
      })
      setDialogOpen(false)
      resetForm()
      await fetchTasks()
    } catch (err) {
      toast({
        title: "創建失敗",
        description: err instanceof Error ? err.message : "無法創建任務",
        variant: "destructive",
      })
    }
  }

  const handleUpdate = async () => {
    if (!editingTask) return

    try {
      const update: ScheduledMessageUpdate = {
        name: formData.name,
        enabled: formData.enabled,
        schedule_type: formData.schedule_type,
        cron_expression: formData.cron_expression,
        interval_seconds: formData.interval_seconds,
        groups: formData.groups,
        accounts: formData.accounts,
        message_template: formData.message_template,
        rotation: formData.rotation,
      }
      await updateScheduledMessage(editingTask.task_id, update)
      toast({
        title: "成功",
        description: "任務已更新",
      })
      setDialogOpen(false)
      resetForm()
      await fetchTasks()
    } catch (err) {
      toast({
        title: "更新失敗",
        description: err instanceof Error ? err.message : "無法更新任務",
        variant: "destructive",
      })
    }
  }

  const handleDelete = async () => {
    if (!deletingTaskId) return

    try {
      await deleteScheduledMessage(deletingTaskId)
      toast({
        title: "成功",
        description: "任務已刪除",
      })
      setDeleteDialogOpen(false)
      setDeletingTaskId(null)
      await fetchTasks()
    } catch (err) {
      toast({
        title: "刪除失敗",
        description: err instanceof Error ? err.message : "無法刪除任務",
        variant: "destructive",
      })
    }
  }

  const handleViewLogs = async (taskId: string) => {
    try {
      setSelectedTaskId(taskId)
      const logs = await getScheduledMessageLogs(taskId, { limit: 50 })
      setTaskLogs(logs)
      setLogsDialogOpen(true)
    } catch (err) {
      toast({
        title: "加載日誌失敗",
        description: err instanceof Error ? err.message : "無法加載任務日誌",
        variant: "destructive",
      })
    }
  }

  const openEditDialog = (task: ScheduledMessageTask) => {
    setEditingTask(task)
    setFormData({
      task_id: task.task_id,
      name: task.name,
      enabled: task.enabled,
      schedule_type: task.schedule_type,
      cron_expression: task.cron_expression,
      interval_seconds: task.interval_seconds,
      groups: task.groups,
      accounts: task.accounts,
      message_template: task.message_template,
      rotation: task.rotation,
      timezone: task.timezone,
    })
    setScheduleType(task.schedule_type === "cron" ? "cron" : task.schedule_type === "interval" ? "interval" : "once")
    setDialogOpen(true)
  }

  const resetForm = () => {
    setFormData({
      task_id: "",
      name: "",
      enabled: true,
      schedule_type: "cron",
      cron_expression: "",
      groups: [],
      accounts: [],
      message_template: "",
      rotation: false,
      timezone: "Asia/Shanghai",
    })
    setEditingTask(null)
    setScheduleType("cron")
    setGroupInput("")
    setAccountInput("")
  }

  const addGroup = () => {
    const groupId = parseInt(groupInput)
    if (!isNaN(groupId) && !formData.groups.includes(groupId)) {
      setFormData({
        ...formData,
        groups: [...formData.groups, groupId],
      })
      setGroupInput("")
    }
  }

  const removeGroup = (groupId: number) => {
    setFormData({
      ...formData,
      groups: formData.groups.filter((g) => g !== groupId),
    })
  }

  const addAccount = () => {
    if (accountInput.trim() && !formData.accounts.includes(accountInput.trim())) {
      setFormData({
        ...formData,
        accounts: [...formData.accounts, accountInput.trim()],
      })
      setAccountInput("")
    }
  }

  const removeAccount = (accountId: string) => {
    setFormData({
      ...formData,
      accounts: formData.accounts.filter((a) => a !== accountId),
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
          <h1 className="text-3xl font-bold">定時消息任務</h1>
          <p className="text-muted-foreground">配置定時發送消息到指定群組</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchTasks}>
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
          <Button onClick={() => { resetForm(); setDialogOpen(true) }}>
            <Plus className="h-4 w-4 mr-2" />
            創建任務
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
          <CardTitle>任務列表</CardTitle>
          <CardDescription>共 {tasks.length} 個任務</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>任務 ID</TableHead>
                <TableHead>名稱</TableHead>
                <TableHead>調度類型</TableHead>
                <TableHead>群組數</TableHead>
                <TableHead>賬號數</TableHead>
                <TableHead>執行次數</TableHead>
                <TableHead>成功率</TableHead>
                <TableHead>下次執行</TableHead>
                <TableHead>狀態</TableHead>
                <TableHead>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tasks.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} className="text-center text-muted-foreground">
                    暫無任務，點擊「創建任務」開始
                  </TableCell>
                </TableRow>
              ) : (
                tasks.map((task) => (
                  <TableRow key={task.id}>
                    <TableCell className="font-mono text-sm">{task.task_id}</TableCell>
                    <TableCell>{task.name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{task.schedule_type}</Badge>
                    </TableCell>
                    <TableCell>{task.groups.length}</TableCell>
                    <TableCell>{task.accounts.length}</TableCell>
                    <TableCell>{task.run_count}</TableCell>
                    <TableCell>
                      {task.run_count > 0
                        ? `${Math.round((task.success_count / task.run_count) * 100)}%`
                        : "-"}
                    </TableCell>
                    <TableCell>{formatDate(task.next_run_at)}</TableCell>
                    <TableCell>
                      {task.enabled ? (
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
                          onClick={() => handleViewLogs(task.task_id)}
                        >
                          <FileText className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditDialog(task)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setDeletingTaskId(task.task_id)
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
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingTask ? "編輯任務" : "創建任務"}</DialogTitle>
            <DialogDescription>
              {editingTask ? "修改定時消息任務配置" : "創建新的定時消息任務"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {!editingTask && (
              <div>
                <Label htmlFor="task_id">任務 ID *</Label>
                <Input
                  id="task_id"
                  value={formData.task_id}
                  onChange={(e) => setFormData({ ...formData, task_id: e.target.value })}
                  placeholder="例如：task_001"
                />
              </div>
            )}
            <div>
              <Label htmlFor="name">任務名稱 *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="例如：每日問候"
              />
            </div>
            <div>
              <Label>調度類型</Label>
              <Tabs value={scheduleType} onValueChange={(v) => {
                setScheduleType(v as "cron" | "interval" | "once")
                setFormData({ ...formData, schedule_type: v as any })
              }}>
                <TabsList>
                  <TabsTrigger value="cron">Cron 表達式</TabsTrigger>
                  <TabsTrigger value="interval">間隔調度</TabsTrigger>
                  <TabsTrigger value="once">一次性</TabsTrigger>
                </TabsList>
                <TabsContent value="cron" className="space-y-2">
                  <Input
                    value={formData.cron_expression || ""}
                    onChange={(e) => setFormData({ ...formData, cron_expression: e.target.value })}
                    placeholder="例如：0 9 * * * (每天 9 點)"
                  />
                  <p className="text-sm text-muted-foreground">
                    格式：分 時 日 月 星期。例如：0 9 * * * 表示每天 9 點
                  </p>
                </TabsContent>
                <TabsContent value="interval" className="space-y-2">
                  <Input
                    type="number"
                    value={formData.interval_seconds || ""}
                    onChange={(e) => setFormData({ ...formData, interval_seconds: parseInt(e.target.value) || undefined })}
                    placeholder="間隔秒數，例如：3600 (每小時)"
                  />
                </TabsContent>
                <TabsContent value="once" className="space-y-2">
                  <Input
                    type="datetime-local"
                    onChange={(e) => {
                      // 轉換為 ISO 字符串
                      const date = new Date(e.target.value)
                      setFormData({ ...formData, cron_expression: date.toISOString() })
                    }}
                  />
                </TabsContent>
              </Tabs>
            </div>
            <div>
              <Label>目標群組</Label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  value={groupInput}
                  onChange={(e) => setGroupInput(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && addGroup()}
                  placeholder="輸入群組 ID 後按 Enter"
                />
                <Button type="button" onClick={addGroup}>添加</Button>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.groups.map((groupId) => (
                  <Badge key={groupId} variant="secondary" className="cursor-pointer" onClick={() => removeGroup(groupId)}>
                    {groupId} ×
                  </Badge>
                ))}
              </div>
            </div>
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
                {formData.accounts.map((accountId) => (
                  <Badge key={accountId} variant="secondary" className="cursor-pointer" onClick={() => removeAccount(accountId)}>
                    {accountId} ×
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <Label htmlFor="message_template">消息模板 *</Label>
              <Textarea
                id="message_template"
                value={formData.message_template}
                onChange={(e) => setFormData({ ...formData, message_template: e.target.value })}
                placeholder="例如：早上好！今天是 {{date}}，祝大家工作順利！"
                rows={4}
              />
              <p className="text-sm text-muted-foreground mt-1">
                支持變量：{"{{date}}"}, {"{{time}}"}, {"{{datetime}}"}, {"{{weekday}}"}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                checked={formData.rotation}
                onCheckedChange={(checked) => setFormData({ ...formData, rotation: checked })}
              />
              <Label>輪流發送</Label>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                checked={formData.enabled}
                onCheckedChange={(checked) => setFormData({ ...formData, enabled: checked })}
              />
              <Label>啟用任務</Label>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => { setDialogOpen(false); resetForm() }}>
                取消
              </Button>
              <Button onClick={editingTask ? handleUpdate : handleCreate}>
                {editingTask ? "更新" : "創建"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 執行日誌對話框 */}
      <Dialog open={logsDialogOpen} onOpenChange={setLogsDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>執行日誌 - {selectedTaskId}</DialogTitle>
            <DialogDescription>查看任務執行歷史記錄</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            {taskLogs.length === 0 ? (
              <p className="text-center text-muted-foreground">暫無日誌</p>
            ) : (
              taskLogs.map((log) => (
                <Card key={log.id}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-2">
                          {log.success ? (
                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-500" />
                          )}
                          <span className="font-medium">群組 {log.group_id}</span>
                          <span className="text-sm text-muted-foreground">賬號 {log.account_id}</span>
                        </div>
                        {log.message_sent && (
                          <p className="text-sm text-muted-foreground mt-1">{log.message_sent}</p>
                        )}
                        {log.error_message && (
                          <p className="text-sm text-red-500 mt-1">{log.error_message}</p>
                        )}
                      </div>
                      <span className="text-sm text-muted-foreground">{formatDate(log.executed_at)}</span>
                    </div>
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
              確定要刪除任務 {deletingTaskId} 嗎？此操作無法撤銷。
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
