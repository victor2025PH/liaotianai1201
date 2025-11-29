"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useToast } from "@/hooks/use-toast"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog-center"
import { Plus, Play, Edit, Trash2, RefreshCw, Clock, Zap, Settings, CheckCircle2, XCircle, Loader2, Calendar, Timer } from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  listAutomationTasks,
  createAutomationTask,
  updateAutomationTask,
  deleteAutomationTask,
  runAutomationTask,
  getTaskLogs,
  type AutomationTask,
  type AutomationTaskCreate,
  type AutomationTaskUpdate,
  type AutomationTaskLog,
} from "@/lib/api/group-ai"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { PermissionGuard } from "@/components/permissions/permission-guard"
import { StepIndicator, type Step } from "@/components/step-indicator"
import Link from "next/link"

const workflowSteps: Step[] = [
  {
    number: 1,
    title: "剧本管理",
    description: "创建和管理 AI 对话剧本（必需）",
    href: "/group-ai/scripts",
    status: "completed",
  },
  {
    number: 2,
    title: "账号管理",
    description: "创建和管理 Telegram 账号，关联剧本",
    href: "/group-ai/accounts",
    status: "completed",
  },
  {
    number: 3,
    title: "角色分配",
    description: "從剧本提取角色並分配給账号（可选）",
    href: "/group-ai/role-assignments",
    status: "completed",
  },
  {
    number: 4,
    title: "分配方案",
    description: "保存和重用角色分配方案（可选）",
    href: "/group-ai/role-assignment-schemes",
    status: "completed",
  },
  {
    number: 5,
    title: "自动化任务",
    description: "配置自动化执行任务（可选）",
    href: "/group-ai/automation-tasks",
    status: "current",
  },
];

export default function AutomationTasksPage() {
  const { toast } = useToast()
  const [tasks, setTasks] = useState<AutomationTask[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingTask, setEditingTask] = useState<AutomationTask | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deletingTaskId, setDeletingTaskId] = useState<string | null>(null)
  const [logsDialogOpen, setLogsDialogOpen] = useState(false)
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [taskLogs, setTaskLogs] = useState<AutomationTaskLog[]>([])
  const [runningTaskId, setRunningTaskId] = useState<string | null>(null)
  const [scheduleType, setScheduleType] = useState<"cron" | "interval" | "template">("template")

  const [formData, setFormData] = useState<AutomationTaskCreate>({
    name: "",
    description: "",
    task_type: "scheduled",
    task_action: "alert_check",
    schedule_config: {},
    action_config: {},
    enabled: true,
    dependent_tasks: [],
    notify_on_success: false,
    notify_on_failure: true,
    notify_recipients: [],
  })
  const [selectedDependentTasks, setSelectedDependentTasks] = useState<string[]>([])
  const [notificationRecipient, setNotificationRecipient] = useState<string>("")

  const fetchTasks = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await listAutomationTasks()
      setTasks(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
  }, [])

  const handleCreate = async () => {
    try {
      await createAutomationTask(formData)
      toast({
        title: "成功",
        description: "自动化任务已创建",
      })
      setDialogOpen(false)
      resetForm()
      await fetchTasks()
    } catch (err) {
      toast({
        title: "创建失败",
        description: err instanceof Error ? err.message : "无法创建自动化任务",
        variant: "destructive",
      })
    }
  }

  const handleUpdate = async () => {
    if (!editingTask) return

    try {
      const update: AutomationTaskUpdate = {
        name: formData.name,
        description: formData.description,
        schedule_config: formData.schedule_config,
        action_config: formData.action_config,
        enabled: formData.enabled,
        dependent_tasks: formData.dependent_tasks,
        notify_on_success: formData.notify_on_success,
        notify_on_failure: formData.notify_on_failure,
        notify_recipients: formData.notify_recipients,
      }
      await updateAutomationTask(editingTask.id, update)
      toast({
        title: "成功",
        description: "自动化任务已更新",
      })
      setDialogOpen(false)
      resetForm()
      await fetchTasks()
    } catch (err) {
      toast({
        title: "更新失败",
        description: err instanceof Error ? err.message : "无法更新自动化任务",
        variant: "destructive",
      })
    }
  }

  const handleDelete = async () => {
    if (!deletingTaskId) return

    try {
      await deleteAutomationTask(deletingTaskId)
      toast({
        title: "成功",
        description: "自动化任务已删除",
      })
      setDeleteDialogOpen(false)
      setDeletingTaskId(null)
      await fetchTasks()
    } catch (err) {
      toast({
        title: "删除失败",
        description: err instanceof Error ? err.message : "无法删除自动化任务",
        variant: "destructive",
      })
    }
  }

  const handleRun = async (taskId: string) => {
    try {
      setRunningTaskId(taskId)
      await runAutomationTask(taskId)
      toast({
        title: "成功",
        description: "任务已提交执行",
      })
      await fetchTasks()
    } catch (err) {
      toast({
        title: "执行失败",
        description: err instanceof Error ? err.message : "无法执行任务",
        variant: "destructive",
      })
    } finally {
      setRunningTaskId(null)
    }
  }

  const handleViewLogs = async (taskId: string) => {
    try {
      setSelectedTaskId(taskId)
      const logs = await getTaskLogs(taskId, 50)
      setTaskLogs(logs)
      setLogsDialogOpen(true)
    } catch (err) {
      toast({
        title: "加载日志失败",
        description: err instanceof Error ? err.message : "无法加载任务日志",
        variant: "destructive",
      })
    }
  }

  const openEditDialog = (task: AutomationTask) => {
    setEditingTask(task)
    setFormData({
      name: task.name,
      description: task.description || "",
      task_type: task.task_type,
      task_action: task.task_action,
      schedule_config: task.schedule_config || {},
      action_config: task.action_config || {},
      enabled: task.enabled,
      dependent_tasks: task.dependent_tasks || [],
      notify_on_success: task.notify_on_success ?? false,
      notify_on_failure: task.notify_on_failure ?? true,
      notify_recipients: task.notify_recipients || [],
    })
    setSelectedDependentTasks(task.dependent_tasks || [])
    setNotificationRecipient("")
    setDialogOpen(true)
  }

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      task_type: "scheduled",
      task_action: "alert_check",
      schedule_config: {},
      action_config: {},
      enabled: true,
      dependent_tasks: [],
      notify_on_success: false,
      notify_on_failure: true,
      notify_recipients: [],
    })
    setEditingTask(null)
    setScheduleType("template")
    setSelectedDependentTasks([])
    setNotificationRecipient("")
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return "-"
    return new Date(dateString).toLocaleString("zh-TW")
  }

  const getTaskTypeBadge = (type: string) => {
    const variants: Record<string, "default" | "secondary" | "outline"> = {
      scheduled: "default",
      triggered: "secondary",
      manual: "outline",
    }
    return variants[type] || "default"
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive"> = {
      success: "default",
      failure: "destructive",
      running: "secondary",
    }
    return variants[status] || "default"
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <StepIndicator currentStep={5} steps={workflowSteps} />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">自动化任务</h1>
          <p className="text-muted-foreground mt-2">管理定時任务和觸發式任务</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchTasks} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
          <PermissionGuard permission="automation_task:create">
            <Dialog open={dialogOpen} onOpenChange={(open) => {
              setDialogOpen(open)
              if (!open) resetForm()
            }}>
              <DialogTrigger asChild>
                <Button onClick={resetForm}>
                  <Plus className="h-4 w-4 mr-2" />
                  创建任务
                </Button>
              </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{editingTask ? "编辑任务" : "创建任务"}</DialogTitle>
                <DialogDescription>
                  {editingTask ? "修改自动化任务配置" : "创建新的自动化任务"}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="name">任务名稱 *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="例如：每日告警检查"
                  />
                </div>
                <div>
                  <Label htmlFor="description">描述</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="任务描述"
                    rows={3}
                  />
                </div>
                {!editingTask && (
                  <>
                    <div>
                      <Label htmlFor="task_type">任务類型 *</Label>
                      <Select
                        value={formData.task_type}
                        onValueChange={(value: "scheduled" | "triggered" | "manual") =>
                          setFormData({ ...formData, task_type: value })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="scheduled">定時任务</SelectItem>
                          <SelectItem value="triggered">觸發式任务</SelectItem>
                          <SelectItem value="manual">手动任务</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="task_action">任务動作 *</Label>
                      <Select
                        value={formData.task_action}
                        onValueChange={(value) => setFormData({ ...formData, task_action: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="alert_check">告警检查</SelectItem>
                          <SelectItem value="account_start">启动账号</SelectItem>
                          <SelectItem value="account_stop">停止账号</SelectItem>
                          <SelectItem value="account_batch_start">批量启动账号</SelectItem>
                          <SelectItem value="account_batch_stop">批量停止账号</SelectItem>
                          <SelectItem value="script_publish">发布剧本</SelectItem>
                          <SelectItem value="script_review">剧本審核</SelectItem>
                          <SelectItem value="data_backup">数据備份</SelectItem>
                          <SelectItem value="data_export">数据导出</SelectItem>
                          <SelectItem value="role_assignment">角色分配</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </>
                )}
                
                {/* 調度配置 */}
                {formData.task_type === "scheduled" && (
                  <div className="space-y-4 border-t pt-4">
                    <Label>調度配置</Label>
                    <Tabs value={scheduleType} onValueChange={(v) => setScheduleType(v as "cron" | "interval" | "template")}>
                      <TabsList className="grid w-full grid-cols-3">
                        <TabsTrigger value="template">默认模板</TabsTrigger>
                        <TabsTrigger value="cron">Cron 表達式</TabsTrigger>
                        <TabsTrigger value="interval">間隔調度</TabsTrigger>
                      </TabsList>
                      
                      <TabsContent value="template" className="space-y-4 mt-4">
                        <div className="grid grid-cols-2 gap-2">
                          {[
                            { label: "每5分鐘", value: { interval_seconds: 300 } },
                            { label: "每15分鐘", value: { interval_seconds: 900 } },
                            { label: "每30分鐘", value: { interval_minutes: 30 } },
                            { label: "每小时", value: { interval_hours: 1 } },
                            { label: "每天 9:00", value: { cron: "0 9 * * *" } },
                            { label: "每天 0:00", value: { cron: "0 0 * * *" } },
                            { label: "每週一 9:00", value: { cron: "0 9 * * 1" } },
                            { label: "每月1日 0:00", value: { cron: "0 0 1 * *" } },
                          ].map((template) => (
                            <Button
                              key={template.label}
                              type="button"
                              variant="outline"
                              className="justify-start"
                              onClick={() => {
                                setFormData({ ...formData, schedule_config: template.value })
                              }}
                            >
                              {template.label}
                            </Button>
                          ))}
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="cron" className="space-y-4 mt-4">
                        <div>
                          <Label htmlFor="cron_expr">Cron 表達式</Label>
                          <Input
                            id="cron_expr"
                            placeholder="0 9 * * * (分鐘 小时 日 月 星期)"
                            value={(formData.schedule_config as any)?.cron || ""}
                            onChange={(e) => {
                              setFormData({
                                ...formData,
                                schedule_config: { cron: e.target.value },
                              })
                            }}
                          />
                          <p className="text-xs text-muted-foreground mt-1">
                            格式: 分鐘 小时 日 月 星期 (例如: 0 9 * * * 表示每天9點)
                          </p>
                        </div>
                        <div className="bg-muted p-3 rounded-md text-xs space-y-1">
                          <p><strong>範例:</strong></p>
                          <p>• <code className="bg-background px-1 rounded">0 9 * * *</code> - 每天 9:00</p>
                          <p>• <code className="bg-background px-1 rounded">0 */2 * * *</code> - 每 2 小时</p>
                          <p>• <code className="bg-background px-1 rounded">*/15 * * * *</code> - 每 15 分鐘</p>
                          <p>• <code className="bg-background px-1 rounded">0 0 * * 1</code> - 每週一 0:00</p>
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="interval" className="space-y-4 mt-4">
                        <div className="grid grid-cols-3 gap-4">
                          <div>
                            <Label htmlFor="interval_seconds">秒</Label>
                            <Input
                              id="interval_seconds"
                              type="number"
                              placeholder="秒數"
                              value={(formData.schedule_config as any)?.interval_seconds || ""}
                              onChange={(e) => {
                                const seconds = e.target.value ? parseInt(e.target.value) : undefined
                                setFormData({
                                  ...formData,
                                  schedule_config: seconds ? { interval_seconds: seconds } : {},
                                })
                              }}
                            />
                          </div>
                          <div>
                            <Label htmlFor="interval_minutes">分鐘</Label>
                            <Input
                              id="interval_minutes"
                              type="number"
                              placeholder="分鐘數"
                              value={(formData.schedule_config as any)?.interval_minutes || ""}
                              onChange={(e) => {
                                const minutes = e.target.value ? parseInt(e.target.value) : undefined
                                setFormData({
                                  ...formData,
                                  schedule_config: minutes ? { interval_minutes: minutes } : {},
                                })
                              }}
                            />
                          </div>
                          <div>
                            <Label htmlFor="interval_hours">小时</Label>
                            <Input
                              id="interval_hours"
                              type="number"
                              placeholder="小时數"
                              value={(formData.schedule_config as any)?.interval_hours || ""}
                              onChange={(e) => {
                                const hours = e.target.value ? parseInt(e.target.value) : undefined
                                setFormData({
                                  ...formData,
                                  schedule_config: hours ? { interval_hours: hours } : {},
                                })
                              }}
                            />
                          </div>
                        </div>
                      </TabsContent>
                    </Tabs>
                  </div>
                )}
                
                {/* 任务動作配置 */}
                {formData.task_type === "scheduled" && (
                  <div className="space-y-4 border-t pt-4">
                    <Label>動作配置</Label>
                    {formData.task_action === "account_start" && (
                      <div>
                        <Label htmlFor="account_ids">账号ID列表（可选，留空則启动所有停用的账号）</Label>
                        <Textarea
                          id="account_ids"
                          placeholder="每行一个账号ID，例如：&#10;account1&#10;account2"
                          value={Array.isArray((formData.action_config as any)?.account_ids) 
                            ? (formData.action_config as any).account_ids.join("\n")
                            : ""}
                          onChange={(e) => {
                            const accountIds = e.target.value
                              .split("\n")
                              .map((id) => id.trim())
                              .filter((id) => id.length > 0)
                            setFormData({
                              ...formData,
                              action_config: { account_ids: accountIds },
                            })
                          }}
                          rows={4}
                        />
                      </div>
                    )}
                    {formData.task_action === "account_stop" && (
                      <div>
                        <Label htmlFor="account_ids">账号ID列表（可选，留空則停止所有啟用的账号）</Label>
                        <Textarea
                          id="account_ids"
                          placeholder="每行一个账号ID，例如：&#10;account1&#10;account2"
                          value={Array.isArray((formData.action_config as any)?.account_ids)
                            ? (formData.action_config as any).account_ids.join("\n")
                            : ""}
                          onChange={(e) => {
                            const accountIds = e.target.value
                              .split("\n")
                              .map((id) => id.trim())
                              .filter((id) => id.length > 0)
                            setFormData({
                              ...formData,
                              action_config: { account_ids: accountIds },
                            })
                          }}
                          rows={4}
                        />
                      </div>
                    )}
                    {formData.task_action === "script_publish" && (
                      <div>
                        <Label htmlFor="script_id">剧本ID *</Label>
                        <Input
                          id="script_id"
                          placeholder="script_id"
                          value={(formData.action_config as any)?.script_id || ""}
                          onChange={(e) => {
                            setFormData({
                              ...formData,
                              action_config: { script_id: e.target.value },
                            })
                          }}
                        />
                      </div>
                    )}
                    {formData.task_action === "alert_check" && (
                      <div className="text-sm text-muted-foreground">
                        告警检查任务不需要額外配置，將自动检查所有啟用的告警規則。
                      </div>
                    )}
                    {formData.task_action === "data_backup" && (
                      <div className="text-sm text-muted-foreground">
                        数据備份任务不需要額外配置，將自动備份所有数据库表。
                      </div>
                    )}
                  </div>
                )}
                
                {/* 依賴任务配置 */}
                <div className="space-y-4 border-t pt-4">
                  <Label>依賴任务（完成後自动觸發）</Label>
                  <div className="space-y-2">
                    <Select
                      value=""
                      onValueChange={(value) => {
                        if (value && !selectedDependentTasks.includes(value)) {
                          const newDependentTasks = [...selectedDependentTasks, value]
                          setSelectedDependentTasks(newDependentTasks)
                          setFormData({ ...formData, dependent_tasks: newDependentTasks })
                        }
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择依賴任务" />
                      </SelectTrigger>
                      <SelectContent>
                        {tasks
                          .filter((t) => t.id !== editingTask?.id && !selectedDependentTasks.includes(t.id))
                          .map((task) => (
                            <SelectItem key={task.id} value={task.id}>
                              {task.name}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                    {selectedDependentTasks.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {selectedDependentTasks.map((taskId) => {
                          const task = tasks.find((t) => t.id === taskId)
                          return (
                            <Badge
                              key={taskId}
                              variant="secondary"
                              className="cursor-pointer"
                              onClick={() => {
                                const newDependentTasks = selectedDependentTasks.filter((id) => id !== taskId)
                                setSelectedDependentTasks(newDependentTasks)
                                setFormData({ ...formData, dependent_tasks: newDependentTasks })
                              }}
                            >
                              {task?.name || taskId}
                              <XCircle className="h-3 w-3 ml-1" />
                            </Badge>
                          )
                        })}
                      </div>
                    )}
                  </div>
                </div>

                {/* 通知配置 */}
                <div className="space-y-4 border-t pt-4">
                  <Label>通知配置</Label>
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="notify_on_success"
                        checked={formData.notify_on_success}
                        onCheckedChange={(checked) => setFormData({ ...formData, notify_on_success: checked })}
                      />
                      <Label htmlFor="notify_on_success">成功時通知</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="notify_on_failure"
                        checked={formData.notify_on_failure}
                        onCheckedChange={(checked) => setFormData({ ...formData, notify_on_failure: checked })}
                      />
                      <Label htmlFor="notify_on_failure">失败時通知（默認啟用）</Label>
                    </div>
                    {(formData.notify_on_success || formData.notify_on_failure) && (
                      <div>
                        <Label htmlFor="notification_recipient">通知接收人（郵箱或用户ID）</Label>
                        <div className="flex gap-2 mt-1">
                          <Input
                            id="notification_recipient"
                            placeholder="输入郵箱或用户ID"
                            value={notificationRecipient}
                            onChange={(e) => setNotificationRecipient(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter" && notificationRecipient.trim()) {
                                e.preventDefault()
                                const recipients = [...(formData.notify_recipients || []), notificationRecipient.trim()]
                                setFormData({ ...formData, notify_recipients: recipients })
                                setNotificationRecipient("")
                              }
                            }}
                          />
                          <Button
                            type="button"
                            variant="outline"
                            onClick={() => {
                              if (notificationRecipient.trim()) {
                                const recipients = [...(formData.notify_recipients || []), notificationRecipient.trim()]
                                setFormData({ ...formData, notify_recipients: recipients })
                                setNotificationRecipient("")
                              }
                            }}
                          >
                            添加
                          </Button>
                        </div>
                        {formData.notify_recipients && formData.notify_recipients.length > 0 && (
                          <div className="flex flex-wrap gap-2 mt-2">
                            {formData.notify_recipients.map((recipient, index) => (
                              <Badge
                                key={index}
                                variant="secondary"
                                className="cursor-pointer"
                                onClick={() => {
                                  const recipients = formData.notify_recipients?.filter((_, i) => i !== index) || []
                                  setFormData({ ...formData, notify_recipients: recipients })
                                }}
                              >
                                {recipient}
                                <XCircle className="h-3 w-3 ml-1" />
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="enabled"
                    checked={formData.enabled}
                    onCheckedChange={(checked) => setFormData({ ...formData, enabled: checked })}
                  />
                  <Label htmlFor="enabled">啟用任务</Label>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setDialogOpen(false)}>
                    取消
                  </Button>
                  <PermissionGuard permission={editingTask ? "automation_task:update" : "automation_task:create"}>
                    <Button onClick={editingTask ? handleUpdate : handleCreate}>
                      {editingTask ? "更新" : "创建"}
                    </Button>
                  </PermissionGuard>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </PermissionGuard>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>任务列表</CardTitle>
          <CardDescription>所有自动化任务</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : tasks.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              暫无任务，点击「创建任务」开始
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>任务名稱</TableHead>
                  <TableHead>類型</TableHead>
                  <TableHead>動作</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>执行次数</TableHead>
                  <TableHead>最后执行</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tasks.map((task) => (
                  <TableRow key={task.id}>
                    <TableCell className="font-medium">{task.name}</TableCell>
                    <TableCell>
                      <Badge variant={getTaskTypeBadge(task.task_type)}>
                        {task.task_type === "scheduled" ? "定時" : task.task_type === "triggered" ? "觸發" : "手动"}
                      </Badge>
                    </TableCell>
                    <TableCell>{task.task_action}</TableCell>
                    <TableCell>
                      <Badge variant={task.enabled ? "default" : "secondary"}>
                        {task.enabled ? "啟用" : "停用"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="text-sm">總: {task.run_count}</span>
                        <span className="text-sm text-green-600">✓ {task.success_count}</span>
                        <span className="text-sm text-red-600">✗ {task.failure_count}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      <div className="space-y-1">
                        <div>最后执行: {formatDate(task.last_run_at)}</div>
                        {task.next_run_at && (
                          <div className="text-xs text-green-600 flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            下次执行: {formatDate(task.next_run_at)}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <PermissionGuard permission="automation_task:run">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleRun(task.id)}
                            disabled={runningTaskId === task.id}
                          >
                            {runningTaskId === task.id ? (
                              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                            ) : (
                              <Play className="h-4 w-4 mr-1" />
                            )}
                            执行
                          </Button>
                        </PermissionGuard>
                        <PermissionGuard permission="automation_task:log:view">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleViewLogs(task.id)}
                          >
                            <Clock className="h-4 w-4 mr-1" />
                            日志
                          </Button>
                        </PermissionGuard>
                        <PermissionGuard permission="automation_task:update">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openEditDialog(task)}
                          >
                            <Edit className="h-4 w-4 mr-1" />
                            编辑
                          </Button>
                        </PermissionGuard>
                        <PermissionGuard permission="automation_task:delete">
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => {
                              setDeletingTaskId(task.id)
                              setDeleteDialogOpen(true)
                            }}
                          >
                            <Trash2 className="h-4 w-4 mr-1" />
                            删除
                          </Button>
                        </PermissionGuard>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* 删除确认对话框 */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除此自动化任务嗎？此操作无法撤銷。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <PermissionGuard permission="automation_task:delete">
              <AlertDialogAction onClick={handleDelete}>删除</AlertDialogAction>
            </PermissionGuard>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 任务日志对话框 */}
      <Dialog open={logsDialogOpen} onOpenChange={setLogsDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>任务执行日志</DialogTitle>
            <DialogDescription>
              任务 ID: {selectedTaskId}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            {taskLogs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                暫无执行日志
              </div>
            ) : (
              taskLogs.map((log) => (
                <Card key={log.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Badge variant={getStatusBadge(log.status)}>
                            {log.status === "success" ? "成功" : log.status === "failure" ? "失败" : "运行中"}
                          </Badge>
                          <span className="text-sm text-muted-foreground">
                            {formatDate(log.started_at)}
                          </span>
                          {log.duration_seconds && (
                            <span className="text-sm text-muted-foreground">
                              耗時: {log.duration_seconds.toFixed(2)}s
                            </span>
                          )}
                        </div>
                        {log.result && (
                          <p className="text-sm mt-2">{log.result}</p>
                        )}
                        {log.error_message && (
                          <p className="text-sm mt-2 text-red-600">{log.error_message}</p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

