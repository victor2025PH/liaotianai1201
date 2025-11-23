/**
 * 通知配置管理頁面
 */
"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { useToast } from "@/hooks/use-toast"
import { PermissionGuard } from "@/components/permissions/permission-guard"
import { Settings, Plus, Edit, Trash2, Loader2, Eye } from "lucide-react"
import {
  listNotificationConfigs,
  createNotificationConfig,
  updateNotificationConfig,
  deleteNotificationConfig,
  type NotificationConfig,
  type NotificationConfigCreate,
  type NotificationType,
  listNotificationTemplates,
  createNotificationTemplate,
  updateNotificationTemplate,
  deleteNotificationTemplate,
  previewNotificationTemplate,
  type NotificationTemplate,
  type NotificationTemplateCreate,
  type NotificationTemplatePreviewResponse,
} from "@/lib/api/notifications"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function NotificationConfigsPage() {
  const [activeTab, setActiveTab] = useState<"configs" | "templates">("configs")
  const [configs, setConfigs] = useState<NotificationConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [editingConfig, setEditingConfig] = useState<NotificationConfig | null>(null)
  const [processing, setProcessing] = useState(false)
  const { toast } = useToast()

  const createInitialTemplateForm = (): NotificationTemplateCreate => ({
    name: "",
    description: "",
    notification_type: "email",
    title_template: "[{alert_level}] {alert_title}",
    body_template: "{alert_message}",
    variables: ["alert_title", "alert_message", "resource_type", "resource_id"],
    conditions: {
      alert_levels: [],
      event_types: [],
      resource_types: [],
    },
    default_metadata: {},
    enabled: true,
  })
  const [templates, setTemplates] = useState<NotificationTemplate[]>([])
  const [templateLoading, setTemplateLoading] = useState(true)
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false)
  const [templateProcessing, setTemplateProcessing] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<NotificationTemplate | null>(null)
  const [templateForm, setTemplateForm] = useState<NotificationTemplateCreate>(() => createInitialTemplateForm())
  const [previewResult, setPreviewResult] = useState<{ title: string; message: string } | null>(null)
  const [previewing, setPreviewing] = useState(false)

  const [formData, setFormData] = useState<NotificationConfigCreate>({
    name: "",
    description: "",
    notification_type: "email",
    alert_levels: [],
    event_types: [],
    config_data: {},
    recipients: [],
    enabled: true,
  })

  const loadConfigs = async () => {
    try {
      setLoading(true)
      const data = await listNotificationConfigs()
      setConfigs(data)
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "加載通知配置失敗",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const loadTemplates = async () => {
    try {
      setTemplateLoading(true)
      const response = await listNotificationTemplates({ skip: 0, limit: 200 })
      setTemplates(response.items)
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "加載通知模板失敗",
        variant: "destructive",
      })
    } finally {
      setTemplateLoading(false)
    }
  }

  useEffect(() => {
    loadConfigs()
    loadTemplates()
  }, [])

  const handleOpenCreateDialog = () => {
    setFormData({
      name: "",
      description: "",
      notification_type: "email",
      alert_levels: [],
      event_types: [],
      config_data: {},
      recipients: [],
      enabled: true,
    })
    setIsCreateDialogOpen(true)
  }

  const handleOpenEditDialog = (config: NotificationConfig) => {
    setEditingConfig(config)
    setFormData({
      name: config.name,
      description: config.description || "",
      notification_type: config.notification_type,
      alert_levels: config.alert_levels || [],
      event_types: config.event_types || [],
      config_data: config.config_data,
      recipients: config.recipients,
      enabled: config.enabled,
    })
    setIsEditDialogOpen(true)
  }

  const handleOpenTemplateDialog = (template?: NotificationTemplate) => {
    if (template) {
      setEditingTemplate(template)
      setTemplateForm({
        name: template.name,
        description: template.description,
        notification_type: template.notification_type,
        title_template: template.title_template,
        body_template: template.body_template,
        variables: template.variables || [],
        conditions: {
          alert_levels: template.conditions?.alert_levels || [],
          event_types: template.conditions?.event_types || [],
          resource_types: template.conditions?.resource_types || [],
        },
        default_metadata: template.default_metadata || {},
        enabled: template.enabled,
      })
    } else {
      setEditingTemplate(null)
      setTemplateForm(createInitialTemplateForm())
    }
    setPreviewResult(null)
    setTemplateDialogOpen(true)
  }

  const handleSaveTemplate = async () => {
    if (!templateForm.name || !templateForm.title_template || !templateForm.body_template) {
      toast({
        title: "錯誤",
        description: "請填寫模板名稱、標題與內容",
        variant: "destructive",
      })
      return
    }

    try {
      setTemplateProcessing(true)
      if (editingTemplate) {
        await updateNotificationTemplate(editingTemplate.id, templateForm)
        toast({ title: "成功", description: "模板已更新" })
      } else {
        await createNotificationTemplate(templateForm)
        toast({ title: "成功", description: "模板已創建" })
      }
      setTemplateDialogOpen(false)
      setEditingTemplate(null)
      loadTemplates()
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "保存模板失敗",
        variant: "destructive",
      })
    } finally {
      setTemplateProcessing(false)
    }
  }

  const handleDeleteTemplate = async (templateId: number) => {
    if (!confirm("確定要刪除此通知模板嗎？")) return
    try {
      await deleteNotificationTemplate(templateId)
      toast({ title: "成功", description: "模板已刪除" })
      loadTemplates()
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "刪除模板失敗",
        variant: "destructive",
      })
    }
  }

  const handlePreviewTemplate = async () => {
    if (!templateForm.title_template || !templateForm.body_template) {
      toast({
        title: "錯誤",
        description: "請先填寫模板內容",
        variant: "destructive",
      })
      return
    }
    try {
      setPreviewing(true)
      const sampleContext = {
        alert_title: "樣本告警",
        alert_message: "這是一條測試告警內容，用於預覽模板效果。",
        alert_level: templateForm.conditions?.alert_levels?.[0] || "medium",
        resource_type: templateForm.conditions?.resource_types?.[0] || "account",
        resource_id: "ACCT-001",
        event_type: templateForm.conditions?.event_types?.[0] || "alert",
      }
      const preview = await previewNotificationTemplate({
        title_template: templateForm.title_template,
        body_template: templateForm.body_template,
        context: sampleContext,
      })
      setPreviewResult(preview)
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "預覽模板失敗",
        variant: "destructive",
      })
    } finally {
      setPreviewing(false)
    }
  }

  const toggleTemplateCondition = (
    field: "alert_levels" | "event_types",
    value: string,
    checked: boolean
  ) => {
    setTemplateForm((prev) => {
      const nextConditions = {
        alert_levels: prev.conditions?.alert_levels ? [...prev.conditions.alert_levels] : [],
        event_types: prev.conditions?.event_types ? [...prev.conditions.event_types] : [],
        resource_types: prev.conditions?.resource_types ? [...prev.conditions.resource_types] : [],
      }
      const list = nextConditions[field] || []
      if (checked) {
        if (!list.includes(value)) list.push(value)
      } else {
        const index = list.indexOf(value)
        if (index >= 0) list.splice(index, 1)
      }
      nextConditions[field] = list
      return {
        ...prev,
        conditions: nextConditions,
      }
    })
  }

  const handleResourceTypesChange = (value: string) => {
    const resourceTypes = value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
    setTemplateForm((prev) => ({
      ...prev,
      conditions: {
        alert_levels: prev.conditions?.alert_levels || [],
        event_types: prev.conditions?.event_types || [],
        resource_types: resourceTypes,
      },
    }))
  }

  const handleCreate = async () => {
    if (!formData.name || !formData.recipients.length) {
      toast({
        title: "錯誤",
        description: "請填寫配置名稱和接收人",
        variant: "destructive",
      })
      return
    }

    try {
      setProcessing(true)
      await createNotificationConfig(formData)
      toast({
        title: "成功",
        description: "通知配置已創建",
      })
      setIsCreateDialogOpen(false)
      loadConfigs()
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "創建通知配置失敗",
        variant: "destructive",
      })
    } finally {
      setProcessing(false)
    }
  }

  const handleUpdate = async () => {
    if (!editingConfig) return

    try {
      setProcessing(true)
      await updateNotificationConfig(editingConfig.id, formData)
      toast({
        title: "成功",
        description: "通知配置已更新",
      })
      setIsEditDialogOpen(false)
      setEditingConfig(null)
      loadConfigs()
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "更新通知配置失敗",
        variant: "destructive",
      })
    } finally {
      setProcessing(false)
    }
  }

  const handleDelete = async (configId: number) => {
    if (!confirm("確定要刪除此通知配置嗎？")) return

    try {
      await deleteNotificationConfig(configId)
      toast({
        title: "成功",
        description: "通知配置已刪除",
      })
      loadConfigs()
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "刪除通知配置失敗",
        variant: "destructive",
      })
    }
  }

  const getNotificationTypeLabel = (type: NotificationType) => {
    const labels: Record<NotificationType, string> = {
      email: "郵件",
      browser: "瀏覽器",
      webhook: "Webhook",
    }
    return labels[type]
  }

  const renderConditionBadges = (items?: string[]) => {
    if (!items || items.length === 0) {
      return <span className="text-muted-foreground text-sm">全部</span>
    }
    return (
      <div className="flex flex-wrap gap-1">
        {items.map((item) => (
          <Badge key={item} variant="outline" className="text-xs">
            {item}
          </Badge>
        ))}
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Settings className="h-8 w-8" />
            通知配置
          </h1>
          <p className="text-muted-foreground mt-2">
            管理通知配置和規則
          </p>
        </div>
        <PermissionGuard permission="alert_rule:create">
          {activeTab === "configs" ? (
            <Button onClick={handleOpenCreateDialog}>
              <Plus className="h-4 w-4 mr-2" />
              創建配置
            </Button>
          ) : (
            <Button onClick={() => handleOpenTemplateDialog()}>
              <Plus className="h-4 w-4 mr-2" />
              創建模板
            </Button>
          )}
        </PermissionGuard>
      </div>
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as "configs" | "templates")}>
        <TabsList className="mb-4">
          <TabsTrigger value="configs">通知配置</TabsTrigger>
          <TabsTrigger value="templates">通知模板</TabsTrigger>
        </TabsList>

        <TabsContent value="configs">
          <PermissionGuard permission="alert_rule:view">
            {loading ? (
              <div className="text-center py-8">加載中...</div>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle>通知配置列表</CardTitle>
                  <CardDescription>共 {configs.length} 個配置</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="border rounded-lg">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>名稱</TableHead>
                          <TableHead>類型</TableHead>
                          <TableHead>告警級別</TableHead>
                          <TableHead>事件類型</TableHead>
                          <TableHead>接收人</TableHead>
                          <TableHead>狀態</TableHead>
                          <TableHead className="text-right">操作</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {configs.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={7} className="text-center py-8">
                              沒有通知配置
                            </TableCell>
                          </TableRow>
                        ) : (
                          configs.map((config) => (
                            <TableRow key={config.id}>
                              <TableCell>
                                <div>
                                  <div className="font-medium">{config.name}</div>
                                  {config.description && (
                                    <div className="text-sm text-muted-foreground">
                                      {config.description}
                                    </div>
                                  )}
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge>{getNotificationTypeLabel(config.notification_type)}</Badge>
                              </TableCell>
                              <TableCell>
                                {config.alert_levels && config.alert_levels.length > 0 ? (
                                  <div className="flex flex-wrap gap-1">
                                    {config.alert_levels.map((level) => (
                                      <Badge key={level} variant="outline" className="text-xs">
                                        {level}
                                      </Badge>
                                    ))}
                                  </div>
                                ) : (
                                  <span className="text-muted-foreground text-sm">全部</span>
                                )}
                              </TableCell>
                              <TableCell>
                                {config.event_types && config.event_types.length > 0 ? (
                                  <div className="flex flex-wrap gap-1">
                                    {config.event_types.map((type) => (
                                      <Badge key={type} variant="outline" className="text-xs">
                                        {type}
                                      </Badge>
                                    ))}
                                  </div>
                                ) : (
                                  <span className="text-muted-foreground text-sm">全部</span>
                                )}
                              </TableCell>
                              <TableCell>
                                <div className="text-sm">
                                  {config.recipients.length} 個接收人
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge variant={config.enabled ? "default" : "secondary"}>
                                  {config.enabled ? "啟用" : "停用"}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-right">
                                <div className="flex items-center justify-end gap-2">
                                  <PermissionGuard permission="alert_rule:update">
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => handleOpenEditDialog(config)}
                                    >
                                      <Edit className="h-4 w-4" />
                                    </Button>
                                  </PermissionGuard>
                                  <PermissionGuard permission="alert_rule:delete">
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => handleDelete(config.id)}
                                    >
                                      <Trash2 className="h-4 w-4 text-destructive" />
                                    </Button>
                                  </PermissionGuard>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            )}
          </PermissionGuard>
        </TabsContent>

        <TabsContent value="templates">
          <PermissionGuard permission="alert_rule:view">
            {templateLoading ? (
              <div className="text-center py-8">加載中...</div>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle>通知模板列表</CardTitle>
                  <CardDescription>共 {templates.length} 個模板</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="border rounded-lg">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>名稱</TableHead>
                          <TableHead>類型</TableHead>
                          <TableHead>告警級別</TableHead>
                          <TableHead>事件類型</TableHead>
                          <TableHead>資源類型</TableHead>
                          <TableHead>狀態</TableHead>
                          <TableHead className="text-right">操作</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {templates.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={7} className="text-center py-8">
                              尚未創建模板
                            </TableCell>
                          </TableRow>
                        ) : (
                          templates.map((template) => (
                            <TableRow key={template.id}>
                              <TableCell>
                                <div>
                                  <div className="font-medium">{template.name}</div>
                                  {template.description && (
                                    <div className="text-sm text-muted-foreground">
                                      {template.description}
                                    </div>
                                  )}
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge>{getNotificationTypeLabel(template.notification_type)}</Badge>
                              </TableCell>
                              <TableCell>{renderConditionBadges(template.conditions?.alert_levels)}</TableCell>
                              <TableCell>{renderConditionBadges(template.conditions?.event_types)}</TableCell>
                              <TableCell>{renderConditionBadges(template.conditions?.resource_types)}</TableCell>
                              <TableCell>
                                <Badge variant={template.enabled ? "default" : "secondary"}>
                                  {template.enabled ? "啟用" : "停用"}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-right">
                                <div className="flex items-center justify-end gap-2">
                                  <PermissionGuard permission="alert_rule:update">
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => handleOpenTemplateDialog(template)}
                                    >
                                      <Edit className="h-4 w-4" />
                                    </Button>
                                  </PermissionGuard>
                                  <PermissionGuard permission="alert_rule:delete">
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => handleDeleteTemplate(template.id)}
                                    >
                                      <Trash2 className="h-4 w-4 text-destructive" />
                                    </Button>
                                  </PermissionGuard>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            )}
          </PermissionGuard>
        </TabsContent>
      </Tabs>

      {/* 創建/編輯對話框 */}
      <Dialog
        open={isCreateDialogOpen || isEditDialogOpen}
        onOpenChange={(open) => {
          if (!open) {
            setIsCreateDialogOpen(false)
            setIsEditDialogOpen(false)
            setEditingConfig(null)
          }
        }}
      >
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {isEditDialogOpen ? "編輯通知配置" : "創建通知配置"}
            </DialogTitle>
            <DialogDescription>
              {isEditDialogOpen
                ? "更新通知配置信息"
                : "填寫通知配置信息"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">配置名稱 *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="例如：高級別告警郵件通知"
              />
            </div>
            <div>
              <Label htmlFor="description">描述</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="配置描述（可選）"
              />
            </div>
            <div>
              <Label htmlFor="notification_type">通知類型 *</Label>
              <Select
                value={formData.notification_type}
                onValueChange={(value) =>
                  setFormData({ ...formData, notification_type: value as NotificationType })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="email">郵件</SelectItem>
                  <SelectItem value="browser">瀏覽器</SelectItem>
                  <SelectItem value="webhook">Webhook</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {formData.notification_type === "email" && (
              <div className="space-y-2">
                <Label>郵件配置</Label>
                <Input
                  placeholder="SMTP 主機"
                  value={formData.config_data.smtp_host || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      config_data: { ...formData.config_data, smtp_host: e.target.value },
                    })
                  }
                />
                <Input
                  placeholder="SMTP 端口"
                  type="number"
                  value={formData.config_data.smtp_port || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      config_data: { ...formData.config_data, smtp_port: parseInt(e.target.value) },
                    })
                  }
                />
                <Input
                  placeholder="SMTP 用戶名"
                  value={formData.config_data.smtp_user || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      config_data: { ...formData.config_data, smtp_user: e.target.value },
                    })
                  }
                />
                <Input
                  placeholder="SMTP 密碼"
                  type="password"
                  value={formData.config_data.smtp_password || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      config_data: { ...formData.config_data, smtp_password: e.target.value },
                    })
                  }
                />
                <Input
                  placeholder="發件人郵箱"
                  value={formData.config_data.email_from || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      config_data: { ...formData.config_data, email_from: e.target.value },
                    })
                  }
                />
              </div>
            )}
            {formData.notification_type === "webhook" && (
              <div>
                <Label htmlFor="webhook_url">Webhook URL *</Label>
                <Input
                  id="webhook_url"
                  value={formData.config_data.webhook_url || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      config_data: { ...formData.config_data, webhook_url: e.target.value },
                    })
                  }
                  placeholder="https://example.com/webhook"
                />
              </div>
            )}
            <div>
              <Label>告警級別</Label>
              <div className="flex gap-4 mt-2">
                {["high", "medium", "low"].map((level) => (
                  <div key={level} className="flex items-center gap-2">
                    <Checkbox
                      checked={formData.alert_levels?.includes(level)}
                      onCheckedChange={(checked) => {
                        const levels = formData.alert_levels || []
                        if (checked) {
                          setFormData({
                            ...formData,
                            alert_levels: [...levels, level],
                          })
                        } else {
                          setFormData({
                            ...formData,
                            alert_levels: levels.filter((l) => l !== level),
                          })
                        }
                      }}
                    />
                    <Label className="text-sm">{level === "high" ? "高" : level === "medium" ? "中" : "低"}</Label>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <Label>事件類型</Label>
              <div className="flex gap-4 mt-2">
                {["alert", "error", "info"].map((type) => (
                  <div key={type} className="flex items-center gap-2">
                    <Checkbox
                      checked={formData.event_types?.includes(type)}
                      onCheckedChange={(checked) => {
                        const types = formData.event_types || []
                        if (checked) {
                          setFormData({
                            ...formData,
                            event_types: [...types, type],
                          })
                        } else {
                          setFormData({
                            ...formData,
                            event_types: types.filter((t) => t !== type),
                          })
                        }
                      }}
                    />
                    <Label className="text-sm">
                      {type === "alert" ? "告警" : type === "error" ? "錯誤" : "信息"}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <Label htmlFor="recipients">接收人 *（每行一個郵箱或用戶ID）</Label>
              <Textarea
                id="recipients"
                value={formData.recipients.join("\n")}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    recipients: e.target.value
                      .split("\n")
                      .map((r) => r.trim())
                      .filter((r) => r),
                  })
                }
                placeholder="user@example.com&#10;user2@example.com"
                rows={4}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="enabled">啟用狀態</Label>
              <Switch
                id="enabled"
                checked={formData.enabled}
                onCheckedChange={(checked) => setFormData({ ...formData, enabled: checked })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsCreateDialogOpen(false)
                setIsEditDialogOpen(false)
                setEditingConfig(null)
              }}
              disabled={processing}
            >
              取消
            </Button>
            <Button onClick={isEditDialogOpen ? handleUpdate : handleCreate} disabled={processing}>
              {processing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {isEditDialogOpen ? "更新中..." : "創建中..."}
                </>
              ) : (
                <>{isEditDialogOpen ? "更新" : "創建"}</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={templateDialogOpen}
        onOpenChange={(open) => {
          if (!open) {
            setTemplateDialogOpen(false)
            setEditingTemplate(null)
            setTemplateForm(createInitialTemplateForm())
            setPreviewResult(null)
          }
        }}
      >
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingTemplate ? "編輯通知模板" : "創建通知模板"}</DialogTitle>
            <DialogDescription>定義通知的標題與內容模板，並設定匹配條件</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="template-name">模板名稱 *</Label>
              <Input
                id="template-name"
                value={templateForm.name}
                onChange={(e) => setTemplateForm({ ...templateForm, name: e.target.value })}
                placeholder="例如：高級別郵件模板"
              />
            </div>
            <div>
              <Label htmlFor="template-description">描述</Label>
              <Textarea
                id="template-description"
                value={templateForm.description || ""}
                onChange={(e) => setTemplateForm({ ...templateForm, description: e.target.value })}
                placeholder="模板描述（可選）"
              />
            </div>
            <div>
              <Label>通知類型 *</Label>
              <Select
                value={templateForm.notification_type}
                onValueChange={(value) =>
                  setTemplateForm({ ...templateForm, notification_type: value as NotificationType })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="email">郵件</SelectItem>
                  <SelectItem value="browser">瀏覽器</SelectItem>
                  <SelectItem value="webhook">Webhook</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="title-template">標題模板 *</Label>
              <Input
                id="title-template"
                value={templateForm.title_template}
                onChange={(e) => setTemplateForm({ ...templateForm, title_template: e.target.value })}
                placeholder="[ {alert_level} ] {alert_title}"
              />
            </div>
            <div>
              <Label htmlFor="body-template">內容模板 *</Label>
              <Textarea
                id="body-template"
                value={templateForm.body_template}
                onChange={(e) => setTemplateForm({ ...templateForm, body_template: e.target.value })}
                rows={4}
                placeholder="{alert_message}"
              />
            </div>
            <div>
              <Label htmlFor="template-variables">可用變數（逗號分隔）</Label>
              <Input
                id="template-variables"
                value={(templateForm.variables || []).join(", ")}
                onChange={(e) =>
                  setTemplateForm({
                    ...templateForm,
                    variables: e.target.value
                      .split(",")
                      .map((item) => item.trim())
                      .filter(Boolean),
                  })
                }
                placeholder="alert_title, alert_message, resource_type"
              />
              <p className="text-xs text-muted-foreground mt-1">
                內建變數：alert_title、alert_message、alert_level、resource_type、resource_id、event_type
              </p>
            </div>
            <div>
              <Label>告警級別條件</Label>
              <div className="flex gap-4 mt-2">
                {["high", "medium", "low"].map((level) => (
                  <div key={level} className="flex items-center gap-2">
                    <Checkbox
                      checked={templateForm.conditions?.alert_levels?.includes(level)}
                      onCheckedChange={(checked) => toggleTemplateCondition("alert_levels", level, Boolean(checked))}
                    />
                    <Label className="text-sm">
                      {level === "high" ? "高" : level === "medium" ? "中" : "低"}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <Label>事件類型條件</Label>
              <div className="flex gap-4 mt-2">
                {["alert", "error", "info"].map((type) => (
                  <div key={type} className="flex items-center gap-2">
                    <Checkbox
                      checked={templateForm.conditions?.event_types?.includes(type)}
                      onCheckedChange={(checked) => toggleTemplateCondition("event_types", type, Boolean(checked))}
                    />
                    <Label className="text-sm">
                      {type === "alert" ? "告警" : type === "error" ? "錯誤" : "信息"}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <Label htmlFor="resource-types">資源類型條件（逗號分隔）</Label>
              <Input
                id="resource-types"
                value={(templateForm.conditions?.resource_types || []).join(", ")}
                onChange={(e) => handleResourceTypesChange(e.target.value)}
                placeholder="account, script, system"
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="template-enabled">啟用狀態</Label>
              <Switch
                id="template-enabled"
                checked={templateForm.enabled}
                onCheckedChange={(checked) => setTemplateForm({ ...templateForm, enabled: checked })}
              />
            </div>
            {previewResult && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">預覽結果</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm font-medium">標題：{previewResult.title}</p>
                  <p className="text-sm text-muted-foreground mt-2 whitespace-pre-line">
                    {previewResult.message}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
          <DialogFooter className="flex flex-col gap-2 sm:flex-row sm:justify-end">
            <div className="flex gap-2">
              <Button
                variant="secondary"
                onClick={handlePreviewTemplate}
                disabled={previewing || templateProcessing}
              >
                {previewing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    預覽中...
                  </>
                ) : (
                  <>
                    <Eye className="h-4 w-4 mr-2" />
                    預覽模板
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setTemplateDialogOpen(false)
                  setEditingTemplate(null)
                }}
                disabled={templateProcessing}
              >
                取消
              </Button>
              <Button onClick={handleSaveTemplate} disabled={templateProcessing}>
                {templateProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    保存中...
                  </>
                ) : (
                  <>保存模板</>
                )}
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

