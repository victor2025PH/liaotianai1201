"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
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
import { Plus, Play, Square, RefreshCw, Trash2, Settings, Upload, Scan, FileText, Users, ArrowRight, MessageSquare, UserPlus, Edit, User, CheckSquare, Square as SquareIcon, MoreVertical, Download, Search, X } from "lucide-react"
import { Progress } from "@/components/ui/progress"
import { useRouter } from "next/navigation"
import { PermissionGuard } from "@/components/permissions/permission-guard"
import { PermissionButton } from "@/components/permissions/permission-button"
import { 
  getAccounts, 
  startAccount, 
  stopAccount,
  deleteAccount,
  createAccount,
  updateAccount,
  uploadSessionFile,
  scanSessions,
  getScripts,
  createGroup,
  joinGroup,
  startGroupChat,
  exportAccounts,
  downloadBlob,
  getWorkers,
  extractRoles,
  createAssignment,
  importTelegramAccounts,
  importTelegramAccountsBatch,
  type Account, 
  type AccountCreateRequest,
  type SessionFile,
  type Script,
  type WorkerAccount,
  type WorkersResponse,
  type Role,
  type ExtractRolesResponse,
  type ImportResult
} from "@/lib/api/group-ai"
import { getServers, type ServerStatus } from "@/lib/api/servers"
import { Textarea } from "@/components/ui/textarea"
import { Alert, AlertDescription } from "@/components/ui/alert"
import Image from "next/image"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
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
    status: "current",
  },
  {
    number: 3,
    title: "角色分配",
    description: "從剧本提取角色並分配給账号（可选）",
    href: "/group-ai/role-assignments",
    status: "optional",
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

// 确保 SessionFile 类型被正确导入

export default function GroupAIAccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [workerAccounts, setWorkerAccounts] = useState<Array<Account & { node_id: string, source: 'worker' }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [assignScriptMode, setAssignScriptMode] = useState(false) // 是否为分配剧本模式
  const [creating, setCreating] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [availableSessions, setAvailableSessions] = useState<SessionFile[]>([])
  const [scripts, setScripts] = useState<Script[]>([])
  const [servers, setServers] = useState<ServerStatus[]>([])
  const [formData, setFormData] = useState({
    account_id: "",
    session_file: "",
    script_id: "",
    role_id: "", // 添加角色ID字段
  })
  // 角色相关状态
  const [selectedScriptRoles, setSelectedScriptRoles] = useState<Role[]>([])
  const [roleAssignmentDialogOpen, setRoleAssignmentDialogOpen] = useState(false)
  const [assigningRole, setAssigningRole] = useState(false)
  const [selectedAccountForRole, setSelectedAccountForRole] = useState<Account | null>(null)
  const [accountRoleAssignments, setAccountRoleAssignments] = useState<Record<string, string>>({}) // account_id -> role_id
  const [allRoles, setAllRoles] = useState<Record<string, Role[]>>({}) // script_id -> roles[]，缓存所有剧本的角色
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editingAccount, setEditingAccount] = useState<Account | null>(null)
  const [editingForm, setEditingForm] = useState({
    display_name: "",
    bio: "",
    script_id: "",
    server_id: "",
  })
  const [updating, setUpdating] = useState(false)
  const [batchSelectDialogOpen, setBatchSelectDialogOpen] = useState(false)
  const [selectedSessions, setSelectedSessions] = useState<Set<string>>(new Set())
  const [batchCreating, setBatchCreating] = useState(false)
  const [batchCreateProgress, setBatchCreateProgress] = useState({
    current: 0,
    total: 0,
    currentAccountId: "",
  })
  
  // 批量操作相關状态
  const [selectedAccounts, setSelectedAccounts] = useState<Set<string>>(new Set())
  const [batchOperationDialogOpen, setBatchOperationDialogOpen] = useState(false)
  const [batchOperation, setBatchOperation] = useState<"update" | "start" | "stop" | "delete">("update")
  const [batchOperating, setBatchOperating] = useState(false)
  const [batchUpdateForm, setBatchUpdateForm] = useState({
    script_id: "",
    server_id: "",
    active: undefined as boolean | undefined,
  })
  
  // Telegram 賬號批量導入相關狀態
  const [importDialogOpen, setImportDialogOpen] = useState(false)
  const [importing, setImporting] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importResult, setImportResult] = useState<ImportResult | null>(null)
  
  const router = useRouter()

  // 居中对话框状态
  const [errorDialogOpen, setErrorDialogOpen] = useState(false)
  const [errorDialogTitle, setErrorDialogTitle] = useState("")
  const [errorDialogMessage, setErrorDialogMessage] = useState("")
  const [warningDialogOpen, setWarningDialogOpen] = useState(false)
  const [warningDialogTitle, setWarningDialogTitle] = useState("")
  const [warningDialogMessage, setWarningDialogMessage] = useState("")
  const [warningDialogOnConfirm, setWarningDialogOnConfirm] = useState<(() => void) | null>(null)
  // 批量创建确认对话框状态
  const [batchConfirmDialogOpen, setBatchConfirmDialogOpen] = useState(false)
  const [batchConfirmDialogTitle, setBatchConfirmDialogTitle] = useState("")
  const [batchConfirmDialogMessage, setBatchConfirmDialogMessage] = useState("")
  const [batchConfirmDialogAccountIds, setBatchConfirmDialogAccountIds] = useState<string[]>([])
  const [batchConfirmDialogScriptName, setBatchConfirmDialogScriptName] = useState("")
  const [batchConfirmDialogResolve, setBatchConfirmDialogResolve] = useState<((value: boolean) => void) | null>(null)
  const [successDialogOpen, setSuccessDialogOpen] = useState(false)
  const [successDialogTitle, setSuccessDialogTitle] = useState("")
  const [successDialogMessage, setSuccessDialogMessage] = useState("")
  const [successDialogOnClose, setSuccessDialogOnClose] = useState<(() => void) | null>(null)
  const [createGroupDialogOpen, setCreateGroupDialogOpen] = useState(false)
  const [createGroupAccountId, setCreateGroupAccountId] = useState("")
  const [createGroupForm, setCreateGroupForm] = useState({
    title: "",
    description: "",
    auto_reply: true
  })

  // 显示居中错误对话框
  const showErrorDialog = (title: string, message: string) => {
    setErrorDialogTitle(title)
    setErrorDialogMessage(message)
    setErrorDialogOpen(true)
  }

  // 显示居中警告对话框
  const showWarningDialog = (title: string, message: string, onConfirm?: () => void) => {
    setWarningDialogTitle(title)
    setWarningDialogMessage(message)
    setWarningDialogOnConfirm(() => onConfirm || null)
    setWarningDialogOpen(true)
  }

  // 显示居中成功对话框
  const showSuccessDialog = (title: string, message: string, onClose?: () => void) => {
    setSuccessDialogTitle(title)
    setSuccessDialogMessage(message)
    setSuccessDialogOnClose(() => onClose || null)
    setSuccessDialogOpen(true)
  }

  const [searchFilters, setSearchFilters] = useState<{
    search?: string
    status_filter?: string
    script_id?: string
    server_id?: string
    active?: boolean
    sort_by?: string
    sort_order?: "asc" | "desc"
  }>({})

  // 从Workers API获取所有节点账号
  const fetchWorkerAccounts = async () => {
    try {
      const workersData = await getWorkers()
      const workerAccs: Array<Account & { node_id: string, source: 'worker' }> = []
      
      // 遍历所有节点
      for (const [nodeId, worker] of Object.entries(workersData.workers || {})) {
        if (worker.status === "online" && worker.accounts) {
          // 遍历节点上的所有账号
          for (const workerAcc of worker.accounts) {
            // 检查是否已经在数据库账号列表中
            const existingAccount = accounts.find(acc => 
              acc.phone_number === workerAcc.phone || 
              acc.account_id === workerAcc.phone
            )
            
            // 如果不在数据库中，添加到Worker账号列表
            if (!existingAccount) {
              workerAccs.push({
                account_id: workerAcc.phone,
                phone_number: workerAcc.phone,
                first_name: workerAcc.first_name || undefined,
                username: undefined,
                display_name: workerAcc.first_name || workerAcc.phone,
                status: workerAcc.status === "online" ? "online" : "offline",
                script_id: "", // Worker账号可能还没有分配剧本
                server_id: nodeId,
                session_file: "", // Worker账号的session文件在节点上
                group_count: 0,
                message_count: 0,
                reply_count: 0,
                node_id: nodeId,
                source: 'worker' as const,
                // 如果Worker账号有角色信息，保存到角色分配映射中
                ...(workerAcc.role_name && {
                  // 这里可以保存角色信息
                })
              })
            }
          }
        }
      }
      
      setWorkerAccounts(workerAccs)
    } catch (err) {
      console.warn("获取Worker节点账号失败:", err)
      // 不显示错误，因为Worker节点可能暂时不可用
    }
  }

  const fetchAccounts = async (filters?: typeof searchFilters) => {
    try {
      setLoading(true)
      setError(null)
      const params = {
        page: 1,
        page_size: 100, // 后端限制最大100
        ...(filters || searchFilters),
      }
      const data = await getAccounts(params)
      setAccounts(Array.isArray(data) ? data : (data as any)?.items || [])
      
      // 获取Worker节点账号
      await fetchWorkerAccounts()
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败")
      showErrorDialog("加载失败", err instanceof Error ? err.message : "无法加载账号列表")
    } finally {
      setLoading(false)
    }
  }

  const fetchSessions = async () => {
    try {
      setScanning(true)
      const result = await scanSessions()
      setAvailableSessions(result.sessions)
      if (result.sessions && result.sessions.length > 0) {
        showSuccessDialog("掃描成功", `找到 ${result.sessions.length} 个 session 文件`)
      } else {
        showWarningDialog("扫描完成", "未找到任何 session 文件，請确认文件已放置在 sessions 目錄中")
      }
    } catch (err) {
      console.error("扫描 Session 失败:", err)
      showErrorDialog("掃描失败", err instanceof Error ? err.message : "无法掃描 session 文件")
    } finally {
      setScanning(false)
    }
  }

  const fetchServers = async () => {
    try {
      const data = await getServers()
      setServers(data)
    } catch (err) {
      console.error("獲取服务器列表失败:", err)
    }
  }

  const fetchScripts = async () => {
    try {
      const data = await getScripts()
      setScripts(data)
    } catch (err) {
      console.error("加载剧本列表失败:", err)
    }
  }

  // 当选择剧本时，自动加载角色列表
  const handleScriptSelect = async (scriptId: string) => {
    setFormData({ ...formData, script_id: scriptId, role_id: "" }) // 切换剧本时清空角色选择
    
    if (scriptId) {
      // 如果已缓存，直接使用
      if (allRoles[scriptId]) {
        setSelectedScriptRoles(allRoles[scriptId])
      } else {
        try {
          const rolesData = await extractRoles(scriptId)
          const roles = rolesData.roles || []
          setSelectedScriptRoles(roles)
          // 缓存角色列表
          setAllRoles({ ...allRoles, [scriptId]: roles })
        } catch (err) {
          console.warn("提取剧本角色失败:", err)
          setSelectedScriptRoles([])
        }
      }
    } else {
      setSelectedScriptRoles([])
    }
  }
  
  // 检查角色是否已被其他账号使用
  const isRoleAssigned = (roleId: string, currentAccountId?: string): { assigned: boolean; accountId?: string } => {
    for (const [accountId, assignedRoleId] of Object.entries(accountRoleAssignments)) {
      if (assignedRoleId === roleId && accountId !== currentAccountId) {
        // 检查该账号是否还存在（可能在账号列表中）
        const accountExists = accounts.some(acc => acc.account_id === accountId) || 
                              workerAccounts.some(acc => acc.account_id === accountId)
        if (accountExists) {
          return { assigned: true, accountId }
        }
      }
    }
    return { assigned: false }
  }
  
  // 获取使用该角色的账号名称
  const getAccountNameByRole = (roleId: string, currentAccountId?: string): string | null => {
    const { assigned, accountId } = isRoleAssigned(roleId, currentAccountId)
    if (assigned && accountId) {
      const account = accounts.find(acc => acc.account_id === accountId) || 
                     workerAccounts.find(acc => acc.account_id === accountId)
      return account ? (account.display_name || account.first_name || account.account_id) : accountId
    }
    return null
  }

  // 获取账号的角色名称（从缓存中查找）
  const getAccountRoleName = (account: Account): string | null => {
    if (!account.script_id || !accountRoleAssignments[account.account_id]) {
      return null
    }
    const roleId = accountRoleAssignments[account.account_id]
    const roles = allRoles[account.script_id] || []
    const role = roles.find(r => r.role_id === roleId)
    return role ? role.role_name : null
  }

  // 打开角色分配对话框
  const handleOpenRoleAssignment = async (account: Account) => {
    setSelectedAccountForRole(account)
    // 如果账号已有剧本，加载角色列表
    if (account.script_id) {
      // 如果已缓存，直接使用
      if (allRoles[account.script_id]) {
        setSelectedScriptRoles(allRoles[account.script_id])
      } else {
        try {
          const rolesData = await extractRoles(account.script_id)
          const roles = rolesData.roles || []
          setSelectedScriptRoles(roles)
          // 缓存角色列表
          setAllRoles({ ...allRoles, [account.script_id]: roles })
        } catch (err) {
          console.warn("提取剧本角色失败:", err)
          setSelectedScriptRoles([])
        }
      }
    } else {
      setSelectedScriptRoles([])
    }
    setRoleAssignmentDialogOpen(true)
  }

  // 分配角色
  const handleAssignRole = async (accountId: string, roleId: string) => {
    if (!selectedAccountForRole) return
    
    try {
      setAssigningRole(true)
      
      // 如果账号还没有剧本，需要先分配剧本
      if (!selectedAccountForRole.script_id) {
        showErrorDialog("错误", "请先为账号分配剧本")
        return
      }

      // 创建角色分配
      const assignment = await createAssignment({
        script_id: selectedAccountForRole.script_id,
        account_ids: [accountId],
        mode: "manual",
        manual_assignments: {
          [accountId]: roleId
        }
      })

      // 更新本地角色分配映射
      setAccountRoleAssignments({
        ...accountRoleAssignments,
        [accountId]: roleId
      })

      showSuccessDialog("成功", `账号 ${accountId} 已分配角色`)
      setRoleAssignmentDialogOpen(false)
      await fetchAccounts() // 刷新账号列表
    } catch (err) {
      showErrorDialog("分配失败", err instanceof Error ? err.message : "分配角色失败")
    } finally {
      setAssigningRole(false)
    }
  }

  // 自动分配角色（为多个账号自动分配角色）
  const handleAutoAssignRoles = async (accountIds: string[], scriptId: string) => {
    try {
      setAssigningRole(true)
      
      const assignment = await createAssignment({
        script_id: scriptId,
        account_ids: accountIds,
        mode: "auto"
      })

      // 更新本地角色分配映射
      const newAssignments: Record<string, string> = { ...accountRoleAssignments }
      assignment.assignments.forEach(ass => {
        if (ass.account_id && ass.role_id) {
          newAssignments[ass.account_id] = ass.role_id
        }
      })
      setAccountRoleAssignments(newAssignments)

      showSuccessDialog("成功", `已为 ${accountIds.length} 个账号自动分配角色`)
      await fetchAccounts() // 刷新账号列表
    } catch (err) {
      showErrorDialog("自动分配失败", err instanceof Error ? err.message : "自动分配角色失败")
    } finally {
      setAssigningRole(false)
    }
  }

  // 从Session文件名中提取账号ID（去掉.session扩展名）
  // Session文件名通常是：{phone_number}.session 或 {account_id}.session
  const extractAccountIdFromSessionFile = (filename: string): string => {
    // 移除 .session 扩展名，直接使用文件名作为账号ID
    return filename.replace(/\.session$/i, "")
  }

  useEffect(() => {
    fetchAccounts()
    fetchScripts()
    fetchServers()
    // 只在页面加载时静默加载Session列表，不显示成功提示
    const loadSessionsSilently = async () => {
      try {
        const result = await scanSessions()
        setAvailableSessions(result.sessions)
      } catch (err) {
        // 静默失败，不显示错误提示
        console.error("加载Session列表失败:", err)
      }
    }
    loadSessionsSilently()
    fetchScripts()
  }, [])

  const handleStart = async (accountId: string) => {
    try {
      await startAccount(accountId)
      showSuccessDialog("成功", `账号 ${accountId} 已启动`)
      await fetchAccounts()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "启动账号失败"
      showErrorDialog("启动失败", errorMessage)
      console.error(`启动账号 ${accountId} 失败:`, err)
      // 即使失败也刷新列表，確保状态同步
      await fetchAccounts()
    }
  }

  const handleStop = async (accountId: string) => {
    try {
      await stopAccount(accountId)
      showSuccessDialog("成功", `账号 ${accountId} 已停止`)
      await fetchAccounts()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "停止账号失败"
      showErrorDialog("停止失败", errorMessage)
      console.error(`停止账号 ${accountId} 失败:`, err)
      // 即使失败也刷新列表，確保状态同步
      await fetchAccounts()
    }
  }

  // 批量導入 Telegram 賬號配置
  const handleImportTelegramAccounts = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // 檢查文件擴展名
    const validExtensions = ['.txt', '.csv', '.xlsx', '.xls']
    const fileExt = file.name.toLowerCase().slice(file.name.lastIndexOf('.'))
    if (!validExtensions.includes(fileExt)) {
      showErrorDialog("錯誤", `不支持的文件格式: ${fileExt}。支持格式: ${validExtensions.join(', ')}`)
      return
    }

    // 檢查文件大小（限制10MB）
    if (file.size > 10 * 1024 * 1024) {
      showErrorDialog("錯誤", "文件大小不能超過10MB")
      return
    }

    setImportFile(file)
    setImportDialogOpen(true)
  }

  const executeImport = async () => {
    if (!importFile) return

    try {
      setImporting(true)
      setImportResult(null)
      
      const result = await importTelegramAccounts(importFile)
      setImportResult(result)
      
      if (result.success > 0) {
        showSuccessDialog(
          "導入成功",
          `成功導入 ${result.success} 個賬號配置${result.failed > 0 ? `，失敗 ${result.failed} 個` : ''}`
        )
        // 刷新賬號列表
        await fetchAccounts()
      } else {
        showErrorDialog("導入失敗", `所有 ${result.total} 個賬號配置導入失敗`)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "導入失敗"
      showErrorDialog("導入失敗", errorMessage)
      console.error("導入 Telegram 賬號配置失敗:", err)
    } finally {
      setImporting(false)
    }
  }

  const handleUploadSession = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // 检查文件擴展名
    if (!file.name.endsWith('.session')) {
      showErrorDialog("错误", "只支持 .session 文件")
      return
    }

    // 检查文件大小（限制10MB）
    if (file.size > 10 * 1024 * 1024) {
      showErrorDialog("错误", "文件大小不能超過10MB")
      return
    }

    try {
      setUploading(true)
      const result = await uploadSessionFile(file)
      showSuccessDialog("上傳成功", result.message)
      // 刷新session列表
      await fetchSessions()
      // 自动选择上傳的文件
      setFormData({ ...formData, session_file: result.filename })
    } catch (err) {
      showErrorDialog("上傳失败", err instanceof Error ? err.message : "上傳 session 文件失败")
    } finally {
      setUploading(false)
      // 重置文件输入
      event.target.value = ""
    }
  }

  const handleCreate = async () => {
    if (!formData.account_id || !formData.session_file || !formData.script_id) {
      showErrorDialog("错误", "請填寫所有必填字段")
      return
    }

    try {
      setCreating(true)
      const request: AccountCreateRequest = {
        account_id: formData.account_id,
        session_file: formData.session_file, // 使用文件名，後端會自动解析路徑
        script_id: formData.script_id,
      }
      await createAccount(request)
      showSuccessDialog("成功", `账号 ${formData.account_id} 创建成功`)
      setDialogOpen(false)
      setFormData({ account_id: "", session_file: "", script_id: "", role_id: "" })
      // 刷新账号列表和服务器状态（確保服务器账号數更新）
      await Promise.all([fetchAccounts(), fetchServers()])
    } catch (err) {
      showErrorDialog("创建失败", err instanceof Error ? err.message : "创建账号失败")
    } finally {
      setCreating(false)
    }
  }

  // 批量创建账号
  const handleBatchCreate = async () => {
    if (selectedSessions.size === 0) {
      showErrorDialog("错误", "請至少选择一个 Session 文件")
      return
    }

    if (!formData.script_id) {
      showErrorDialog("错误", "請选择剧本")
      return
    }

    // 嚴格按照選中的文件列表创建，確保沒有遺漏或多餘
    const selectedFilenames = Array.from(selectedSessions)
    const sessions = selectedFilenames.map(filename => 
      availableSessions.find(s => s.filename === filename)
    ).filter(Boolean) as SessionFile[]

    if (sessions.length === 0) {
      showErrorDialog("错误", "未找到選中的 Session 文件")
      return
    }

    // 嚴格验证：選中的文件數量必須等於找到的文件數量
    if (sessions.length !== selectedSessions.size) {
      const missing = selectedFilenames.filter(f => !sessions.find(s => s.filename === f))
      console.error(`嚴重错误：選中的文件數量 (${selectedSessions.size}) 與找到的文件數量 (${sessions.length}) 不匹配`)
      console.error(`缺失的文件:`, missing)
      showErrorDialog(
        "选择错误", 
        `選中的 ${selectedSessions.size} 个文件中，只找到 ${sessions.length} 个有效文件。缺失：${missing.join(", ")}`
      )
      return
    }

    // 确认提示：顯示將要创建的账号列表
    const accountIds = sessions.map(s => extractAccountIdFromSessionFile(s.filename))
    const scriptName = scripts.find(s => s.script_id === formData.script_id)?.name || formData.script_id
    
    // 使用 Promise 來处理确认对话框
    const confirmed = await new Promise<boolean>((resolve) => {
      // 设置确认对话框内容
      setBatchConfirmDialogTitle("确认批量创建账号")
      setBatchConfirmDialogMessage(`确定要创建以下 ${sessions.length} 个账号嗎？`)
      setBatchConfirmDialogAccountIds(accountIds)
      setBatchConfirmDialogScriptName(scriptName)
      setBatchConfirmDialogResolve(() => resolve)
      setBatchConfirmDialogOpen(true)
    })

    if (!confirmed) {
      return
    }

    try {
      setBatchCreating(true)
      setBatchCreateProgress({
        current: 0,
        total: sessions.length,
        currentAccountId: "",
      })
      const results: { success: string[], failed: { filename: string, error: string }[] } = {
        success: [],
        failed: []
      }

      // 逐个创建账号（严格按照选中的文件列表）
      console.log(`[批量创建] 开始批量创建 ${sessions.length} 个账号`)
      console.log(`[批量创建] 選中的文件列表:`, sessions.map(s => s.filename))
      console.log(`[批量创建] 將创建的账号 ID:`, accountIds)
      
      for (let i = 0; i < sessions.length; i++) {
        const session = sessions[i]
        try {
          const accountId = extractAccountIdFromSessionFile(session.filename)
          
          // 更新進度
          setBatchCreateProgress({
            current: i,
            total: sessions.length,
            currentAccountId: accountId,
          })
          
          console.log(`[批量创建] (${i+1}/${sessions.length}) 正在创建账号: ${accountId}`)
          
          // 使用完整路径（如果可用），否则使用文件名（后端会尝试解析）
          const session_file = session.path || session.filename
          const request: AccountCreateRequest = {
            account_id: accountId,
            session_file: session_file,
            script_id: formData.script_id,
          }
          await createAccount(request)
          results.success.push(accountId)
          
          // 更新進度（成功）
          setBatchCreateProgress({
            current: i + 1,
            total: sessions.length,
            currentAccountId: accountId,
          })
          
          console.log(`[批量创建] (${i+1}/${sessions.length}) 账号 ${accountId} 创建成功`)
          
          // 每个账号创建成功后立即显示提示，等待用户确认后再继续
          await new Promise<void>((resolve) => {
            showSuccessDialog(
              "账号创建成功",
              `账号 ${accountId} 创建成功！\n\n進度：${i + 1}/${sessions.length}\n\n点击确认继续创建下一个账号。`,
              () => {
                resolve()
              }
            )
          })
        } catch (err) {
          console.error(`[批量创建] (${i+1}/${sessions.length}) 账号 ${extractAccountIdFromSessionFile(session.filename)} 创建失败:`, err)
          results.failed.push({
            filename: session.filename,
            error: err instanceof Error ? err.message : "未知错误"
          })
          
          // 更新進度（失败）
          setBatchCreateProgress({
            current: i + 1,
            total: sessions.length,
            currentAccountId: extractAccountIdFromSessionFile(session.filename),
          })
        }
      }
      
      console.log(`[批量创建] 批量创建完成: 成功 ${results.success.length}, 失败 ${results.failed.length}`)

      // 显示结果
      if (results.failed.length === 0) {
        showSuccessDialog(
          "批量创建成功", 
          `成功创建 ${results.success.length} 个账号：\n${results.success.join(", ")}`
        )
      } else {
        const successMsg = results.success.length > 0 
          ? `成功：${results.success.length} 个\n${results.success.join(", ")}\n\n`
          : ""
        const failedMsg = `失败：${results.failed.length} 个\n${results.failed.map(f => `${f.filename}: ${f.error}`).join("\n")}`
        showErrorDialog("批量创建部分失败", successMsg + failedMsg)
      }

      setBatchSelectDialogOpen(false)
      setSelectedSessions(new Set())
      setBatchCreateProgress({
        current: 0,
        total: 0,
        currentAccountId: "",
      })
      // 刷新账号列表和服务器状态（確保服务器账号數更新）
      await Promise.all([fetchAccounts(), fetchServers()])
    } catch (err) {
      showErrorDialog("批量创建失败", err instanceof Error ? err.message : "批量创建账号失败")
    } finally {
      setBatchCreating(false)
      setBatchCreateProgress({
        current: 0,
        total: 0,
        currentAccountId: "",
      })
    }
  }

  // 批量操作处理函數
  const toggleAccountSelect = (accountId: string) => {
    const newSelected = new Set(selectedAccounts)
    if (newSelected.has(accountId)) {
      newSelected.delete(accountId)
    } else {
      newSelected.add(accountId)
    }
    setSelectedAccounts(newSelected)
  }

  const toggleSelectAllAccounts = () => {
    if (selectedAccounts.size === accounts.length) {
      setSelectedAccounts(new Set())
    } else {
      setSelectedAccounts(new Set(accounts.map(a => a.account_id)))
    }
  }

  const openBatchOperationDialog = (operation: "update" | "start" | "stop" | "delete") => {
    if (selectedAccounts.size === 0) {
      showErrorDialog("错误", "請至少选择一个账号")
      return
    }
    setBatchOperation(operation)
    setBatchUpdateForm({ script_id: "", server_id: "", active: undefined })
    setBatchOperationDialogOpen(true)
  }

  const handleBatchOperation = async () => {
    if (selectedAccounts.size === 0) return

    try {
      setBatchOperating(true)
      const accountIds = Array.from(selectedAccounts)
      const results: { success: string[], failed: { accountId: string, error: string }[] } = {
        success: [],
        failed: []
      }

      switch (batchOperation) {
        case "update":
          // 批量更新配置
          for (const accountId of accountIds) {
            try {
              const updateData: any = {}
              if (batchUpdateForm.script_id) updateData.script_id = batchUpdateForm.script_id
              if (batchUpdateForm.server_id) updateData.server_id = batchUpdateForm.server_id === "unassigned" ? undefined : batchUpdateForm.server_id
              if (batchUpdateForm.active !== undefined) updateData.active = batchUpdateForm.active
              
              if (Object.keys(updateData).length > 0) {
                await updateAccount(accountId, updateData)
                results.success.push(accountId)
              } else {
                results.failed.push({ accountId, error: "未选择任何更新項" })
              }
            } catch (err) {
              results.failed.push({
                accountId,
                error: err instanceof Error ? err.message : "未知错误"
              })
            }
          }
          break

        case "start":
          // 批量启动
          for (const accountId of accountIds) {
            try {
              await startAccount(accountId)
              results.success.push(accountId)
            } catch (err) {
              results.failed.push({
                accountId,
                error: err instanceof Error ? err.message : "未知错误"
              })
            }
          }
          break

        case "stop":
          // 批量停止
          for (const accountId of accountIds) {
            try {
              await stopAccount(accountId)
              results.success.push(accountId)
            } catch (err) {
              results.failed.push({
                accountId,
                error: err instanceof Error ? err.message : "未知错误"
              })
            }
          }
          break

        case "delete":
          // 批量删除
          for (const accountId of accountIds) {
            try {
              await deleteAccount(accountId)
              results.success.push(accountId)
            } catch (err) {
              results.failed.push({
                accountId,
                error: err instanceof Error ? err.message : "未知错误"
              })
            }
          }
          break
      }

      // 顯示結果
      if (results.failed.length === 0) {
        const actionText = {
          update: "批量更新",
          start: "批量启动",
          stop: "批量停止",
          delete: "批量删除"
        }[batchOperation]
        showSuccessDialog(
          `${actionText}成功`,
          `成功${actionText} ${results.success.length} 个账号`
        )
      } else {
        const actionText = {
          update: "批量更新",
          start: "批量启动",
          stop: "批量停止",
          delete: "批量删除"
        }[batchOperation]
        const successMsg = results.success.length > 0
          ? `成功：${results.success.length} 个\n${results.success.join(", ")}\n\n`
          : ""
        const failedMsg = `失败：${results.failed.length} 个\n${results.failed.map(f => `${f.accountId}: ${f.error}`).join("\n")}`
        showErrorDialog(`${actionText}部分失败`, successMsg + failedMsg)
      }

      setBatchOperationDialogOpen(false)
      setSelectedAccounts(new Set())
      await fetchAccounts()
    } catch (err) {
      const actionText = {
        update: "批量更新",
        start: "批量启动",
        stop: "批量停止",
        delete: "批量删除"
      }[batchOperation]
      showErrorDialog(`${actionText}失败`, err instanceof Error ? err.message : `${actionText}账号失败`)
    } finally {
      setBatchOperating(false)
    }
  }

  // 切换Session选择状态
  const toggleSessionSelect = (filename: string) => {
    const newSelected = new Set(selectedSessions)
    if (newSelected.has(filename)) {
      newSelected.delete(filename)
    } else {
      newSelected.add(filename)
    }
    setSelectedSessions(newSelected)
  }

  // 全选/取消全选
  const toggleSelectAll = () => {
    if (selectedSessions.size === availableSessions.length) {
      setSelectedSessions(new Set())
    } else {
      setSelectedSessions(new Set(availableSessions.map(s => s.filename)))
    }
  }

  const handleDelete = async (accountId: string) => {
    showWarningDialog(
      "确认删除",
      `确定要删除账号 ${accountId} 嗎？此操作无法撤銷。`,
      async () => {
        try {
          await deleteAccount(accountId)
          showSuccessDialog("成功", `账号 ${accountId} 已删除`)
          await fetchAccounts()
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : "删除账号失败"
          // 如果账号不存在，也刷新列表（可能是前端数据不同步）
          if (errorMessage.includes("不存在")) {
            showWarningDialog("账号不存在", `账号 ${accountId} 不存在，已從列表中移除。`)
            await fetchAccounts() // 刷新列表以同步数据
          } else {
            showErrorDialog("删除失败", errorMessage)
          }
        }
      }
    )
  }

  const handleCreateGroup = async (accountId: string) => {
    setCreateGroupAccountId(accountId)
    setCreateGroupForm({ title: "", description: "", auto_reply: true })
    setCreateGroupDialogOpen(true)
  }

  const handleSubmitCreateGroup = async () => {
    if (!createGroupForm.title.trim()) {
      showErrorDialog("错误", "请输入群组標題")
      return
    }

    try {
      const result = await createGroup({
        account_id: createGroupAccountId,
        title: createGroupForm.title,
        description: createGroupForm.description || undefined,
        auto_reply: createGroupForm.auto_reply
      })
      showSuccessDialog("成功", `群组 "${result.group_title || createGroupForm.title}" 创建成功並已启动群聊`)
      setCreateGroupDialogOpen(false)
      await fetchAccounts()
    } catch (err) {
      showErrorDialog("创建失败", err instanceof Error ? err.message : "创建群组失败")
    }
  }

  const handleStartGroupChat = async (accountId: string, groupId: number) => {
    try {
      const result = await startGroupChat({
        account_id: accountId,
        group_id: groupId,
        auto_reply: true
      })
      showSuccessDialog("成功", `群组聊天已启动`)
      await fetchAccounts()
    } catch (err) {
      showErrorDialog("启动失败", err instanceof Error ? err.message : "启动群组聊天失败")
    }
  }

  const handleEdit = async (account: Account) => {
    setEditingAccount(account)
    setEditingForm({
      display_name: account.display_name || account.first_name || account.username || account.account_id,
      bio: account.bio || "",
      script_id: account.script_id,
      server_id: account.server_id === "unassigned" || !account.server_id ? "" : account.server_id,
    })
    // 如果账号已有剧本，加载角色列表
    if (account.script_id) {
      // 如果已缓存，直接使用
      if (allRoles[account.script_id]) {
        setSelectedScriptRoles(allRoles[account.script_id])
      } else {
        try {
          const rolesData = await extractRoles(account.script_id)
          const roles = rolesData.roles || []
          setSelectedScriptRoles(roles)
          // 缓存角色列表
          setAllRoles({ ...allRoles, [account.script_id]: roles })
        } catch (err) {
          console.warn("提取剧本角色失败:", err)
          setSelectedScriptRoles([])
        }
      }
    } else {
      setSelectedScriptRoles([])
    }
    setEditDialogOpen(true)
  }

  const handleUpdate = async () => {
    if (!editingAccount) return

    try {
      setUpdating(true)
        await updateAccount(editingAccount.account_id, {
        display_name: editingForm.display_name || undefined,
        bio: editingForm.bio || undefined,
        script_id: editingForm.script_id || undefined,
        server_id: editingForm.server_id === "unassigned" || !editingForm.server_id ? undefined : editingForm.server_id,
      })
      showSuccessDialog("成功", `账号 ${editingAccount.account_id} 已更新`)
      setEditDialogOpen(false)
      await fetchAccounts()
    } catch (err) {
      showErrorDialog("更新失败", err instanceof Error ? err.message : "更新账号失败")
    } finally {
      setUpdating(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      online: "default",
      offline: "secondary",
      error: "destructive",
      starting: "outline",
      stopping: "outline",
    }
    return (
      <Badge variant={variants[status] || "secondary"}>
        {status}
      </Badge>
    )
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <StepIndicator currentStep={2} steps={workflowSteps} />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">群组 AI 账号管理</h1>
          <p className="text-muted-foreground mt-2">管理 Telegram 群组 AI 账号</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => fetchAccounts()} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
          <Button onClick={fetchSessions} variant="outline" size="sm" disabled={scanning}>
            <Scan className="h-4 w-4 mr-2" />
            {scanning ? "扫描中..." : "扫描 Session"}
          </Button>
          <Dialog 
            open={dialogOpen} 
            onOpenChange={(open) => {
              setDialogOpen(open)
              if (!open) {
                // 关闭時重置表單和模式
                setFormData({ account_id: "", session_file: "", script_id: "", role_id: "" })
                setAssignScriptMode(false)
                setSelectedAccountForRole(null)
                setSelectedScriptRoles([])
              }
            }}
          >
            <PermissionGuard permission="account:create">
              <div className="flex gap-2">
                <Button onClick={() => setDialogOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  添加账号
                </Button>
                <input
                  type="file"
                  id="telegram-import"
                  accept=".txt,.csv,.xlsx,.xls"
                  onChange={handleImportTelegramAccounts}
                  className="hidden"
                />
                <label htmlFor="telegram-import">
                  <Button
                    type="button"
                    variant="outline"
                    asChild
                  >
                    <span>
                      <Upload className="h-4 w-4 mr-2" />
                      批量導入配置
                    </span>
                  </Button>
                </label>
              </div>
            </PermissionGuard>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>{assignScriptMode ? "分配剧本" : "添加新账号"}</DialogTitle>
                <DialogDescription>
                  {assignScriptMode 
                    ? `为账号 ${selectedAccountForRole?.display_name || selectedAccountForRole?.account_id || ""} 分配剧本`
                    : "配置新的 Telegram AI 账号"}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                {/* 分配剧本模式：显示账号信息（只读） */}
                {assignScriptMode && selectedAccountForRole && (
                  <div className="space-y-2 p-4 bg-muted rounded-md">
                    <Label className="text-sm font-medium">账号信息</Label>
                    <div className="space-y-1 text-sm">
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">账号ID:</span>
                        <span className="font-medium">{selectedAccountForRole.account_id}</span>
                      </div>
                      {selectedAccountForRole.display_name && (
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground">名称:</span>
                          <span className="font-medium">{selectedAccountForRole.display_name}</span>
                        </div>
                      )}
                      {selectedAccountForRole.phone_number && (
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground">手机号:</span>
                          <span className="font-medium">{selectedAccountForRole.phone_number}</span>
                        </div>
                      )}
                      {selectedAccountForRole.node_id && (
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground">节点:</span>
                          <Badge variant="outline">{selectedAccountForRole.node_id}</Badge>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {/* 添加新账号模式：显示账号ID和Session文件字段 */}
                {!assignScriptMode && (
                  <>
                    <div className="space-y-2">
                      <Label>账号 ID *</Label>
                      <Input 
                        placeholder="將從 Session 文件自动提取，或手动输入自定義 ID" 
                        value={formData.account_id}
                        onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
                      />
                      {formData.session_file && (
                        <p className="text-xs text-muted-foreground">
                          💡 已從 Session 文件自动提取，可手动修改為自定義 ID
                        </p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>Session 文件 *</Label>
                        <div className="flex gap-2">
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setBatchSelectDialogOpen(true)
                              // 如果已有选中的Session，将其添加到批量选择中
                              if (formData.session_file) {
                                setSelectedSessions(new Set([formData.session_file]))
                              }
                            }}
                          >
                            <CheckSquare className="h-4 w-4 mr-2" />
                            选择 Session
                          </Button>
                          <input
                            type="file"
                            id="session-upload"
                            accept=".session"
                            onChange={handleUploadSession}
                            className="hidden"
                          />
                          <label htmlFor="session-upload">
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              disabled={uploading}
                              asChild
                            >
                              <span>
                                <Upload className="h-4 w-4 mr-2" />
                                {uploading ? "上傳中..." : "上傳 Session"}
                              </span>
                            </Button>
                          </label>
                        </div>
                      </div>
                      <Select
                        value={formData.session_file}
                        onValueChange={(value) => {
                          // 当选择Session文件时，自动提取账号ID（去掉.session扩展名）
                          const accountId = extractAccountIdFromSessionFile(value)
                          setFormData({ 
                            ...formData, 
                            session_file: value,
                            account_id: accountId || formData.account_id
                          })
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="选择或输入 session 文件名" />
                        </SelectTrigger>
                        <SelectContent>
                          {availableSessions.length === 0 ? (
                            <div className="px-2 py-1.5 text-sm text-muted-foreground">
                              暫无可用 session 文件，請点击「扫描 Session」或「上傳 Session」
                            </div>
                          ) : (
                            availableSessions.map((session) => (
                              <SelectItem key={session.filename} value={session.filename}>
                                {session.filename}
                              </SelectItem>
                            ))
                          )}
                        </SelectContent>
                      </Select>
                      {availableSessions.length > 0 && (
                        <p className="text-sm text-muted-foreground">
                          已掃描到 {availableSessions.length} 个 session 文件，点击「选择 Session」可批量选择並创建
                        </p>
                      )}
                      {formData.session_file && !availableSessions.find(s => s.filename === formData.session_file) && (
                        <Input
                          placeholder="或手动输入文件名（如：account.session）"
                          value={formData.session_file}
                          onChange={(e) => {
                            const value = e.target.value
                            const accountId = extractAccountIdFromSessionFile(value)
                            setFormData({ 
                              ...formData, 
                              session_file: value,
                              account_id: accountId || formData.account_id
                            })
                          }}
                          className="mt-2"
                        />
                      )}
                    </div>
                  </>
                )}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>剧本 ID *</Label>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => router.push("/group-ai/scripts")}
                      className="h-auto p-1 text-xs"
                    >
                      管理剧本
                      <ArrowRight className="h-3 w-3 ml-1" />
                    </Button>
                  </div>
                  <Select
                    value={formData.script_id}
                    onValueChange={handleScriptSelect}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择剧本或输入剧本 ID" />
                    </SelectTrigger>
                    <SelectContent>
                      {scripts.length === 0 ? (
                        <div className="px-2 py-1.5 text-sm text-muted-foreground">
                          暫无可用剧本，請先创建剧本
                        </div>
                      ) : (
                        scripts.map((script) => (
                          <SelectItem key={script.script_id} value={script.script_id}>
                            {script.name || script.script_id} {script.version && `(v${script.version})`}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                  {formData.script_id && selectedScriptRoles.length > 0 && (
                    <div className="mt-2 p-3 bg-muted rounded-md space-y-2">
                      <p className="text-xs text-muted-foreground mb-2">剧本包含 {selectedScriptRoles.length} 个角色（可选）：</p>
                      <div className="grid grid-cols-2 gap-2">
                        {selectedScriptRoles.map(role => {
                          const roleAssigned = isRoleAssigned(role.role_id, assignScriptMode ? selectedAccountForRole?.account_id : formData.account_id)
                          const assignedAccountName = getAccountNameByRole(role.role_id, assignScriptMode ? selectedAccountForRole?.account_id : formData.account_id)
                          const isSelected = formData.role_id === role.role_id
                          
                          return (
                            <button
                              key={role.role_id}
                              type="button"
                              onClick={() => {
                                if (roleAssigned.assigned && !isSelected) {
                                  // 如果角色已被使用，询问是否要替换
                                  showWarningDialog(
                                    "角色已被使用",
                                    `角色"${role.role_name}"已被账号"${assignedAccountName}"使用。是否要替换为该账号？`,
                                    () => {
                                      setFormData({ ...formData, role_id: role.role_id })
                                    }
                                  )
                                } else {
                                  setFormData({ ...formData, role_id: isSelected ? "" : role.role_id })
                                }
                              }}
                              className={`
                                p-2 rounded-md border text-left transition-colors
                                ${isSelected 
                                  ? "bg-primary text-primary-foreground border-primary" 
                                  : roleAssigned.assigned
                                  ? "bg-yellow-500/10 border-yellow-500/50 hover:bg-yellow-500/20"
                                  : "bg-background border-border hover:bg-muted"
                                }
                              `}
                            >
                              <div className="flex items-center justify-between">
                                <span className="text-sm font-medium">{role.role_name}</span>
                                {isSelected && (
                                  <CheckSquare className="h-4 w-4" />
                                )}
                              </div>
                              {roleAssigned.assigned && !isSelected && (
                                <p className="text-xs mt-1 opacity-75">
                                  已分配给: {assignedAccountName}
                                </p>
                              )}
                            </button>
                          )
                        })}
                      </div>
                      {formData.role_id && (
                        <p className="text-xs text-muted-foreground mt-2">
                          ✓ 已选择角色: {selectedScriptRoles.find(r => r.role_id === formData.role_id)?.role_name}
                        </p>
                      )}
                    </div>
                  )}
                  {formData.script_id && !scripts.find(s => s.script_id === formData.script_id) && (
                    <Input 
                      placeholder="或手动输入剧本 ID（如：default）" 
                      value={formData.script_id}
                      onChange={(e) => setFormData({ ...formData, script_id: e.target.value })}
                      className="mt-2"
                    />
                  )}
                </div>
                {assignScriptMode ? (
                  <div className="flex gap-2">
                    <Button 
                      className="flex-1" 
                      variant="outline"
                      onClick={() => {
                        setDialogOpen(false)
                        setAssignScriptMode(false)
                        setSelectedAccountForRole(null)
                      }}
                    >
                      取消
                    </Button>
                    <Button 
                      className="flex-1" 
                      onClick={async () => {
                        if (!selectedAccountForRole || !formData.script_id) {
                          showErrorDialog("错误", "请选择剧本")
                          return
                        }
                        try {
                          setCreating(true)
                          // 更新账号的剧本ID
                          // 确保传递 server_id（优先使用 server_id，如果没有则使用 node_id）
                          // 尝试多种方式获取 server_id
                          const serverId = selectedAccountForRole.server_id 
                            || (selectedAccountForRole as any).node_id 
                            || (selectedAccountForRole as any).server_id
                            || undefined
                          
                          console.log(`[分配剧本] 账号详情:`, {
                            account_id: selectedAccountForRole.account_id,
                            server_id: selectedAccountForRole.server_id,
                            node_id: (selectedAccountForRole as any).node_id,
                            all_fields: Object.keys(selectedAccountForRole),
                            最终serverId: serverId
                          })
                          
                          // 如果没有 server_id，提示用户
                          if (!serverId) {
                            throw new Error(`无法获取账号的节点ID。账号信息: ${JSON.stringify({
                              account_id: selectedAccountForRole.account_id,
                              has_server_id: !!selectedAccountForRole.server_id,
                              has_node_id: !!(selectedAccountForRole as any).node_id,
                            })}`)
                          }
                          
                          await updateAccount(selectedAccountForRole.account_id, {
                            script_id: formData.script_id,
                            session_file: selectedAccountForRole.session_file || undefined,  // 如果是空字符串，传递 undefined
                            server_id: serverId,  // 传递 server_id 或 node_id 以便从远程服务器创建记录
                          })
                          
                          // 如果选择了角色，同时分配角色
                          if (formData.role_id) {
                            try {
                              await createAssignment({
                                script_id: formData.script_id,
                                account_ids: [selectedAccountForRole.account_id],
                                mode: "manual",
                                manual_assignments: {
                                  [selectedAccountForRole.account_id]: formData.role_id
                                }
                              })
                              // 更新本地角色分配映射
                              setAccountRoleAssignments({
                                ...accountRoleAssignments,
                                [selectedAccountForRole.account_id]: formData.role_id
                              })
                            } catch (roleErr) {
                              console.warn("分配角色失败:", roleErr)
                              // 角色分配失败不影响剧本分配
                            }
                          }
                          
                          showSuccessDialog(
                            "成功", 
                            `账号 ${selectedAccountForRole.account_id} 已分配剧本${formData.role_id ? "和角色" : ""}`
                          )
                          setDialogOpen(false)
                          setAssignScriptMode(false)
                          setSelectedAccountForRole(null)
                          setFormData({ account_id: "", session_file: "", script_id: "", role_id: "" })
                          await fetchAccounts()
                        } catch (err) {
                          showErrorDialog("分配失败", err instanceof Error ? err.message : "分配剧本失败")
                        } finally {
                          setCreating(false)
                        }
                      }}
                      disabled={creating || !formData.script_id}
                    >
                      {creating ? "分配中..." : "分配剧本"}
                    </Button>
                  </div>
                ) : (
                  <Button 
                    className="w-full" 
                    onClick={handleCreate}
                    disabled={creating || uploading}
                  >
                    {creating ? "创建中..." : "创建"}
                  </Button>
                )}
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive p-4 rounded-md">
          {error}
        </div>
      )}

      {/* 已掃描的 Session 文件列表 */}
      {availableSessions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>可用的 Session 文件</span>
              <Badge variant="secondary">{availableSessions.length} 个文件</Badge>
            </CardTitle>
            <CardDescription>
              已掃描到的 Session 文件，可用於创建新账号。点击文件卡片可直接使用該文件创建账号，或点击「添加账号」按鈕。支持多選进行批量创建。
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {availableSessions.map((session) => {
                const isSelected = selectedSessions.has(session.filename)
                return (
                  <div
                    key={session.filename}
                    className={`flex items-center gap-3 p-3 border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer ${
                      isSelected ? "bg-accent border-primary" : ""
                    }`}
                    onClick={(e) => {
                      // 如果按住Ctrl或Cmd键，进行多选
                      if (e.ctrlKey || e.metaKey) {
                        e.stopPropagation()
                        toggleSessionSelect(session.filename)
                      } else {
                        // 普通点击：打开创建账号对话框并自动选择该文件
                        const accountId = extractAccountIdFromSessionFile(session.filename)
                        setFormData({ 
                          account_id: accountId, 
                          session_file: session.filename,
                          script_id: formData.script_id 
                        })
                        setDialogOpen(true)
                      }
                    }}
                    title={`点击使用 ${session.filename} 创建账号，按住 Ctrl/Cmd 鍵可多選进行批量创建`}
                  >
                    <div 
                      className="flex-shrink-0 cursor-pointer"
                      onClick={(e) => {
                        e.stopPropagation()
                        toggleSessionSelect(session.filename)
                      }}
                    >
                      {isSelected ? (
                        <CheckSquare className="h-5 w-5 text-primary" />
                      ) : (
                        <SquareIcon className="h-5 w-5 text-muted-foreground" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{session.filename}</p>
                      <p className="text-xs text-muted-foreground">
                        {(session.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
            {selectedSessions.size > 0 && (
              <div className="mt-4 p-4 bg-muted rounded-lg flex items-center justify-between">
                <div className="text-sm">
                  已选择 <strong>{selectedSessions.size}</strong> 个 Session 文件
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedSessions(new Set())
                    }}
                  >
                    清除选择
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => {
                      setBatchSelectDialogOpen(true)
                    }}
                  >
                    批量创建账号
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 搜索和過濾 */}
      <div className="flex gap-4 mb-4 flex-wrap">
        <div className="flex-1 relative min-w-[200px]">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索账号ID、名稱、用户名或手机号..."
            value={searchFilters.search || ""}
            onChange={(e) => {
              const newFilters = { ...searchFilters, search: e.target.value }
              setSearchFilters(newFilters)
              if (!e.target.value) {
                fetchAccounts({ ...newFilters, search: undefined })
              }
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                fetchAccounts()
              }
            }}
            className="pl-10"
          />
        </div>
        <Select
          value={searchFilters.status_filter || "__all__"}
          onValueChange={(value) => {
            const newFilters = { ...searchFilters, status_filter: value === "__all__" ? undefined : value }
            setSearchFilters(newFilters)
            fetchAccounts(newFilters)
          }}
        >
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="全部状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">全部状态</SelectItem>
            <SelectItem value="online">在線</SelectItem>
            <SelectItem value="offline">离线</SelectItem>
            <SelectItem value="error">错误</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={searchFilters.script_id || "__all__"}
          onValueChange={(value) => {
            const newFilters = { ...searchFilters, script_id: value === "__all__" ? undefined : value }
            setSearchFilters(newFilters)
            fetchAccounts(newFilters)
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
          value={searchFilters.server_id || "__all__"}
          onValueChange={(value) => {
            const newFilters = { ...searchFilters, server_id: value === "__all__" ? undefined : value }
            setSearchFilters(newFilters)
            fetchAccounts(newFilters)
          }}
        >
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="全部服务器" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">全部服务器</SelectItem>
            {servers.map((server) => (
              <SelectItem key={server.node_id} value={server.node_id}>
                {server.node_id}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {(searchFilters.search || searchFilters.status_filter || searchFilters.script_id || searchFilters.server_id) && (
          <Button
            variant="outline"
            onClick={() => {
              setSearchFilters({})
              fetchAccounts({})
            }}
          >
            <X className="h-4 w-4 mr-2" />
            清除
          </Button>
        )}
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>账号列表</CardTitle>
              <CardDescription>
                共 {accounts.length + workerAccounts.length} 个账号
                {workerAccounts.length > 0 && `（${accounts.length} 个数据库账号，${workerAccounts.length} 个Worker节点账号）`}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <PermissionGuard permission="export:account">
                    <Button variant="outline" size="sm" disabled={loading || accounts.length === 0}>
                      <Download className="mr-2 h-4 w-4" />
                      导出
                    </Button>
                  </PermissionGuard>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuLabel>选择导出格式</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={async () => {
                      try {
                        const blob = await exportAccounts("csv")
                        const filename = `账号列表_${new Date().toISOString().slice(0, 10)}.csv`
                        downloadBlob(blob, filename)
                        showSuccessDialog("导出成功", "账号列表已导出為 CSV")
                      } catch (err) {
                        showErrorDialog("导出失败", err instanceof Error ? err.message : "无法导出账号列表")
                      }
                    }}
                  >
                    CSV 格式
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={async () => {
                      try {
                        const blob = await exportAccounts("excel")
                        const filename = `账号列表_${new Date().toISOString().slice(0, 10)}.xlsx`
                        downloadBlob(blob, filename)
                        showSuccessDialog("导出成功", "账号列表已导出為 Excel")
                      } catch (err) {
                        showErrorDialog("导出失败", err instanceof Error ? err.message : "无法导出账号列表")
                      }
                    }}
                  >
                    Excel 格式
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={async () => {
                      try {
                        const blob = await exportAccounts("pdf")
                        const filename = `账号列表_${new Date().toISOString().slice(0, 10)}.pdf`
                        downloadBlob(blob, filename)
                        showSuccessDialog("导出成功", "账号列表已导出為 PDF")
                      } catch (err) {
                        showErrorDialog("导出失败", err instanceof Error ? err.message : "无法导出账号列表")
                      }
                    }}
                  >
                    PDF 格式
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              {selectedAccounts.size > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">
                    已选择 {selectedAccounts.size} 个账号
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => openBatchOperationDialog("update")}
                  >
                    <Settings className="h-4 w-4 mr-1" />
                    批量更新
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => openBatchOperationDialog("start")}
                  >
                    <Play className="h-4 w-4 mr-1" />
                    批量启动
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => openBatchOperationDialog("stop")}
                  >
                    <Square className="h-4 w-4 mr-1" />
                    批量停止
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => openBatchOperationDialog("delete")}
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    批量删除
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setSelectedAccounts(new Set())}
                  >
                    取消选择
                  </Button>
                </div>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : accounts.length === 0 && workerAccounts.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              暫无账号，点击「添加账号」创建第一个账号
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selectedAccounts.size === accounts.length && accounts.length > 0}
                        onChange={toggleSelectAllAccounts}
                        className="h-4 w-4 rounded border-gray-300"
                      />
                    </div>
                  </TableHead>
                  <TableHead>账号数据</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>剧本</TableHead>
                  <TableHead>服务器</TableHead>
                  <TableHead>群组數</TableHead>
                  <TableHead>消息数</TableHead>
                  <TableHead>回复數</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {/* 显示数据库账号 */}
                {accounts.map((account) => (
                  <TableRow key={account.account_id}>
                    <TableCell>
                      <input
                        type="checkbox"
                        checked={selectedAccounts.has(account.account_id)}
                        onChange={() => toggleAccountSelect(account.account_id)}
                        className="h-4 w-4 rounded border-gray-300"
                      />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        {account.avatar_url ? (
                          <div className="relative h-10 w-10 rounded-full overflow-hidden bg-muted">
                            <Image
                              src={account.avatar_url}
                              alt={account.display_name || account.account_id}
                              fill
                              className="object-cover"
                              onError={(e) => {
                                // 如果圖片加载失败，顯示默認頭像
                                e.currentTarget.style.display = "none"
                              }}
                            />
                          </div>
                        ) : (
                          <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
                            <User className="h-5 w-5 text-muted-foreground" />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="font-medium truncate">
                            {account.display_name || account.first_name || account.username || account.account_id}
                          </div>
                          <div className="text-sm text-muted-foreground truncate">
                            {account.username && `@${account.username}`}
                            {account.username && account.phone_number && " • "}
                            {account.phone_number}
                          </div>
                          <div className="text-xs text-muted-foreground truncate">
                            {account.account_id}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(account.status)}</TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        <span>{account.script_id || <span className="text-muted-foreground">未分配</span>}</span>
                        {(() => {
                          const roleName = getAccountRoleName(account)
                          return roleName && (
                            <Badge variant="secondary" className="text-xs w-fit">
                              {roleName}
                            </Badge>
                          )
                        })()}
                        {!account.script_id && (
                          <Button
                            size="sm"
                            variant="outline"
                            className="w-fit text-xs mt-1"
                            onClick={() => {
                              setSelectedAccountForRole(account)
                              setAssignScriptMode(true)
                              setDialogOpen(true)
                              setFormData({
                                account_id: account.account_id,
                                session_file: account.session_file || "",
                                script_id: account.script_id || ""
                              })
                            }}
                          >
                            分配剧本
                          </Button>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">
                      {account.server_id ? (
                        <Badge variant="outline">{account.server_id}</Badge>
                      ) : (
                        <span className="text-muted-foreground">未分配</span>
                      )}
                    </TableCell>
                    <TableCell>{account.group_count}</TableCell>
                    <TableCell>{account.message_count}</TableCell>
                    <TableCell>{account.reply_count}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        {account.status === "offline" ? (
                          <PermissionGuard permission="account:start">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleStart(account.account_id)}
                              title="启动"
                            >
                              <Play className="h-4 w-4" />
                            </Button>
                          </PermissionGuard>
                        ) : (
                          <PermissionGuard permission="account:stop">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleStop(account.account_id)}
                              title="停止"
                            >
                              <Square className="h-4 w-4" />
                            </Button>
                          </PermissionGuard>
                        )}
                        <PermissionGuard permission="account:update">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleEdit(account)}
                            title="编辑数据"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                        </PermissionGuard>
                        <PermissionGuard permission="account:update">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => router.push(`/group-ai/accounts/${account.account_id}/params`)}
                            title="账号设置"
                          >
                            <Settings className="h-4 w-4" />
                          </Button>
                        </PermissionGuard>
                        <PermissionGuard permission="role_assignment:view">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleOpenRoleAssignment(account)}
                            title="角色分配"
                            disabled={!account.script_id}
                          >
                            <Users className="h-4 w-4" />
                          </Button>
                        </PermissionGuard>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleCreateGroup(account.account_id)}
                          title="创建群组"
                        >
                          <UserPlus className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            if (account.group_count > 0) {
                              showWarningDialog(
                                "启动群组聊天",
                                "請先创建群组或加入群组，然後使用群组ID启动聊天",
                                () => {}
                              )
                            } else {
                              showWarningDialog(
                                "提示",
                                "該账号尚未加入任何群组，請先创建或加入群组",
                                () => {}
                              )
                            }
                          }}
                          title="启动群组聊天"
                        >
                          <MessageSquare className="h-4 w-4" />
                        </Button>
                        <PermissionGuard permission="account:delete">
                          <Button 
                            size="sm" 
                            variant="destructive"
                            onClick={() => handleDelete(account.account_id)}
                            title="删除账号"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </PermissionGuard>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
                {/* 显示Worker节点账号（未在数据库中的） */}
                {workerAccounts.map((account) => (
                  <TableRow key={`worker-${account.account_id}-${account.node_id}`} className="bg-muted/30">
                    <TableCell>
                      <input
                        type="checkbox"
                        checked={selectedAccounts.has(account.account_id)}
                        onChange={() => toggleAccountSelect(account.account_id)}
                        className="h-4 w-4 rounded border-gray-300"
                      />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
                          <User className="h-5 w-5 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium truncate flex items-center gap-2">
                            {account.display_name || account.first_name || account.phone_number || account.account_id}
                            <Badge variant="outline" className="text-xs">Worker节点</Badge>
                          </div>
                          <div className="text-sm text-muted-foreground truncate">
                            {account.phone_number}
                          </div>
                          <div className="text-xs text-muted-foreground truncate">
                            {account.account_id} @ {account.node_id}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(account.status)}</TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        <span className="text-muted-foreground text-sm">未分配剧本</span>
                        <Button
                          size="sm"
                          variant="outline"
                          className="w-fit text-xs"
                          onClick={() => {
                            setSelectedAccountForRole(account)
                            setAssignScriptMode(true)
                            setDialogOpen(true)
                            setFormData({
                              account_id: account.account_id,
                              session_file: account.session_file || "",
                              script_id: account.script_id || "",
                              role_id: accountRoleAssignments[account.account_id] || ""
                            })
                            // 如果账号已有剧本，加载角色列表
                            if (account.script_id) {
                              handleScriptSelect(account.script_id)
                            }
                          }}
                        >
                          分配剧本
                        </Button>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">
                      <Badge variant="outline">{account.node_id}</Badge>
                    </TableCell>
                    <TableCell>0</TableCell>
                    <TableCell>0</TableCell>
                    <TableCell>0</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedAccountForRole(account)
                            setDialogOpen(true)
                            setFormData({
                              account_id: account.account_id,
                              session_file: "",
                              script_id: ""
                            })
                          }}
                          title="创建账号"
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* 居中错误对话框 */}
      <AlertDialog open={errorDialogOpen} onOpenChange={setErrorDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{errorDialogTitle}</AlertDialogTitle>
            <AlertDialogDescription className="whitespace-pre-wrap">
              {errorDialogMessage}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogAction onClick={() => setErrorDialogOpen(false)}>
              确认
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 居中警告对话框 */}
      <AlertDialog open={warningDialogOpen} onOpenChange={setWarningDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{warningDialogTitle}</AlertDialogTitle>
            <AlertDialogDescription className="whitespace-pre-wrap">
              {warningDialogMessage}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setWarningDialogOpen(false)}>
              取消
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (warningDialogOnConfirm) {
                  warningDialogOnConfirm()
                }
                setWarningDialogOpen(false)
              }}
            >
              确认
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 居中成功对话框 */}
      <AlertDialog open={successDialogOpen} onOpenChange={(open) => {
        setSuccessDialogOpen(open)
        if (!open && successDialogOnClose) {
          successDialogOnClose()
          setSuccessDialogOnClose(null)
        }
      }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{successDialogTitle}</AlertDialogTitle>
            <AlertDialogDescription className="whitespace-pre-wrap">
              {successDialogMessage}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogAction onClick={() => {
              setSuccessDialogOpen(false)
              if (successDialogOnClose) {
                successDialogOnClose()
                setSuccessDialogOnClose(null)
              }
            }}>
              确认
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 批量创建确认对话框 */}
      <AlertDialog open={batchConfirmDialogOpen} onOpenChange={(open) => {
        if (!open && batchConfirmDialogResolve) {
          // 用户关闭对话框（点击外部或ESC），视为取消
          batchConfirmDialogResolve(false)
          setBatchConfirmDialogResolve(null)
        }
        setBatchConfirmDialogOpen(open)
      }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{batchConfirmDialogTitle}</AlertDialogTitle>
            <AlertDialogDescription className="space-y-2">
              <p>{batchConfirmDialogMessage}</p>
              <div className="mt-3 space-y-1 max-h-48 overflow-y-auto">
                {batchConfirmDialogAccountIds.map((accountId) => (
                  <div key={accountId} className="text-sm font-mono text-muted-foreground">
                    • {accountId}
                  </div>
                ))}
              </div>
              <p className="mt-3 text-sm">
                剧本：<span className="font-medium">{batchConfirmDialogScriptName}</span>
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() => {
                if (batchConfirmDialogResolve) {
                  batchConfirmDialogResolve(false)
                  setBatchConfirmDialogResolve(null)
                }
                setBatchConfirmDialogOpen(false)
              }}
            >
              取消
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (batchConfirmDialogResolve) {
                  batchConfirmDialogResolve(true)
                  setBatchConfirmDialogResolve(null)
                }
                setBatchConfirmDialogOpen(false)
              }}
            >
              确定
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 编辑账号数据对话框 */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>编辑账号数据</DialogTitle>
            <DialogDescription>
              编辑账号 {editingAccount?.account_id} 的数据信息和配置
            </DialogDescription>
          </DialogHeader>
          {editingAccount && (
            <div className="space-y-4 py-4">
              <div className="flex items-center gap-4 pb-4 border-b">
                {editingAccount.avatar_url ? (
                  <div className="relative h-16 w-16 rounded-full overflow-hidden bg-muted">
                    <Image
                      src={editingAccount.avatar_url}
                      alt={editingAccount.display_name || editingAccount.account_id}
                      fill
                      className="object-cover"
                    />
                  </div>
                ) : (
                  <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center">
                    <User className="h-8 w-8 text-muted-foreground" />
                  </div>
                )}
                <div>
                  <div className="font-medium">
                    {editingAccount.first_name} {editingAccount.last_name}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {editingAccount.username && `@${editingAccount.username}`}
                    {editingAccount.phone_number && ` • ${editingAccount.phone_number}`}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    ID: {editingAccount.account_id}
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label>顯示名稱</Label>
                <Input
                  placeholder="自定義顯示名稱"
                  value={editingForm.display_name}
                  onChange={(e) => setEditingForm({ ...editingForm, display_name: e.target.value })}
                />
                <p className="text-xs text-muted-foreground">
                  用於在列表中顯示的名稱，可自定義
                </p>
              </div>

              <div className="space-y-2">
                <Label>个人簡介</Label>
                <Textarea
                  placeholder="输入个人簡介"
                  value={editingForm.bio}
                  onChange={(e) => setEditingForm({ ...editingForm, bio: e.target.value })}
                  rows={3}
                />
                <p className="text-xs text-muted-foreground">
                  账号的个人簡介信息
                </p>
              </div>

              <div className="space-y-2">
                <Label>剧本</Label>
                <Select
                  value={editingForm.script_id}
                  onValueChange={async (value) => {
                    setEditingForm({ ...editingForm, script_id: value })
                    // 加载角色列表
                    if (value) {
                      // 如果已缓存，直接使用
                      if (allRoles[value]) {
                        setSelectedScriptRoles(allRoles[value])
                      } else {
                        try {
                          const rolesData = await extractRoles(value)
                          const roles = rolesData.roles || []
                          setSelectedScriptRoles(roles)
                          // 缓存角色列表
                          setAllRoles({ ...allRoles, [value]: roles })
                        } catch (err) {
                          console.warn("提取剧本角色失败:", err)
                          setSelectedScriptRoles([])
                        }
                      }
                    } else {
                      setSelectedScriptRoles([])
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择剧本" />
                  </SelectTrigger>
                  <SelectContent>
                    {scripts.map((script) => (
                      <SelectItem key={script.script_id} value={script.script_id}>
                        {script.name || script.script_id}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  选择此账号使用的剧本
                </p>
                {editingForm.script_id && selectedScriptRoles.length > 0 && (
                  <div className="mt-2 p-2 bg-muted rounded-md">
                    <p className="text-xs text-muted-foreground mb-1">剧本包含 {selectedScriptRoles.length} 个角色：</p>
                    <div className="flex flex-wrap gap-1">
                      {selectedScriptRoles.map(role => (
                        <Badge key={role.role_id} variant="outline" className="text-xs">
                          {role.role_name}
                        </Badge>
                      ))}
                    </div>
                    {editingAccount && !accountRoleAssignments[editingAccount.account_id] && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="mt-2 w-full"
                        onClick={() => {
                          setEditDialogOpen(false)
                          handleOpenRoleAssignment(editingAccount)
                        }}
                      >
                        <Users className="h-3 w-3 mr-1" />
                        分配角色
                      </Button>
                    )}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <Label>服务器</Label>
                <Select
                  value={editingForm.server_id}
                  onValueChange={(value) => setEditingForm({ ...editingForm, server_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择服务器（可选）" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="unassigned">未分配</SelectItem>
                    {servers.map((server) => (
                      <SelectItem key={server.node_id} value={server.node_id}>
                        {server.node_id} ({server.status}) - {server.accounts_count}/{server.max_accounts}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  选择此账号運行的服务器节点（可选，未分配則在本地運行）
                </p>
              </div>

              <div className="flex gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setEditDialogOpen(false)}
                  className="flex-1"
                >
                  取消
                </Button>
                <Button
                  onClick={handleUpdate}
                  className="flex-1"
                  disabled={updating}
                >
                  {updating ? "更新中..." : "保存更改"}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* 批量选择Session对话框 */}
      <Dialog 
        open={batchSelectDialogOpen} 
        onOpenChange={(open) => {
          // 如果正在创建，不允許关闭对话框
          if (!open && batchCreating) {
            return
          }
          setBatchSelectDialogOpen(open)
        }}
      >
        <DialogContent className="max-w-4xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>批量选择 Session 文件</DialogTitle>
            <DialogDescription>
              选择一个或多个 Session 文件进行批量创建账号。账号 ID 將自动從文件名中提取（去掉 .session 擴展名）。
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-auto space-y-4 py-4">
            <div className="flex items-center justify-between pb-2 border-b">
              <div className="text-sm text-muted-foreground">
                已选择 {selectedSessions.size} / {availableSessions.length} 个文件
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={toggleSelectAll}
                >
                  {selectedSessions.size === availableSessions.length ? "取消全选" : "全选"}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedSessions(new Set())}
                >
                  清除选择
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              {availableSessions.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  暫无可用 session 文件，請点击「扫描 Session」或「上傳 Session」
                </div>
              ) : (
                availableSessions.map((session) => {
                  const isSelected = selectedSessions.has(session.filename)
                  const accountId = extractAccountIdFromSessionFile(session.filename)
                  return (
                    <div
                      key={session.filename}
                      className={`flex items-center gap-3 p-3 border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer ${
                        isSelected ? "bg-accent border-primary" : ""
                      }`}
                      onClick={() => toggleSessionSelect(session.filename)}
                    >
                      <div className="flex-shrink-0">
                        {isSelected ? (
                          <CheckSquare className="h-5 w-5 text-primary" />
                        ) : (
                          <SquareIcon className="h-5 w-5 text-muted-foreground" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium truncate">{session.filename}</p>
                          <Badge variant="outline" className="text-xs">
                            {(session.size / 1024).toFixed(1)} KB
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          账号 ID: <span className="font-mono">{accountId}</span>
                        </p>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>

          <div className="space-y-4 pt-4 border-t">
            {/* 创建進度條 */}
            {batchCreating && batchCreateProgress.total > 0 && (
              <div className="space-y-2 p-4 bg-muted rounded-lg">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">创建進度</span>
                  <span className="text-muted-foreground">
                    {batchCreateProgress.current} / {batchCreateProgress.total}
                  </span>
                </div>
                <Progress 
                  value={(batchCreateProgress.current / batchCreateProgress.total) * 100} 
                  className="h-2"
                />
                {batchCreateProgress.currentAccountId && (
                  <div className="text-xs text-muted-foreground mt-1">
                    正在创建: <span className="font-mono font-medium">{batchCreateProgress.currentAccountId}</span>
                  </div>
                )}
              </div>
            )}

            <div className="space-y-2">
              <Label>剧本 ID *</Label>
              <Select
                value={formData.script_id}
                onValueChange={(value) => setFormData({ ...formData, script_id: value })}
                disabled={batchCreating}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择剧本（所有選中的 Session 將使用此剧本）" />
                </SelectTrigger>
                <SelectContent>
                  {scripts.length === 0 ? (
                    <div className="px-2 py-1.5 text-sm text-muted-foreground">
                      暫无可用剧本，請先创建剧本
                    </div>
                  ) : (
                    scripts.map((script) => (
                      <SelectItem key={script.script_id} value={script.script_id}>
                        {script.name || script.script_id} {script.version && `(v${script.version})`}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  if (!batchCreating) {
                    setBatchSelectDialogOpen(false)
                    setSelectedSessions(new Set())
                  }
                }}
                disabled={batchCreating}
                className="flex-1"
              >
                取消
              </Button>
              <PermissionGuard permission="account:create">
                <Button
                  onClick={handleBatchCreate}
                  disabled={batchCreating || selectedSessions.size === 0 || !formData.script_id}
                  className="flex-1"
                >
                  {batchCreating ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      创建中... ({batchCreateProgress.current}/{batchCreateProgress.total})
                    </>
                  ) : (
                    `批量创建 (${selectedSessions.size} 个)`
                  )}
                </Button>
              </PermissionGuard>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 创建群组对话框 */}
      <Dialog open={createGroupDialogOpen} onOpenChange={setCreateGroupDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>创建新群组</DialogTitle>
            <DialogDescription>
              為账号 {createGroupAccountId} 创建新的 Telegram 群组並启动自动群聊
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>群组標題 *</Label>
              <Input
                placeholder="输入群组名称"
                value={createGroupForm.title}
                onChange={(e) => setCreateGroupForm({ ...createGroupForm, title: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>群组描述（可选）</Label>
              <Input
                placeholder="输入群组描述"
                value={createGroupForm.description}
                onChange={(e) => setCreateGroupForm({ ...createGroupForm, description: e.target.value })}
              />
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="auto_reply"
                checked={createGroupForm.auto_reply}
                onChange={(e) => setCreateGroupForm({ ...createGroupForm, auto_reply: e.target.checked })}
                className="rounded"
              />
              <Label htmlFor="auto_reply" className="cursor-pointer">
                自动启动群聊（啟用自动回复）
              </Label>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setCreateGroupDialogOpen(false)}
                className="flex-1"
              >
                取消
              </Button>
              <Button
                onClick={handleSubmitCreateGroup}
                className="flex-1"
                disabled={!createGroupForm.title.trim()}
              >
                创建並启动
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 批量操作对话框 */}
      <Dialog open={batchOperationDialogOpen} onOpenChange={setBatchOperationDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {batchOperation === "update" && "批量更新配置"}
              {batchOperation === "start" && "批量启动账号"}
              {batchOperation === "stop" && "批量停止账号"}
              {batchOperation === "delete" && "批量删除账号"}
            </DialogTitle>
            <DialogDescription>
              {batchOperation === "update" && `將更新 ${selectedAccounts.size} 个账号的配置`}
              {batchOperation === "start" && `將启动 ${selectedAccounts.size} 个账号`}
              {batchOperation === "stop" && `將停止 ${selectedAccounts.size} 个账号`}
              {batchOperation === "delete" && `确定要删除 ${selectedAccounts.size} 个账号嗎？此操作无法撤銷。`}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {batchOperation === "update" && (
              <>
                <div>
                  <Label htmlFor="batch_script_id">剧本（可选）</Label>
                  <Select
                    value={batchUpdateForm.script_id || "__none__"}
                    onValueChange={(value) => setBatchUpdateForm({ ...batchUpdateForm, script_id: value === "__none__" ? "" : value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择剧本（留空不更新）" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">不更新</SelectItem>
                      {scripts.map((script) => (
                        <SelectItem key={script.script_id} value={script.script_id}>
                          {script.name} ({script.script_id})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="batch_server_id">服务器（可选）</Label>
                  <Select
                    value={batchUpdateForm.server_id || "__none__"}
                    onValueChange={(value) => setBatchUpdateForm({ ...batchUpdateForm, server_id: value === "__none__" ? "" : value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择服务器（留空不更新）" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">不更新</SelectItem>
                      <SelectItem value="unassigned">未分配</SelectItem>
                      {servers.map((server) => (
                        <SelectItem key={server.node_id} value={server.node_id}>
                          {server.node_id} ({server.status})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="batch_active">啟用状态（可选）</Label>
                  <Select
                    value={batchUpdateForm.active === undefined ? "__none__" : batchUpdateForm.active ? "true" : "false"}
                    onValueChange={(value) => setBatchUpdateForm({ 
                      ...batchUpdateForm, 
                      active: value === "__none__" ? undefined : value === "true" 
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择状态（留空不更新）" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">不更新</SelectItem>
                      <SelectItem value="true">啟用</SelectItem>
                      <SelectItem value="false">停用</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}
            {(batchOperation === "start" || batchOperation === "stop") && (
              <Alert>
                <AlertDescription>
                  {batchOperation === "start" && `确定要启动 ${selectedAccounts.size} 个账号嗎？`}
                  {batchOperation === "stop" && `确定要停止 ${selectedAccounts.size} 个账号嗎？`}
                </AlertDescription>
              </Alert>
            )}
            {batchOperation === "delete" && (
              <Alert variant="destructive">
                <AlertDescription>
                  警告：此操作將永久删除選中的 {selectedAccounts.size} 个账号，无法撤銷。請确认您要删除的账号：
                  <ul className="list-disc list-inside mt-2">
                    {Array.from(selectedAccounts).slice(0, 10).map((id) => (
                      <li key={id} className="text-sm">{id}</li>
                    ))}
                    {selectedAccounts.size > 10 && <li className="text-sm">... 還有 {selectedAccounts.size - 10} 个</li>}
                  </ul>
                </AlertDescription>
              </Alert>
            )}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setBatchOperationDialogOpen(false)}>
                取消
              </Button>
              <Button 
                onClick={handleBatchOperation} 
                disabled={batchOperating}
                variant={batchOperation === "delete" ? "destructive" : "default"}
              >
                {batchOperating ? "处理中..." : "确认"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 角色分配对话框 */}
      <Dialog open={roleAssignmentDialogOpen} onOpenChange={setRoleAssignmentDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>分配角色</DialogTitle>
            <DialogDescription>
              为账号 {selectedAccountForRole?.account_id} 分配角色
              {selectedAccountForRole?.script_id && `（剧本：${selectedAccountForRole.script_id}）`}
            </DialogDescription>
          </DialogHeader>
          {selectedAccountForRole && (
            <div className="space-y-4 py-4">
              {!selectedAccountForRole.script_id ? (
                <Alert>
                  <AlertDescription>
                    该账号尚未分配剧本，请先为账号分配剧本后再分配角色。
                  </AlertDescription>
                </Alert>
              ) : selectedScriptRoles.length === 0 ? (
                <Alert>
                  <AlertDescription>
                    该剧本没有定义角色，或无法提取角色信息。
                  </AlertDescription>
                </Alert>
              ) : (
                <>
                  <div className="space-y-2">
                    <Label>选择角色</Label>
                    <div className="grid grid-cols-2 gap-2">
                      {selectedScriptRoles.map(role => (
                        <Button
                          key={role.role_id}
                          variant={accountRoleAssignments[selectedAccountForRole.account_id] === role.role_id ? "default" : "outline"}
                          onClick={() => handleAssignRole(selectedAccountForRole.account_id, role.role_id)}
                          disabled={assigningRole}
                          className="justify-start"
                        >
                          <Users className="h-4 w-4 mr-2" />
                          <div className="flex-1 text-left">
                            <div className="font-medium">{role.role_name}</div>
                            <div className="text-xs text-muted-foreground">
                              {role.dialogue_count} 条对话
                            </div>
                          </div>
                        </Button>
                      ))}
                    </div>
                  </div>
                  {accountRoleAssignments[selectedAccountForRole.account_id] && (() => {
                    const roleId = accountRoleAssignments[selectedAccountForRole.account_id]
                    const role = selectedScriptRoles.find(r => r.role_id === roleId)
                    return role && (
                      <Alert>
                        <AlertDescription>
                          当前已分配角色：<strong>{role.role_name}</strong>
                        </AlertDescription>
                      </Alert>
                    )
                  })()}
                </>
              )}
              <div className="flex gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setRoleAssignmentDialogOpen(false)}
                  className="flex-1"
                >
                  关闭
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Telegram 賬號批量導入對話框 */}
      <Dialog open={importDialogOpen} onOpenChange={(open) => {
        setImportDialogOpen(open)
        if (!open) {
          setImportFile(null)
          setImportResult(null)
        }
      }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>批量導入 Telegram 賬號配置</DialogTitle>
            <DialogDescription>
              從文件導入 Telegram 賬號配置（API_ID, API_HASH, SESSION_NAME）
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {importFile && (
              <div className="space-y-2">
                <Label>選擇的文件</Label>
                <div className="flex items-center gap-2 p-3 bg-muted rounded-md">
                  <FileText className="h-5 w-5 text-muted-foreground" />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{importFile.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(importFile.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setImportFile(null)
                      const input = document.getElementById('telegram-import') as HTMLInputElement
                      if (input) input.value = ''
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}

            <Alert>
              <AlertDescription>
                <p className="font-medium mb-2">支持的文件格式：</p>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li><strong>TXT/CSV 文件</strong>：每行格式為 <code>API_ID|API_HASH|SESSION_NAME</code> 或 <code>API_ID,API_HASH,SESSION_NAME</code></li>
                  <li><strong>Excel 文件</strong>：包含列 <code>API_ID</code>, <code>API_HASH</code>, <code>SESSION_NAME</code></li>
                </ul>
                <p className="mt-2 text-sm text-muted-foreground">
                  注意：導入的配置將保存到數據庫，但不會自動啟動賬號。您需要在賬號列表中手動啟動。
                </p>
              </AlertDescription>
            </Alert>

            {importResult && (
              <div className="space-y-2">
                <Label>導入結果</Label>
                <div className="p-4 bg-muted rounded-md space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">總數：</span>
                    <span className="text-sm font-medium">{importResult.total}</span>
                  </div>
                  <div className="flex items-center justify-between text-green-600">
                    <span className="text-sm">成功：</span>
                    <span className="text-sm font-medium">{importResult.success}</span>
                  </div>
                  {importResult.failed > 0 && (
                    <div className="flex items-center justify-between text-red-600">
                      <span className="text-sm">失敗：</span>
                      <span className="text-sm font-medium">{importResult.failed}</span>
                    </div>
                  )}
                  {importResult.errors && importResult.errors.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm font-medium mb-1">錯誤詳情：</p>
                      <div className="max-h-32 overflow-y-auto space-y-1">
                        {importResult.errors.map((error, index) => (
                          <p key={index} className="text-xs text-red-600">{error}</p>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {importing && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span className="text-sm">正在導入，請稍候...</span>
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2">
            <Button 
              variant="outline" 
              onClick={() => {
                setImportDialogOpen(false)
                setImportFile(null)
                setImportResult(null)
              }}
              disabled={importing}
            >
              取消
            </Button>
            <Button 
              onClick={executeImport}
              disabled={!importFile || importing}
            >
              {importing ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  導入中...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  開始導入
                </>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
