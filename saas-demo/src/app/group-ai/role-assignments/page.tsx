"use client"

import { useState, useEffect, Suspense } from "react"
import dynamic from "next/dynamic"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { PermissionGuard } from "@/components/permissions/permission-guard"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"

// 懒加载重型组件
const Table = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.Table })), { ssr: false })
const TableBody = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableBody })), { ssr: false })
const TableCell = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableCell })), { ssr: false })
const TableHead = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableHead })), { ssr: false })
const TableHeader = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableHeader })), { ssr: false })
const TableRow = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableRow })), { ssr: false })
const Select = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.Select })), { ssr: false })
const SelectContent = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectContent })), { ssr: false })
const SelectItem = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectItem })), { ssr: false })
const SelectTrigger = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectTrigger })), { ssr: false })
const SelectValue = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectValue })), { ssr: false })
const Tabs = dynamic(() => import("@/components/ui/tabs").then(mod => ({ default: mod.Tabs })), { ssr: false })
const TabsContent = dynamic(() => import("@/components/ui/tabs").then(mod => ({ default: mod.TabsContent })), { ssr: false })
const TabsList = dynamic(() => import("@/components/ui/tabs").then(mod => ({ default: mod.TabsList })), { ssr: false })
const TabsTrigger = dynamic(() => import("@/components/ui/tabs").then(mod => ({ default: mod.TabsTrigger })), { ssr: false })
const AlertDialog = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialog })), { ssr: false })
const AlertDialogAction = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogAction })), { ssr: false })
const AlertDialogCancel = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogCancel })), { ssr: false })
const AlertDialogContent = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogContent })), { ssr: false })
const AlertDialogDescription = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogDescription })), { ssr: false })
const AlertDialogFooter = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogFooter })), { ssr: false })
const AlertDialogHeader = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogHeader })), { ssr: false })
const AlertDialogTitle = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogTitle })), { ssr: false })
import { 
  Users, 
  RefreshCw, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle,
  Play,
  Loader2
} from "lucide-react"
import { 
  extractRoles, 
  createAssignment, 
  applyAssignment,
  getScripts,
  getAccounts,
  type ExtractRolesResponse,
  type AssignmentResponse,
  type Role,
  type RoleAssignment,
  type Script,
  type Account
} from "@/lib/api/group-ai"
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
    status: "current",
  },
  {
    number: 4,
    title: "分配方案",
    description: "保存和重用角色分配方案（可选）",
    href: "/group-ai/role-assignment-schemes",
    status: "optional",
  },
  {
    number: 5,
    title: "自动化任务",
    description: "配置自动化执行任务（可选）",
    href: "/group-ai/automation-tasks",
    status: "optional",
  },
];

// localStorage 键名
const STORAGE_KEYS = {
  SELECTED_SCRIPT_ID: "role_assignment_selected_script_id",
  EXTRACTED_ROLES: "role_assignment_extracted_roles",
  SELECTED_ACCOUNT_IDS: "role_assignment_selected_account_ids",
  ASSIGNMENT_MODE: "role_assignment_mode",
  MANUAL_ASSIGNMENTS: "role_assignment_manual_assignments",
  ASSIGNMENT_PLAN: "role_assignment_plan",
}

export default function RoleAssignmentsPage() {
  const [scripts, setScripts] = useState<Script[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [selectedScriptId, setSelectedScriptId] = useState<string>("")
  const [roles, setRoles] = useState<Role[]>([])
  const [loadingRoles, setLoadingRoles] = useState(false)
  const [assignmentPlan, setAssignmentPlan] = useState<AssignmentResponse | null>(null)
  const [creatingAssignment, setCreatingAssignment] = useState(false)
  const [applyingAssignment, setApplyingAssignment] = useState(false)
  const [assignmentMode, setAssignmentMode] = useState<"auto" | "manual">("auto")
  const [manualAssignments, setManualAssignments] = useState<Record<string, string>>({})
  const [selectedAccountIds, setSelectedAccountIds] = useState<string[]>([])
  const [rolesSaved, setRolesSaved] = useState(false) // 标记角色是否已保存

  // 对话框状态
  const [errorDialogOpen, setErrorDialogOpen] = useState(false)
  const [errorDialogTitle, setErrorDialogTitle] = useState("")
  const [errorDialogMessage, setErrorDialogMessage] = useState("")
  const [successDialogOpen, setSuccessDialogOpen] = useState(false)
  const [successDialogTitle, setSuccessDialogTitle] = useState("")
  const [successDialogMessage, setSuccessDialogMessage] = useState("")
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false)
  const [confirmDialogTitle, setConfirmDialogTitle] = useState("")
  const [confirmDialogMessage, setConfirmDialogMessage] = useState("")
  const [confirmDialogOnConfirm, setConfirmDialogOnConfirm] = useState<(() => void) | null>(null)

  // 从 localStorage 恢复数据
  useEffect(() => {
    try {
      const savedScriptId = localStorage.getItem(STORAGE_KEYS.SELECTED_SCRIPT_ID)
      if (savedScriptId) {
        setSelectedScriptId(savedScriptId)
      }

      const savedRoles = localStorage.getItem(STORAGE_KEYS.EXTRACTED_ROLES)
      if (savedRoles) {
        const parsedRoles = JSON.parse(savedRoles)
        setRoles(parsedRoles)
        setRolesSaved(true) // 标记为已保存
      }

      const savedAccountIds = localStorage.getItem(STORAGE_KEYS.SELECTED_ACCOUNT_IDS)
      if (savedAccountIds) {
        setSelectedAccountIds(JSON.parse(savedAccountIds))
      }

      const savedMode = localStorage.getItem(STORAGE_KEYS.ASSIGNMENT_MODE)
      if (savedMode) {
        setAssignmentMode(savedMode as "auto" | "manual")
      }

      const savedManualAssignments = localStorage.getItem(STORAGE_KEYS.MANUAL_ASSIGNMENTS)
      if (savedManualAssignments) {
        setManualAssignments(JSON.parse(savedManualAssignments))
      }

      const savedPlan = localStorage.getItem(STORAGE_KEYS.ASSIGNMENT_PLAN)
      if (savedPlan) {
        setAssignmentPlan(JSON.parse(savedPlan))
      }
    } catch (err) {
      console.error("[角色分配] 恢复数据失败:", err)
    }
  }, [])

  // 保存数据到 localStorage
  useEffect(() => {
    if (selectedScriptId) {
      localStorage.setItem(STORAGE_KEYS.SELECTED_SCRIPT_ID, selectedScriptId)
    }
  }, [selectedScriptId])

  useEffect(() => {
    if (roles.length > 0 && rolesSaved) {
      localStorage.setItem(STORAGE_KEYS.EXTRACTED_ROLES, JSON.stringify(roles))
    }
  }, [roles, rolesSaved])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.SELECTED_ACCOUNT_IDS, JSON.stringify(selectedAccountIds))
  }, [selectedAccountIds])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.ASSIGNMENT_MODE, assignmentMode)
  }, [assignmentMode])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.MANUAL_ASSIGNMENTS, JSON.stringify(manualAssignments))
  }, [manualAssignments])

  useEffect(() => {
    if (assignmentPlan) {
      localStorage.setItem(STORAGE_KEYS.ASSIGNMENT_PLAN, JSON.stringify(assignmentPlan))
    }
  }, [assignmentPlan])

  useEffect(() => {
    fetchScripts()
    fetchAccounts()
  }, [])

  const fetchScripts = async () => {
    try {
      const data = await getScripts()
      setScripts(data || [])
      // 移除空列表警告，因為空列表不代表错误（可能只是尚未创建剧本）
    } catch (err) {
      console.error("[角色分配] 加载剧本列表失败:", err)
      // 设置空數組而不是顯示错误，避免干擾用户
      setScripts([])
      // 只在明確的错误情況下顯示错误消息
      if (err instanceof Error && !err.message.includes("fetch") && !err.message.includes("HTTP 500")) {
        showError("加载失败", err.message)
      }
    }
  }

  const fetchAccounts = async () => {
    try {
      const data = await getAccounts()
      const accountList = Array.isArray(data) ? data : (data as any)?.items || []
      setAccounts(accountList)
      // 移除空列表警告，因為空列表不代表错误（可能只是尚未创建账号）
    } catch (err) {
      console.error("[角色分配] 加载账号列表失败:", err)
      // 设置空數組而不是顯示错误，避免干擾用户
      setAccounts([])
      // 只在明確的错误情況下顯示错误消息
      if (err instanceof Error && !err.message.includes("fetch") && !err.message.includes("HTTP 500")) {
        showError("加载失败", err.message)
      }
    }
  }

  const handleExtractRoles = async () => {
    if (!selectedScriptId) {
      showError("错误", "請先选择剧本")
      return
    }

    try {
      setLoadingRoles(true)
      const response = await extractRoles(selectedScriptId)
      setRoles(response.roles)
      setRolesSaved(false) // 标记为未保存，需要用户确认
      showSuccess("提取成功", `成功提取 ${response.total_roles} 个角色，請点击「确认保存」按鈕保存数据`)
    } catch (err) {
      showError("提取失败", err instanceof Error ? err.message : "无法提取角色")
    } finally {
      setLoadingRoles(false)
    }
  }

  // 确认保存提取的角色数据
  const handleConfirmSaveRoles = () => {
    if (roles.length === 0) {
      showError("错误", "沒有可保存的角色数據")
      return
    }
    
    try {
      localStorage.setItem(STORAGE_KEYS.EXTRACTED_ROLES, JSON.stringify(roles))
      setRolesSaved(true)
      showSuccess("保存成功", "角色数據已保存，切換菜單不會丟失")
    } catch (err) {
      showError("保存失败", "无法保存角色数據到本地存儲")
    }
  }

  // 清除保存的数据
  const handleClearSavedData = () => {
    showConfirm(
      "确认清除",
      "确定要清除所有已保存的数据嗎？此操作不可恢复。",
      () => {
        localStorage.removeItem(STORAGE_KEYS.SELECTED_SCRIPT_ID)
        localStorage.removeItem(STORAGE_KEYS.EXTRACTED_ROLES)
        localStorage.removeItem(STORAGE_KEYS.SELECTED_ACCOUNT_IDS)
        localStorage.removeItem(STORAGE_KEYS.ASSIGNMENT_MODE)
        localStorage.removeItem(STORAGE_KEYS.MANUAL_ASSIGNMENTS)
        localStorage.removeItem(STORAGE_KEYS.ASSIGNMENT_PLAN)
        
        setSelectedScriptId("")
        setRoles([])
        setSelectedAccountIds([])
        setAssignmentMode("auto")
        setManualAssignments({})
        setAssignmentPlan(null)
        setRolesSaved(false)
        
        showSuccess("清除成功", "所有数据已清除")
      }
    )
  }

  const handleCreateAssignment = async () => {
    if (!selectedScriptId) {
      showError("错误", "請先选择剧本")
      return
    }

    if (selectedAccountIds.length === 0) {
      showError("错误", "請至少选择一个账号")
      return
    }

    if (roles.length === 0) {
      showError("错误", "請先提取角色")
      return
    }

    try {
      setCreatingAssignment(true)
      const response = await createAssignment({
        script_id: selectedScriptId,
        account_ids: selectedAccountIds,
        mode: assignmentMode,
        manual_assignments: assignmentMode === "manual" ? manualAssignments : undefined,
      })
      setAssignmentPlan(response)
      showSuccess("创建成功", "分配方案已生成")
    } catch (err) {
      showError("创建失败", err instanceof Error ? err.message : "无法创建分配方案")
    } finally {
      setCreatingAssignment(false)
    }
  }

  const handleApplyAssignment = async () => {
    if (!assignmentPlan) {
      showError("错误", "沒有可應用的分配方案")
      return
    }

    const assignments: Record<string, string> = {}
    assignmentPlan.assignments.forEach(a => {
      assignments[a.role_id] = a.account_id
    })

    showConfirm(
      "确认應用",
      `确定要應用分配方案到 ${assignmentPlan.assignments.length} 个角色嗎？`,
      async () => {
        try {
          setApplyingAssignment(true)
          const result = await applyAssignment(selectedScriptId, assignments)
          showSuccess("應用成功", result.message)
          // 刷新账号列表
          await fetchAccounts()
        } catch (err) {
          showError("應用失败", err instanceof Error ? err.message : "无法應用分配方案")
        } finally {
          setApplyingAssignment(false)
        }
      }
    )
  }

  const showError = (title: string, message: string) => {
    setErrorDialogTitle(title)
    setErrorDialogMessage(message)
    setErrorDialogOpen(true)
  }

  const showSuccess = (title: string, message: string) => {
    setSuccessDialogTitle(title)
    setSuccessDialogMessage(message)
    setSuccessDialogOpen(true)
  }

  const showConfirm = (title: string, message: string, onConfirm: () => void) => {
    setConfirmDialogTitle(title)
    setConfirmDialogMessage(message)
    setConfirmDialogOnConfirm(() => onConfirm)
    setConfirmDialogOpen(true)
  }

  const handleManualAssignmentChange = (roleId: string, accountId: string) => {
    setManualAssignments(prev => ({
      ...prev,
      [roleId]: accountId,
    }))
  }

  return (
    <PermissionGuard permission="role_assignment:view" fallback={
      <div className="container mx-auto py-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>您沒有權限查看角色分配</AlertDescription>
        </Alert>
      </div>
    }>
      <div className="container mx-auto py-6 space-y-6">
        <StepIndicator currentStep={3} steps={workflowSteps} />
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">角色分配管理</h1>
            <p className="text-muted-foreground mt-2">
              自动或手动分配剧本角色到账号
            </p>
          </div>
          <Button
            onClick={handleClearSavedData}
            variant="outline"
            size="sm"
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
          >
            <XCircle className="mr-2 h-4 w-4" />
            清除数据
          </Button>
        </div>

      <Tabs defaultValue="extract" className="space-y-4">
        <TabsList>
          <TabsTrigger value="extract">提取角色</TabsTrigger>
          <TabsTrigger value="assign">分配方案</TabsTrigger>
          <TabsTrigger value="review">審查方案</TabsTrigger>
        </TabsList>

        {/* 提取角色 */}
        <TabsContent value="extract">
          <Card>
            <CardHeader>
              <CardTitle>從剧本提取角色</CardTitle>
              <CardDescription>
                选择剧本並提取其中的角色列表
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>选择剧本</Label>
                <Select value={selectedScriptId} onValueChange={setSelectedScriptId}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择剧本" />
                  </SelectTrigger>
                  <SelectContent>
                    {scripts.map((script) => (
                      <SelectItem key={script.script_id} value={script.script_id}>
                        {script.name || script.script_id} (v{script.version})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <PermissionGuard permission="role_assignment:view">
                <Button 
                  onClick={handleExtractRoles} 
                  disabled={!selectedScriptId || loadingRoles}
                  className="w-full"
                >
                  {loadingRoles ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      提取中...
                    </>
                  ) : (
                    <>
                      <Users className="mr-2 h-4 w-4" />
                      提取角色
                    </>
                  )}
                </Button>
              </PermissionGuard>

              {roles.length > 0 && (
                <div className="mt-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">
                      提取到的角色 ({roles.length})
                      {rolesSaved && (
                        <Badge variant="outline" className="ml-2 text-green-600 border-green-600">
                          <CheckCircle2 className="mr-1 h-3 w-3" />
                          已保存
                        </Badge>
                      )}
                    </h3>
                    {!rolesSaved && (
                      <Button
                        onClick={handleConfirmSaveRoles}
                        variant="default"
                        size="sm"
                        className="bg-green-600 hover:bg-green-700"
                      >
                        <CheckCircle2 className="mr-2 h-4 w-4" />
                        确认保存
                      </Button>
                    )}
                  </div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>角色ID</TableHead>
                        <TableHead>角色名稱</TableHead>
                        <TableHead>台詞數量</TableHead>
                        <TableHead>權重</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {roles.map((role) => (
                        <TableRow key={role.role_id}>
                          <TableCell className="font-mono text-sm">{role.role_id}</TableCell>
                          <TableCell>{role.role_name}</TableCell>
                          <TableCell>{role.dialogue_count}</TableCell>
                          <TableCell>{role.dialogue_weight.toFixed(2)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  {rolesSaved && (
                    <div className="text-sm text-muted-foreground bg-green-50 dark:bg-green-950 p-2 rounded">
                      <CheckCircle2 className="inline mr-1 h-3 w-3 text-green-600" />
                      数据已保存，切換菜單不會丟失
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 分配方案 */}
        <TabsContent value="assign">
          <Card>
            <CardHeader>
              <CardTitle>创建分配方案</CardTitle>
              <CardDescription>
                选择账号並创建角色分配方案
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>选择账号</Label>
                <div className="grid grid-cols-2 gap-2 max-h-60 overflow-y-auto border rounded-md p-2">
                  {accounts.map((account) => (
                    <label key={account.account_id} className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedAccountIds.includes(account.account_id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedAccountIds([...selectedAccountIds, account.account_id])
                          } else {
                            setSelectedAccountIds(selectedAccountIds.filter(id => id !== account.account_id))
                          }
                        }}
                        className="rounded"
                      />
                      <span className="text-sm">
                        {account.account_id} 
                        <Badge variant="outline" className="ml-2">{account.status}</Badge>
                      </span>
                    </label>
                  ))}
                </div>
                <p className="text-sm text-muted-foreground">
                  已选择 {selectedAccountIds.length} 个账号
                </p>
              </div>

              <div className="space-y-2">
                <Label>分配模式</Label>
                <Select value={assignmentMode} onValueChange={(v) => setAssignmentMode(v as "auto" | "manual")}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">自动分配</SelectItem>
                    <SelectItem value="manual">手动分配</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {assignmentMode === "manual" && roles.length > 0 && (
                <div className="space-y-2">
                  <Label>手动分配角色</Label>
                  <div className="space-y-2 max-h-60 overflow-y-auto border rounded-md p-2">
                    {roles.map((role) => (
                      <div key={role.role_id} className="flex items-center space-x-2">
                        <span className="w-32 text-sm">{role.role_name}</span>
                        <Select
                          value={manualAssignments[role.role_id] || ""}
                          onValueChange={(v) => handleManualAssignmentChange(role.role_id, v)}
                        >
                          <SelectTrigger className="flex-1">
                            <SelectValue placeholder="选择账号" />
                          </SelectTrigger>
                          <SelectContent>
                            {selectedAccountIds.map((accountId) => (
                              <SelectItem key={accountId} value={accountId}>
                                {accountId}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <PermissionGuard permission="role_assignment:create">
                <Button 
                  onClick={handleCreateAssignment} 
                  disabled={creatingAssignment || selectedAccountIds.length === 0 || roles.length === 0}
                  className="w-full"
                >
                  {creatingAssignment ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      创建中...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="mr-2 h-4 w-4" />
                      创建分配方案
                    </>
                  )}
                </Button>
              </PermissionGuard>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 審查方案 */}
        <TabsContent value="review">
          {assignmentPlan ? (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>分配方案详情</CardTitle>
                  <CardDescription>
                    審查分配方案並應用
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* 验证結果 */}
                  <div className={`p-4 rounded-lg border ${
                    assignmentPlan.validation.is_valid 
                      ? "bg-green-50 border-green-200" 
                      : "bg-yellow-50 border-yellow-200"
                  }`}>
                    <div className="flex items-center space-x-2 mb-2">
                      {assignmentPlan.validation.is_valid ? (
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                      ) : (
                        <AlertTriangle className="h-5 w-5 text-yellow-600" />
                      )}
                      <span className="font-semibold">
                        {assignmentPlan.validation.is_valid ? "方案有效" : "方案有問題"}
                      </span>
                    </div>
                    {assignmentPlan.validation.errors.length > 0 && (
                      <ul className="list-disc list-inside text-sm text-yellow-800">
                        {assignmentPlan.validation.errors.map((error, idx) => (
                          <li key={idx}>{error}</li>
                        ))}
                      </ul>
                    )}
                  </div>

                  {/* 分配列表 */}
                  <div>
                    <h3 className="text-lg font-semibold mb-2">角色分配列表</h3>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>角色</TableHead>
                          <TableHead>账号</TableHead>
                          <TableHead>負載權重</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {assignmentPlan.assignments.map((assignment) => (
                          <TableRow key={assignment.role_id}>
                            <TableCell>{assignment.role_name}</TableCell>
                            <TableCell className="font-mono text-sm">{assignment.account_id}</TableCell>
                            <TableCell>{assignment.weight.toFixed(2)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  {/* 账号負載統計 */}
                  <div>
                    <h3 className="text-lg font-semibold mb-2">账号負載統計</h3>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>账号</TableHead>
                          <TableHead>角色数量</TableHead>
                          <TableHead>總負載</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {Object.entries(assignmentPlan.summary.account_assignments).map(([accountId, data]) => (
                          <TableRow key={accountId}>
                            <TableCell className="font-mono text-sm">{accountId}</TableCell>
                            <TableCell>{data.roles.length}</TableCell>
                            <TableCell>{data.total_weight.toFixed(2)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  <PermissionGuard permission="role_assignment:create">
                    <Button 
                      onClick={handleApplyAssignment} 
                      disabled={applyingAssignment || !assignmentPlan.validation.is_valid}
                      className="w-full"
                    >
                      {applyingAssignment ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          應用中...
                        </>
                      ) : (
                        <>
                          <Play className="mr-2 h-4 w-4" />
                          應用分配方案
                        </>
                      )}
                    </Button>
                  </PermissionGuard>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                請先在「分配方案」標籤页创建分配方案
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* 错误对话框 */}
      <AlertDialog open={errorDialogOpen} onOpenChange={setErrorDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center space-x-2">
              <XCircle className="h-5 w-5 text-red-500" />
              <span>{errorDialogTitle}</span>
            </AlertDialogTitle>
            <AlertDialogDescription>{errorDialogMessage}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogAction onClick={() => setErrorDialogOpen(false)}>确定</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 成功对话框 */}
      <AlertDialog open={successDialogOpen} onOpenChange={setSuccessDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center space-x-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              <span>{successDialogTitle}</span>
            </AlertDialogTitle>
            <AlertDialogDescription>{successDialogMessage}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogAction onClick={() => setSuccessDialogOpen(false)}>确定</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 确认对话框 */}
      <AlertDialog open={confirmDialogOpen} onOpenChange={setConfirmDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmDialogTitle}</AlertDialogTitle>
            <AlertDialogDescription>{confirmDialogMessage}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={() => {
              if (confirmDialogOnConfirm) {
                confirmDialogOnConfirm()
              }
              setConfirmDialogOpen(false)
            }}>
              确定
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      </div>
    </PermissionGuard>
  )
}

