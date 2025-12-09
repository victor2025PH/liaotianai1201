"use client"

import { useState, useEffect, Suspense } from "react"
import dynamic from "next/dynamic"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useToast } from "@/hooks/use-toast"

// 懒加载重型组件
const Table = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.Table })), { ssr: false })
const TableBody = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableBody })), { ssr: false })
const TableCell = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableCell })), { ssr: false })
const TableHead = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableHead })), { ssr: false })
const TableHeader = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableHeader })), { ssr: false })
const TableRow = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableRow })), { ssr: false })
const Dialog = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.Dialog })), { ssr: false })
const DialogContent = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogContent })), { ssr: false })
const DialogDescription = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogDescription })), { ssr: false })
const DialogFooter = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogFooter })), { ssr: false })
const DialogHeader = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogHeader })), { ssr: false })
const DialogTitle = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogTitle })), { ssr: false })
const Textarea = dynamic(() => import("@/components/ui/textarea").then(mod => ({ default: mod.Textarea })), { ssr: false })
const Select = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.Select })), { ssr: false })
const SelectContent = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectContent })), { ssr: false })
const SelectItem = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectItem })), { ssr: false })
const SelectTrigger = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectTrigger })), { ssr: false })
const SelectValue = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectValue })), { ssr: false })
const DropdownMenu = dynamic(() => import("@/components/ui/dropdown-menu").then(mod => ({ default: mod.DropdownMenu })), { ssr: false })
const DropdownMenuContent = dynamic(() => import("@/components/ui/dropdown-menu").then(mod => ({ default: mod.DropdownMenuContent })), { ssr: false })
const DropdownMenuItem = dynamic(() => import("@/components/ui/dropdown-menu").then(mod => ({ default: mod.DropdownMenuItem })), { ssr: false })
const DropdownMenuLabel = dynamic(() => import("@/components/ui/dropdown-menu").then(mod => ({ default: mod.DropdownMenuLabel })), { ssr: false })
const DropdownMenuSeparator = dynamic(() => import("@/components/ui/dropdown-menu").then(mod => ({ default: mod.DropdownMenuSeparator })), { ssr: false })
const DropdownMenuTrigger = dynamic(() => import("@/components/ui/dropdown-menu").then(mod => ({ default: mod.DropdownMenuTrigger })), { ssr: false })
import {
  Plus,
  Edit,
  Trash2,
  Play,
  History,
  Eye,
  Loader2,
  Download,
  Search,
  X,
} from "lucide-react"
import { PermissionGuard } from "@/components/permissions/permission-guard"
import { PermissionButton } from "@/components/permissions/permission-button"
import {
  getRoleAssignmentSchemes,
  getRoleAssignmentScheme,
  createRoleAssignmentScheme,
  updateRoleAssignmentScheme,
  deleteRoleAssignmentScheme,
  applyRoleAssignmentScheme,
  getRoleAssignmentSchemeHistory,
  getScripts,
  getAccounts,
  extractRoles,
  exportSchemes,
  exportSchemeDetails,
  downloadBlob,
  type RoleAssignmentScheme,
  type SchemeCreateRequest,
  type SchemeUpdateRequest,
  type ApplySchemeRequest,
  type AssignmentHistory,
} from "@/lib/api/group-ai"
import type { Script } from "@/lib/api/group-ai"
import type { Account } from "@/lib/api/group-ai"
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
    status: "current",
  },
  {
    number: 5,
    title: "自动化任务",
    description: "配置自动化执行任务（可选）",
    href: "/group-ai/automation-tasks",
    status: "optional",
  },
];

export default function RoleAssignmentSchemesPage() {
  const { toast } = useToast()
  const [schemes, setSchemes] = useState<RoleAssignmentScheme[]>([])
  const [loading, setLoading] = useState(true)
  const [scripts, setScripts] = useState<Script[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [selectedScriptId, setSelectedScriptId] = useState<string>("")
  const [roles, setRoles] = useState<any[]>([])
  const [assignmentResult, setAssignmentResult] = useState<any>(null)
  const [searchFilters, setSearchFilters] = useState<{
    search?: string
    script_id?: string
    mode?: string
    sort_by?: string
    sort_order?: "asc" | "desc"
  }>({})
  
  // 对话框状态
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [applyDialogOpen, setApplyDialogOpen] = useState(false)
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false)
  const [viewDialogOpen, setViewDialogOpen] = useState(false)
  
  // 当前操作的方案
  const [currentScheme, setCurrentScheme] = useState<RoleAssignmentScheme | null>(null)
  const [historyRecords, setHistoryRecords] = useState<AssignmentHistory[]>([])
  
  // 表單状态
  const [formData, setFormData] = useState<SchemeCreateRequest>({
    name: "",
    description: "",
    script_id: "",
    assignments: [],
    mode: "auto",
    account_ids: [],
  })
  const [creating, setCreating] = useState(false)
  const [applying, setApplying] = useState(false)

  // 加载数据
  useEffect(() => {
    loadSchemes()
    loadScripts()
    loadAccounts()
  }, [])

  const loadSchemes = async (filters?: typeof searchFilters) => {
    try {
      setLoading(true)
      const filters = searchFilters || {}
      const data = await getRoleAssignmentSchemes(
        filters.script_id,
        1,
        100  // 后端限制最大100
      )
      setSchemes(data.items || [])
    } catch (error: any) {
      toast({
        title: "加载失败",
        description: error.message || "无法加载分配方案列表",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const loadScripts = async () => {
    try {
      const data = await getScripts()
      setScripts(data)
    } catch (error: any) {
      console.error("加载剧本失败:", error)
    }
  }

  const loadAccounts = async () => {
    try {
      const data = await getAccounts()
      setAccounts(Array.isArray(data) ? data : [])
    } catch (error: any) {
      console.error("加载账号失败:", error)
    }
  }

  const handleScriptChange = async (scriptId: string) => {
    setSelectedScriptId(scriptId)
    setFormData({ ...formData, script_id: scriptId })
    
    if (scriptId) {
      try {
        // 提取角色
        const rolesData = await extractRoles(scriptId)
        setRoles(rolesData.roles || [])
      } catch (error: any) {
        toast({
          title: "提取角色失败",
          description: error.message || "无法從剧本中提取角色",
          variant: "destructive",
        })
      }
    }
  }

  const handleCreateAssignment = async () => {
    if (!formData.script_id || formData.account_ids.length === 0) {
      toast({
        title: "参数不完整",
        description: "請选择剧本和账号",
        variant: "destructive",
      })
      return
    }

    try {
      // 首先创建方案，然後應用
      const scheme = await createRoleAssignmentScheme({
        name: formData.name || `方案_${Date.now()}`,
        description: formData.description,
        script_id: formData.script_id,
        assignments: formData.assignments || [],
        mode: formData.mode,
        account_ids: formData.account_ids,
      })
      
      // 應用方案
      const result = await applyRoleAssignmentScheme(scheme.id, {
        account_ids: formData.account_ids,
      })
      setAssignmentResult(result)
      toast({
        title: "分配方案创建成功",
        description: `已應用方案，影響 ${result.applied_count || 0} 个账号`,
      })
    } catch (error: any) {
      toast({
        title: "创建分配方案失败",
        description: error.message || "无法创建分配方案",
        variant: "destructive",
      })
    }
  }

  const handleCreateScheme = async () => {
    if (!formData.name || !formData.script_id || formData.assignments.length === 0) {
      toast({
        title: "参数不完整",
        description: "請填寫方案名稱、选择剧本並创建分配方案",
        variant: "destructive",
      })
      return
    }

    try {
      setCreating(true)
      await createRoleAssignmentScheme(formData)
      toast({
        title: "创建成功",
        description: "分配方案已创建",
      })
      setCreateDialogOpen(false)
      setFormData({
        name: "",
        description: "",
        script_id: "",
        assignments: [],
        mode: "auto",
        account_ids: [],
      })
      loadSchemes()
    } catch (error: any) {
      toast({
        title: "创建失败",
        description: error.message || "无法创建分配方案",
        variant: "destructive",
      })
    } finally {
      setCreating(false)
    }
  }

  const handleEdit = async (scheme: RoleAssignmentScheme) => {
    setCurrentScheme(scheme)
    setFormData({
      name: scheme.name,
      description: scheme.description || "",
      script_id: scheme.script_id,
      assignments: scheme.assignments,
      mode: scheme.mode,
      account_ids: scheme.account_ids,
    })
    setSelectedScriptId(scheme.script_id)
    await handleScriptChange(scheme.script_id)
    setEditDialogOpen(true)
  }

  const handleUpdateScheme = async () => {
    if (!currentScheme) return

    try {
      setCreating(true)
      const updateData: SchemeUpdateRequest = {
        name: formData.name,
        description: formData.description,
        assignments: formData.assignments,
        account_ids: formData.account_ids,
      }
      await updateRoleAssignmentScheme(currentScheme.id, updateData)
      toast({
        title: "更新成功",
        description: "分配方案已更新",
      })
      setEditDialogOpen(false)
      loadSchemes()
    } catch (error: any) {
      toast({
        title: "更新失败",
        description: error.message || "无法更新分配方案",
        variant: "destructive",
      })
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (scheme: RoleAssignmentScheme) => {
    if (!confirm(`确定要删除分配方案 "${scheme.name}" 嗎？`)) {
      return
    }

    try {
      await deleteRoleAssignmentScheme(scheme.id)
      toast({
        title: "删除成功",
        description: "分配方案已删除",
      })
      loadSchemes()
    } catch (error: any) {
      toast({
        title: "删除失败",
        description: error.message || "无法删除分配方案",
        variant: "destructive",
      })
    }
  }

  const handleApply = async (scheme: RoleAssignmentScheme) => {
    try {
      // 重新获取完整的方案详情，确保获取到完整的 assignments 数据
      const fullScheme = await getRoleAssignmentScheme(scheme.id)
      setCurrentScheme(fullScheme)
      setApplyDialogOpen(true)
    } catch (error: any) {
      toast({
        title: "加载失败",
        description: error.message || "无法加载分配方案详情",
        variant: "destructive",
      })
      // 如果获取详情失败，使用列表中的数据
      setCurrentScheme(scheme)
      setApplyDialogOpen(true)
    }
  }

  const handleApplyScheme = async () => {
    if (!currentScheme) return

    try {
      setApplying(true)
      const request: ApplySchemeRequest = {}
      const result = await applyRoleAssignmentScheme(currentScheme.id, request)
      toast({
        title: "應用成功",
        description: result.message || `已應用 ${result.applied_count} 个账号`,
      })
      setApplyDialogOpen(false)
      loadSchemes()
    } catch (error: any) {
      toast({
        title: "應用失败",
        description: error.message || "无法應用分配方案",
        variant: "destructive",
      })
    } finally {
      setApplying(false)
    }
  }

  const handleViewHistory = async (scheme: RoleAssignmentScheme) => {
    setCurrentScheme(scheme)
    try {
      const data = await getRoleAssignmentSchemeHistory(scheme.id)
      setHistoryRecords(data.items || [])
      setHistoryDialogOpen(true)
    } catch (error: any) {
      toast({
        title: "加载历史失败",
        description: error.message || "无法加载應用历史",
        variant: "destructive",
      })
    }
  }

  const handleView = async (scheme: RoleAssignmentScheme) => {
    try {
      const data = await getRoleAssignmentScheme(scheme.id)
      setCurrentScheme(data)
      setViewDialogOpen(true)
    } catch (error: any) {
      toast({
        title: "加载失败",
        description: error.message || "无法加载方案详情",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <StepIndicator currentStep={4} steps={workflowSteps} />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">角色分配方案管理</h1>
          <p className="text-muted-foreground mt-2">
            保存和管理角色分配方案，支持方案重用和历史記錄
          </p>
        </div>
        <PermissionGuard permission="role_assignment_scheme:create">
          <Button onClick={() => setCreateDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            创建方案
          </Button>
        </PermissionGuard>
      </div>

      {/* 搜索和過濾 */}
      {schemes.length > 0 && (
        <div className="flex gap-4 mb-4 flex-wrap">
          <div className="flex-1 relative min-w-[200px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="搜索方案名稱或描述..."
              value={searchFilters.search || ""}
              onChange={(e) => {
                const newFilters = { ...searchFilters, search: e.target.value }
                setSearchFilters(newFilters)
                if (!e.target.value) {
                  loadSchemes({ ...newFilters, search: undefined })
                }
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  loadSchemes()
                }
              }}
              className="pl-10"
            />
          </div>
          <Select
            value={searchFilters.script_id || "__all__"}
            onValueChange={(value) => {
              const newFilters = { ...searchFilters, script_id: value === "__all__" ? undefined : value }
              setSearchFilters(newFilters)
              loadSchemes(newFilters)
            }}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="全部剧本" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">全部剧本</SelectItem>
              {scripts.map((script) => (
                <SelectItem key={script.script_id} value={script.script_id}>
                  {script.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={searchFilters.mode || "__all__"}
            onValueChange={(value) => {
              const newFilters = { ...searchFilters, mode: value === "__all__" ? undefined : value }
              setSearchFilters(newFilters)
              loadSchemes(newFilters)
            }}
          >
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="全部模式" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">全部模式</SelectItem>
              <SelectItem value="auto">自动</SelectItem>
              <SelectItem value="manual">手动</SelectItem>
            </SelectContent>
          </Select>
          {(searchFilters.search || searchFilters.script_id || searchFilters.mode) && (
            <Button
              variant="outline"
              onClick={() => {
                setSearchFilters({})
                loadSchemes({})
              }}
            >
              <X className="h-4 w-4 mr-2" />
              清除
            </Button>
          )}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : schemes.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">暫无分配方案</p>
            <PermissionGuard permission="role_assignment_scheme:create">
              <Button
                className="mt-4"
                onClick={() => setCreateDialogOpen(true)}
              >
                <Plus className="mr-2 h-4 w-4" />
                创建第一个方案
              </Button>
            </PermissionGuard>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>分配方案列表</CardTitle>
                <CardDescription>共 {schemes.length} 个方案</CardDescription>
              </div>
              <PermissionGuard permission="export:role_assignment_scheme">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" disabled={loading || schemes.length === 0}>
                      <Download className="mr-2 h-4 w-4" />
                      导出
                    </Button>
                  </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuLabel>选择导出格式</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={async () => {
                      try {
                        const blob = await exportSchemes("csv")
                        const filename = `分配方案列表_${new Date().toISOString().slice(0, 10)}.csv`
                        downloadBlob(blob, filename)
                        toast({ title: "导出成功", description: "分配方案列表已导出為 CSV" })
                      } catch (error: any) {
                        toast({
                          title: "导出失败",
                          description: error.message || "无法导出分配方案列表",
                          variant: "destructive",
                        })
                      }
                    }}
                  >
                    CSV 格式
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={async () => {
                      try {
                        const blob = await exportSchemes("excel")
                        const filename = `分配方案列表_${new Date().toISOString().slice(0, 10)}.xlsx`
                        downloadBlob(blob, filename)
                        toast({ title: "导出成功", description: "分配方案列表已导出為 Excel" })
                      } catch (error: any) {
                        toast({
                          title: "导出失败",
                          description: error.message || "无法导出分配方案列表",
                          variant: "destructive",
                        })
                      }
                    }}
                  >
                    Excel 格式
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={async () => {
                      try {
                        const blob = await exportSchemes("pdf")
                        const filename = `分配方案列表_${new Date().toISOString().slice(0, 10)}.pdf`
                        downloadBlob(blob, filename)
                        toast({ title: "导出成功", description: "分配方案列表已导出為 PDF" })
                      } catch (error: any) {
                        toast({
                          title: "导出失败",
                          description: error.message || "无法导出分配方案列表",
                          variant: "destructive",
                        })
                      }
                    }}
                  >
                    PDF 格式
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              </PermissionGuard>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>方案名稱</TableHead>
                  <TableHead>剧本</TableHead>
                  <TableHead>分配模式</TableHead>
                  <TableHead>账号數量</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {schemes.map((scheme) => (
                  <TableRow key={scheme.id}>
                    <TableCell className="font-medium">{scheme.name}</TableCell>
                    <TableCell>
                      {scheme.script_name || scheme.script_id}
                    </TableCell>
                    <TableCell>
                      <Badge variant={scheme.mode === "auto" ? "default" : "secondary"}>
                        {scheme.mode === "auto" ? "自动" : "手动"}
                      </Badge>
                    </TableCell>
                    <TableCell>{scheme.account_ids.length}</TableCell>
                    <TableCell>
                      {new Date(scheme.created_at).toLocaleString("zh-TW")}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <PermissionGuard permission="role_assignment_scheme:view">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleView(scheme)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </PermissionGuard>
                        <PermissionGuard permission="role_assignment_scheme:update">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(scheme)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                        </PermissionGuard>
                        <PermissionGuard permission="role_assignment_scheme:apply">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleApply(scheme)}
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                        </PermissionGuard>
                        <PermissionGuard permission="role_assignment_scheme:view">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewHistory(scheme)}
                          >
                            <History className="h-4 w-4" />
                          </Button>
                        </PermissionGuard>
                        <PermissionGuard permission="role_assignment_scheme:delete">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(scheme)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </PermissionGuard>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* 创建方案对话框 */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>创建分配方案</DialogTitle>
            <DialogDescription>
              创建一个新的角色分配方案，可以保存並重複使用
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">方案名稱 *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="输入方案名稱"
              />
            </div>
            <div>
              <Label htmlFor="description">方案描述</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="输入方案描述（可选）"
                rows={3}
              />
            </div>
            <div>
              <Label htmlFor="script">选择剧本 *</Label>
              <Select
                value={selectedScriptId}
                onValueChange={handleScriptChange}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择剧本" />
                </SelectTrigger>
                <SelectContent>
                  {scripts.map((script) => (
                    <SelectItem key={script.script_id} value={script.script_id}>
                      {script.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {selectedScriptId && (
              <>
                <div>
                  <Label htmlFor="accounts">选择账号 *</Label>
                  <div className="border rounded-md p-4 max-h-48 overflow-y-auto">
                    {accounts.map((account) => (
                      <div key={account.account_id} className="flex items-center space-x-2 py-1">
                        <input
                          type="checkbox"
                          id={`account-${account.account_id}`}
                          checked={formData.account_ids.includes(account.account_id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData({
                                ...formData,
                                account_ids: [...formData.account_ids, account.account_id],
                              })
                            } else {
                              setFormData({
                                ...formData,
                                account_ids: formData.account_ids.filter(
                                  (id) => id !== account.account_id
                                ),
                              })
                            }
                          }}
                        />
                        <label
                          htmlFor={`account-${account.account_id}`}
                          className="text-sm cursor-pointer"
                        >
                          {account.display_name || account.account_id}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <Label htmlFor="mode">分配模式</Label>
                  <Select
                    value={formData.mode}
                    onValueChange={(value) =>
                      setFormData({ ...formData, mode: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auto">自动分配</SelectItem>
                      <SelectItem value="manual">手动分配</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {formData.account_ids.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <Label>分配方案</Label>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleCreateAssignment}
                      >
                        生成分配方案
                      </Button>
                    </div>
                    {assignmentResult && (
                      <div className="border rounded-md p-4 space-y-2">
                        <div className="text-sm text-muted-foreground">
                          验证状态:{" "}
                          <Badge
                            variant={
                              assignmentResult.validation?.is_valid
                                ? "default"
                                : "destructive"
                            }
                          >
                            {assignmentResult.validation?.is_valid
                              ? "有效"
                              : "无效"}
                          </Badge>
                        </div>
                        {assignmentResult.summary && (
                          <div className="text-sm space-y-1">
                            <p>總角色数: {assignmentResult.summary.total_roles}</p>
                            <p>已分配: {assignmentResult.summary.assigned_roles}</p>
                            <p>未分配: {assignmentResult.summary.unassigned_roles}</p>
                          </div>
                        )}
                        {formData.assignments.length > 0 && (
                          <div className="mt-4">
                            <p className="text-sm font-medium mb-2">分配详情:</p>
                            <div className="space-y-1 max-h-32 overflow-y-auto">
                              {formData.assignments.map((assignment, index) => (
                                <div
                                  key={index}
                                  className="text-xs p-2 bg-muted rounded"
                                >
                                  {(assignment as any).role_name || assignment.role_id} →{" "}
                                  {accounts.find(
                                    (a) => a.account_id === assignment.account_id
                                  )?.display_name || assignment.account_id}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCreateDialogOpen(false)}
            >
              取消
            </Button>
            <PermissionGuard permission="role_assignment_scheme:create">
              <Button onClick={handleCreateScheme} disabled={creating}>
                {creating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                创建
              </Button>
            </PermissionGuard>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑方案对话框 */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>编辑分配方案</DialogTitle>
            <DialogDescription>
              修改分配方案的名稱、描述和分配配置
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="edit-name">方案名稱 *</Label>
              <Input
                id="edit-name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
              />
            </div>
            <div>
              <Label htmlFor="edit-description">方案描述</Label>
              <Textarea
                id="edit-description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                rows={3}
              />
            </div>
            {formData.assignments.length > 0 && (
              <div>
                <Label>分配详情</Label>
                <div className="border rounded-md p-4 space-y-2 max-h-48 overflow-y-auto">
                  {formData.assignments.map((assignment, index) => (
                    <div
                      key={index}
                      className="text-sm p-2 bg-muted rounded flex items-center justify-between"
                    >
                      <span>
                        {(assignment as any).role_name || assignment.role_id} →{" "}
                        {accounts.find(
                          (a) => a.account_id === assignment.account_id
                        )?.display_name || assignment.account_id}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const newAssignments = [...formData.assignments]
                          newAssignments.splice(index, 1)
                          setFormData({ ...formData, assignments: newAssignments })
                        }}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setEditDialogOpen(false)}
            >
              取消
            </Button>
            <PermissionGuard permission="role_assignment_scheme:update">
              <Button onClick={handleUpdateScheme} disabled={creating}>
                {creating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                保存
              </Button>
            </PermissionGuard>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 應用方案对话框 */}
      <Dialog open={applyDialogOpen} onOpenChange={setApplyDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>應用分配方案</DialogTitle>
            <DialogDescription>
              确定要應用方案 "{currentScheme?.name}" 到账号嗎？
            </DialogDescription>
          </DialogHeader>
          {currentScheme && (
            <div className="space-y-2">
              <p className="text-sm">
                剧本: {currentScheme.script_name || currentScheme.script_id}
              </p>
              <p className="text-sm">
                账号數量: {currentScheme.account_ids?.length || 0}
              </p>
              <p className="text-sm">
                分配數量: {currentScheme.assignments?.length || 0}
              </p>
              {(!currentScheme.assignments || currentScheme.assignments.length === 0) && (
                <div className="mt-2 p-2 bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-800 rounded text-sm text-yellow-800 dark:text-yellow-200">
                  ⚠️ 警告：此方案沒有分配数据，請先编辑方案並创建分配關係
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setApplyDialogOpen(false)}
            >
              取消
            </Button>
            <PermissionGuard permission="role_assignment_scheme:apply">
              <Button onClick={handleApplyScheme} disabled={applying}>
                {applying && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                應用
              </Button>
            </PermissionGuard>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 查看详情对话框 */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>方案详情</DialogTitle>
            <DialogDescription>
              {currentScheme?.name}
            </DialogDescription>
          </DialogHeader>
          {currentScheme && (
            <div className="space-y-4">
              <div>
                <Label>描述</Label>
                <p className="text-sm text-muted-foreground">
                  {currentScheme.description || "无描述"}
                </p>
              </div>
              <div>
                <Label>剧本</Label>
                <p className="text-sm">
                  {currentScheme.script_name || currentScheme.script_id}
                </p>
              </div>
              <div>
                <Label>分配模式</Label>
                <Badge variant={currentScheme.mode === "auto" ? "default" : "secondary"}>
                  {currentScheme.mode === "auto" ? "自动" : "手动"}
                </Badge>
              </div>
              <div>
                <Label>分配详情</Label>
                <div className="border rounded-md p-4 space-y-2 max-h-64 overflow-y-auto">
                  {currentScheme.assignments.map((assignment, index) => (
                    <div
                      key={index}
                      className="text-sm p-2 bg-muted rounded"
                    >
                      <strong>{assignment.role_name || assignment.role_id}</strong> →{" "}
                      {accounts.find(
                        (a) => a.account_id === assignment.account_id
                      )?.display_name || assignment.account_id}
                      {assignment.weight && (
                        <span className="text-muted-foreground ml-2">
                          (權重: {assignment.weight})
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setViewDialogOpen(false)}>关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 查看历史对话框 */}
      <Dialog open={historyDialogOpen} onOpenChange={setHistoryDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>應用历史</DialogTitle>
            <DialogDescription>
              方案 "{currentScheme?.name}" 的應用历史記錄
            </DialogDescription>
          </DialogHeader>
          {historyRecords.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              暫无應用历史
            </p>
          ) : (
            <div className="space-y-2">
              {historyRecords.map((record) => (
                <div
                  key={record.id}
                  className="border rounded-md p-4 space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">
                        账号: {accounts.find((a) => a.account_id === record.account_id)?.display_name || record.account_id}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        角色: {record.role_id}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-muted-foreground">
                        {new Date(record.applied_at).toLocaleString("zh-TW")}
                      </p>
                      {record.applied_by && (
                        <p className="text-xs text-muted-foreground">
                          應用者: {record.applied_by}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setHistoryDialogOpen(false)}>关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

