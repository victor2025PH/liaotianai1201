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
  type Account, 
  type AccountCreateRequest,
  type SessionFile,
  type Script
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
    title: "劇本管理",
    description: "創建和管理 AI 對話劇本（必需）",
    href: "/group-ai/scripts",
    status: "completed",
  },
  {
    number: 2,
    title: "賬號管理",
    description: "創建和管理 Telegram 賬號，關聯劇本",
    href: "/group-ai/accounts",
    status: "current",
  },
  {
    number: 3,
    title: "角色分配",
    description: "從劇本提取角色並分配給賬號（可選）",
    href: "/group-ai/role-assignments",
    status: "optional",
  },
  {
    number: 4,
    title: "分配方案",
    description: "保存和重用角色分配方案（可選）",
    href: "/group-ai/role-assignment-schemes",
    status: "optional",
  },
  {
    number: 5,
    title: "自動化任務",
    description: "配置自動化執行任務（可選）",
    href: "/group-ai/automation-tasks",
    status: "optional",
  },
];

// 确保 SessionFile 类型被正确导入

export default function GroupAIAccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
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
  })
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
  
  // 批量操作相關狀態
  const [selectedAccounts, setSelectedAccounts] = useState<Set<string>>(new Set())
  const [batchOperationDialogOpen, setBatchOperationDialogOpen] = useState(false)
  const [batchOperation, setBatchOperation] = useState<"update" | "start" | "stop" | "delete">("update")
  const [batchOperating, setBatchOperating] = useState(false)
  const [batchUpdateForm, setBatchUpdateForm] = useState({
    script_id: "",
    server_id: "",
    active: undefined as boolean | undefined,
  })
  
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "加載失敗")
      showErrorDialog("加載失敗", err instanceof Error ? err.message : "無法加載賬號列表")
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
        showSuccessDialog("掃描成功", `找到 ${result.sessions.length} 個 session 文件`)
      } else {
        showWarningDialog("掃描完成", "未找到任何 session 文件，請確認文件已放置在 sessions 目錄中")
      }
    } catch (err) {
      console.error("掃描 Session 失敗:", err)
      showErrorDialog("掃描失敗", err instanceof Error ? err.message : "無法掃描 session 文件")
    } finally {
      setScanning(false)
    }
  }

  const fetchServers = async () => {
    try {
      const data = await getServers()
      setServers(data)
    } catch (err) {
      console.error("獲取服務器列表失敗:", err)
    }
  }

  const fetchScripts = async () => {
    try {
      const data = await getScripts()
      setScripts(data)
    } catch (err) {
      console.error("加載劇本列表失敗:", err)
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
      showSuccessDialog("成功", `賬號 ${accountId} 已啟動`)
      await fetchAccounts()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "啟動賬號失敗"
      showErrorDialog("啟動失敗", errorMessage)
      console.error(`啟動賬號 ${accountId} 失敗:`, err)
      // 即使失敗也刷新列表，確保狀態同步
      await fetchAccounts()
    }
  }

  const handleStop = async (accountId: string) => {
    try {
      await stopAccount(accountId)
      showSuccessDialog("成功", `賬號 ${accountId} 已停止`)
      await fetchAccounts()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "停止賬號失敗"
      showErrorDialog("停止失敗", errorMessage)
      console.error(`停止賬號 ${accountId} 失敗:`, err)
      // 即使失敗也刷新列表，確保狀態同步
      await fetchAccounts()
    }
  }

  const handleUploadSession = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // 檢查文件擴展名
    if (!file.name.endsWith('.session')) {
      showErrorDialog("錯誤", "只支持 .session 文件")
      return
    }

    // 檢查文件大小（限制10MB）
    if (file.size > 10 * 1024 * 1024) {
      showErrorDialog("錯誤", "文件大小不能超過10MB")
      return
    }

    try {
      setUploading(true)
      const result = await uploadSessionFile(file)
      showSuccessDialog("上傳成功", result.message)
      // 刷新session列表
      await fetchSessions()
      // 自動選擇上傳的文件
      setFormData({ ...formData, session_file: result.filename })
    } catch (err) {
      showErrorDialog("上傳失敗", err instanceof Error ? err.message : "上傳 session 文件失敗")
    } finally {
      setUploading(false)
      // 重置文件輸入
      event.target.value = ""
    }
  }

  const handleCreate = async () => {
    if (!formData.account_id || !formData.session_file || !formData.script_id) {
      showErrorDialog("錯誤", "請填寫所有必填字段")
      return
    }

    try {
      setCreating(true)
      const request: AccountCreateRequest = {
        account_id: formData.account_id,
        session_file: formData.session_file, // 使用文件名，後端會自動解析路徑
        script_id: formData.script_id,
      }
      await createAccount(request)
      showSuccessDialog("成功", `賬號 ${formData.account_id} 創建成功`)
      setDialogOpen(false)
      setFormData({ account_id: "", session_file: "", script_id: "" })
      // 刷新賬號列表和服務器狀態（確保服務器賬號數更新）
      await Promise.all([fetchAccounts(), fetchServers()])
    } catch (err) {
      showErrorDialog("創建失敗", err instanceof Error ? err.message : "創建賬號失敗")
    } finally {
      setCreating(false)
    }
  }

  // 批量创建账号
  const handleBatchCreate = async () => {
    if (selectedSessions.size === 0) {
      showErrorDialog("錯誤", "請至少選擇一個 Session 文件")
      return
    }

    if (!formData.script_id) {
      showErrorDialog("錯誤", "請選擇劇本")
      return
    }

    // 嚴格按照選中的文件列表創建，確保沒有遺漏或多餘
    const selectedFilenames = Array.from(selectedSessions)
    const sessions = selectedFilenames.map(filename => 
      availableSessions.find(s => s.filename === filename)
    ).filter(Boolean) as SessionFile[]

    if (sessions.length === 0) {
      showErrorDialog("錯誤", "未找到選中的 Session 文件")
      return
    }

    // 嚴格驗證：選中的文件數量必須等於找到的文件數量
    if (sessions.length !== selectedSessions.size) {
      const missing = selectedFilenames.filter(f => !sessions.find(s => s.filename === f))
      console.error(`嚴重錯誤：選中的文件數量 (${selectedSessions.size}) 與找到的文件數量 (${sessions.length}) 不匹配`)
      console.error(`缺失的文件:`, missing)
      showErrorDialog(
        "選擇錯誤", 
        `選中的 ${selectedSessions.size} 個文件中，只找到 ${sessions.length} 個有效文件。缺失：${missing.join(", ")}`
      )
      return
    }

    // 確認提示：顯示將要創建的賬號列表
    const accountIds = sessions.map(s => extractAccountIdFromSessionFile(s.filename))
    const scriptName = scripts.find(s => s.script_id === formData.script_id)?.name || formData.script_id
    
    // 使用 Promise 來處理確認對話框
    const confirmed = await new Promise<boolean>((resolve) => {
      // 設置確認對話框內容
      setBatchConfirmDialogTitle("確認批量創建賬號")
      setBatchConfirmDialogMessage(`確定要創建以下 ${sessions.length} 個賬號嗎？`)
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
      console.log(`[批量創建] 開始批量創建 ${sessions.length} 個賬號`)
      console.log(`[批量創建] 選中的文件列表:`, sessions.map(s => s.filename))
      console.log(`[批量創建] 將創建的賬號 ID:`, accountIds)
      
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
          
          console.log(`[批量創建] (${i+1}/${sessions.length}) 正在創建賬號: ${accountId}`)
          
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
          
          console.log(`[批量創建] (${i+1}/${sessions.length}) 賬號 ${accountId} 創建成功`)
          
          // 每个账号创建成功后立即显示提示，等待用户确认后再继续
          await new Promise<void>((resolve) => {
            showSuccessDialog(
              "賬號創建成功",
              `賬號 ${accountId} 創建成功！\n\n進度：${i + 1}/${sessions.length}\n\n點擊確認繼續創建下一個賬號。`,
              () => {
                resolve()
              }
            )
          })
        } catch (err) {
          console.error(`[批量創建] (${i+1}/${sessions.length}) 賬號 ${extractAccountIdFromSessionFile(session.filename)} 創建失敗:`, err)
          results.failed.push({
            filename: session.filename,
            error: err instanceof Error ? err.message : "未知錯誤"
          })
          
          // 更新進度（失敗）
          setBatchCreateProgress({
            current: i + 1,
            total: sessions.length,
            currentAccountId: extractAccountIdFromSessionFile(session.filename),
          })
        }
      }
      
      console.log(`[批量創建] 批量創建完成: 成功 ${results.success.length}, 失敗 ${results.failed.length}`)

      // 显示结果
      if (results.failed.length === 0) {
        showSuccessDialog(
          "批量創建成功", 
          `成功創建 ${results.success.length} 個賬號：\n${results.success.join(", ")}`
        )
      } else {
        const successMsg = results.success.length > 0 
          ? `成功：${results.success.length} 個\n${results.success.join(", ")}\n\n`
          : ""
        const failedMsg = `失敗：${results.failed.length} 個\n${results.failed.map(f => `${f.filename}: ${f.error}`).join("\n")}`
        showErrorDialog("批量創建部分失敗", successMsg + failedMsg)
      }

      setBatchSelectDialogOpen(false)
      setSelectedSessions(new Set())
      setBatchCreateProgress({
        current: 0,
        total: 0,
        currentAccountId: "",
      })
      // 刷新賬號列表和服務器狀態（確保服務器賬號數更新）
      await Promise.all([fetchAccounts(), fetchServers()])
    } catch (err) {
      showErrorDialog("批量創建失敗", err instanceof Error ? err.message : "批量創建賬號失敗")
    } finally {
      setBatchCreating(false)
      setBatchCreateProgress({
        current: 0,
        total: 0,
        currentAccountId: "",
      })
    }
  }

  // 批量操作處理函數
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
      showErrorDialog("錯誤", "請至少選擇一個賬號")
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
                results.failed.push({ accountId, error: "未選擇任何更新項" })
              }
            } catch (err) {
              results.failed.push({
                accountId,
                error: err instanceof Error ? err.message : "未知錯誤"
              })
            }
          }
          break

        case "start":
          // 批量啟動
          for (const accountId of accountIds) {
            try {
              await startAccount(accountId)
              results.success.push(accountId)
            } catch (err) {
              results.failed.push({
                accountId,
                error: err instanceof Error ? err.message : "未知錯誤"
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
                error: err instanceof Error ? err.message : "未知錯誤"
              })
            }
          }
          break

        case "delete":
          // 批量刪除
          for (const accountId of accountIds) {
            try {
              await deleteAccount(accountId)
              results.success.push(accountId)
            } catch (err) {
              results.failed.push({
                accountId,
                error: err instanceof Error ? err.message : "未知錯誤"
              })
            }
          }
          break
      }

      // 顯示結果
      if (results.failed.length === 0) {
        const actionText = {
          update: "批量更新",
          start: "批量啟動",
          stop: "批量停止",
          delete: "批量刪除"
        }[batchOperation]
        showSuccessDialog(
          `${actionText}成功`,
          `成功${actionText} ${results.success.length} 個賬號`
        )
      } else {
        const actionText = {
          update: "批量更新",
          start: "批量啟動",
          stop: "批量停止",
          delete: "批量刪除"
        }[batchOperation]
        const successMsg = results.success.length > 0
          ? `成功：${results.success.length} 個\n${results.success.join(", ")}\n\n`
          : ""
        const failedMsg = `失敗：${results.failed.length} 個\n${results.failed.map(f => `${f.accountId}: ${f.error}`).join("\n")}`
        showErrorDialog(`${actionText}部分失敗`, successMsg + failedMsg)
      }

      setBatchOperationDialogOpen(false)
      setSelectedAccounts(new Set())
      await fetchAccounts()
    } catch (err) {
      const actionText = {
        update: "批量更新",
        start: "批量啟動",
        stop: "批量停止",
        delete: "批量刪除"
      }[batchOperation]
      showErrorDialog(`${actionText}失敗`, err instanceof Error ? err.message : `${actionText}賬號失敗`)
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
      "確認刪除",
      `確定要刪除賬號 ${accountId} 嗎？此操作無法撤銷。`,
      async () => {
        try {
          await deleteAccount(accountId)
          showSuccessDialog("成功", `賬號 ${accountId} 已刪除`)
          await fetchAccounts()
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : "刪除賬號失敗"
          // 如果賬號不存在，也刷新列表（可能是前端數據不同步）
          if (errorMessage.includes("不存在")) {
            showWarningDialog("賬號不存在", `賬號 ${accountId} 不存在，已從列表中移除。`)
            await fetchAccounts() // 刷新列表以同步數據
          } else {
            showErrorDialog("刪除失敗", errorMessage)
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
      showErrorDialog("錯誤", "請輸入群組標題")
      return
    }

    try {
      const result = await createGroup({
        account_id: createGroupAccountId,
        title: createGroupForm.title,
        description: createGroupForm.description || undefined,
        auto_reply: createGroupForm.auto_reply
      })
      showSuccessDialog("成功", `群組 "${result.group_title || createGroupForm.title}" 創建成功並已啟動群聊`)
      setCreateGroupDialogOpen(false)
      await fetchAccounts()
    } catch (err) {
      showErrorDialog("創建失敗", err instanceof Error ? err.message : "創建群組失敗")
    }
  }

  const handleStartGroupChat = async (accountId: string, groupId: number) => {
    try {
      const result = await startGroupChat({
        account_id: accountId,
        group_id: groupId,
        auto_reply: true
      })
      showSuccessDialog("成功", `群組聊天已啟動`)
      await fetchAccounts()
    } catch (err) {
      showErrorDialog("啟動失敗", err instanceof Error ? err.message : "啟動群組聊天失敗")
    }
  }

  const handleEdit = (account: Account) => {
    setEditingAccount(account)
    setEditingForm({
      display_name: account.display_name || account.first_name || account.username || account.account_id,
      bio: account.bio || "",
      script_id: account.script_id,
      server_id: account.server_id === "unassigned" || !account.server_id ? "" : account.server_id,
    })
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
      showSuccessDialog("成功", `賬號 ${editingAccount.account_id} 已更新`)
      setEditDialogOpen(false)
      await fetchAccounts()
    } catch (err) {
      showErrorDialog("更新失敗", err instanceof Error ? err.message : "更新賬號失敗")
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
      <StepIndicator
        currentStep={2}
        steps={workflowSteps}
        title="賬號管理"
        description="創建和管理 Telegram 賬號，關聯劇本"
        guideContent={
          <>
            <p className="font-semibold mb-2">使用指導：</p>
            <ol className="list-decimal list-inside space-y-1 text-sm">
              <li>確保已完成 <Link href="/group-ai/scripts" className="text-primary underline">步驟 1：劇本管理</Link></li>
              <li>通過「掃描 Session」或「上傳 Session」添加 Telegram 賬號</li>
              <li>為每個賬號選擇對應的劇本（必需）</li>
              <li>配置賬號的顯示名稱、簡介等信息</li>
              <li>將賬號分配到服務器節點</li>
              <li>完成後，可進入 <Link href="/group-ai/role-assignments" className="text-primary underline">步驟 3：角色分配</Link>（可選）</li>
            </ol>
          </>
        }
      />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">群組 AI 賬號管理</h1>
          <p className="text-muted-foreground mt-2">管理 Telegram 群組 AI 賬號</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => fetchAccounts()} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
          <Button onClick={fetchSessions} variant="outline" size="sm" disabled={scanning}>
            <Scan className="h-4 w-4 mr-2" />
            {scanning ? "掃描中..." : "掃描 Session"}
          </Button>
          <Dialog 
            open={dialogOpen} 
            onOpenChange={(open) => {
              setDialogOpen(open)
              if (!open) {
                // 關閉時重置表單
                setFormData({ account_id: "", session_file: "", script_id: "" })
              }
            }}
          >
            <PermissionGuard permission="account:create">
              <Button onClick={() => setDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                添加賬號
              </Button>
            </PermissionGuard>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>添加新賬號</DialogTitle>
                <DialogDescription>配置新的 Telegram AI 賬號</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>賬號 ID *</Label>
                  <Input 
                    placeholder="將從 Session 文件自動提取，或手動輸入自定義 ID" 
                    value={formData.account_id}
                    onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
                  />
                  {formData.session_file && (
                    <p className="text-xs text-muted-foreground">
                      💡 已從 Session 文件自動提取，可手動修改為自定義 ID
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
                        選擇 Session
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
                      <SelectValue placeholder="選擇或輸入 session 文件名" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableSessions.length === 0 ? (
                        <div className="px-2 py-1.5 text-sm text-muted-foreground">
                          暫無可用 session 文件，請點擊「掃描 Session」或「上傳 Session」
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
                      已掃描到 {availableSessions.length} 個 session 文件，點擊「選擇 Session」可批量選擇並創建
                    </p>
                  )}
                  {formData.session_file && !availableSessions.find(s => s.filename === formData.session_file) && (
                    <Input
                      placeholder="或手動輸入文件名（如：account.session）"
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
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>劇本 ID *</Label>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => router.push("/group-ai/scripts")}
                      className="h-auto p-1 text-xs"
                    >
                      管理劇本
                      <ArrowRight className="h-3 w-3 ml-1" />
                    </Button>
                  </div>
                  <Select
                    value={formData.script_id}
                    onValueChange={(value) => setFormData({ ...formData, script_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="選擇劇本或輸入劇本 ID" />
                    </SelectTrigger>
                    <SelectContent>
                      {scripts.length === 0 ? (
                        <div className="px-2 py-1.5 text-sm text-muted-foreground">
                          暫無可用劇本，請先創建劇本
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
                  {formData.script_id && !scripts.find(s => s.script_id === formData.script_id) && (
                    <Input 
                      placeholder="或手動輸入劇本 ID（如：default）" 
                      value={formData.script_id}
                      onChange={(e) => setFormData({ ...formData, script_id: e.target.value })}
                      className="mt-2"
                    />
                  )}
                </div>
                <Button 
                  className="w-full" 
                  onClick={handleCreate}
                  disabled={creating || uploading}
                >
                  {creating ? "創建中..." : "創建"}
                </Button>
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
              <Badge variant="secondary">{availableSessions.length} 個文件</Badge>
            </CardTitle>
            <CardDescription>
              已掃描到的 Session 文件，可用於創建新賬號。點擊文件卡片可直接使用該文件創建賬號，或點擊「添加賬號」按鈕。支持多選進行批量創建。
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
                    title={`點擊使用 ${session.filename} 創建賬號，按住 Ctrl/Cmd 鍵可多選進行批量創建`}
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
                  已選擇 <strong>{selectedSessions.size}</strong> 個 Session 文件
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedSessions(new Set())
                    }}
                  >
                    清除選擇
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => {
                      setBatchSelectDialogOpen(true)
                    }}
                  >
                    批量創建賬號
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
            placeholder="搜索賬號ID、名稱、用戶名或手機號..."
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
            <SelectValue placeholder="全部狀態" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">全部狀態</SelectItem>
            <SelectItem value="online">在線</SelectItem>
            <SelectItem value="offline">離線</SelectItem>
            <SelectItem value="error">錯誤</SelectItem>
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
            <SelectValue placeholder="全部劇本" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">全部劇本</SelectItem>
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
            <SelectValue placeholder="全部服務器" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">全部服務器</SelectItem>
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
              <CardTitle>賬號列表</CardTitle>
              <CardDescription>共 {accounts.length} 個賬號</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <PermissionGuard permission="export:account">
                    <Button variant="outline" size="sm" disabled={loading || accounts.length === 0}>
                      <Download className="mr-2 h-4 w-4" />
                      導出
                    </Button>
                  </PermissionGuard>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuLabel>選擇導出格式</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={async () => {
                      try {
                        const blob = await exportAccounts("csv")
                        const filename = `賬號列表_${new Date().toISOString().slice(0, 10)}.csv`
                        downloadBlob(blob, filename)
                        showSuccessDialog("導出成功", "賬號列表已導出為 CSV")
                      } catch (err) {
                        showErrorDialog("導出失敗", err instanceof Error ? err.message : "無法導出賬號列表")
                      }
                    }}
                  >
                    CSV 格式
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={async () => {
                      try {
                        const blob = await exportAccounts("excel")
                        const filename = `賬號列表_${new Date().toISOString().slice(0, 10)}.xlsx`
                        downloadBlob(blob, filename)
                        showSuccessDialog("導出成功", "賬號列表已導出為 Excel")
                      } catch (err) {
                        showErrorDialog("導出失敗", err instanceof Error ? err.message : "無法導出賬號列表")
                      }
                    }}
                  >
                    Excel 格式
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={async () => {
                      try {
                        const blob = await exportAccounts("pdf")
                        const filename = `賬號列表_${new Date().toISOString().slice(0, 10)}.pdf`
                        downloadBlob(blob, filename)
                        showSuccessDialog("導出成功", "賬號列表已導出為 PDF")
                      } catch (err) {
                        showErrorDialog("導出失敗", err instanceof Error ? err.message : "無法導出賬號列表")
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
                    已選擇 {selectedAccounts.size} 個賬號
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
                    批量啟動
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
                    批量刪除
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setSelectedAccounts(new Set())}
                  >
                    取消選擇
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
          ) : accounts.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              暫無賬號，點擊「添加賬號」創建第一個賬號
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
                  <TableHead>帳號資料</TableHead>
                  <TableHead>狀態</TableHead>
                  <TableHead>劇本</TableHead>
                  <TableHead>服務器</TableHead>
                  <TableHead>群組數</TableHead>
                  <TableHead>消息數</TableHead>
                  <TableHead>回復數</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
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
                                // 如果圖片加載失敗，顯示默認頭像
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
                    <TableCell>{account.script_id}</TableCell>
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
                              title="啟動"
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
                            title="編輯資料"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                        </PermissionGuard>
                        <PermissionGuard permission="account:update">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => router.push(`/group-ai/accounts/${account.account_id}/params`)}
                            title="賬號設置"
                          >
                            <Settings className="h-4 w-4" />
                          </Button>
                        </PermissionGuard>
                        <PermissionGuard permission="role_assignment:view">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => router.push(`/group-ai/role-assignments?account=${account.account_id}`)}
                            title="角色分配"
                          >
                            <Users className="h-4 w-4" />
                          </Button>
                        </PermissionGuard>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleCreateGroup(account.account_id)}
                          title="創建群組"
                        >
                          <UserPlus className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            if (account.group_count > 0) {
                              showWarningDialog(
                                "啟動群組聊天",
                                "請先創建群組或加入群組，然後使用群組ID啟動聊天",
                                () => {}
                              )
                            } else {
                              showWarningDialog(
                                "提示",
                                "該賬號尚未加入任何群組，請先創建或加入群組",
                                () => {}
                              )
                            }
                          }}
                          title="啟動群組聊天"
                        >
                          <MessageSquare className="h-4 w-4" />
                        </Button>
                        <PermissionGuard permission="account:delete">
                          <Button 
                            size="sm" 
                            variant="destructive"
                            onClick={() => handleDelete(account.account_id)}
                            title="刪除賬號"
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
              確認
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
              確認
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
              確認
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
                劇本：<span className="font-medium">{batchConfirmDialogScriptName}</span>
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
              確定
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 編輯帳號資料對話框 */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>編輯帳號資料</DialogTitle>
            <DialogDescription>
              編輯帳號 {editingAccount?.account_id} 的資料信息和配置
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
                <Label>個人簡介</Label>
                <Textarea
                  placeholder="輸入個人簡介"
                  value={editingForm.bio}
                  onChange={(e) => setEditingForm({ ...editingForm, bio: e.target.value })}
                  rows={3}
                />
                <p className="text-xs text-muted-foreground">
                  帳號的個人簡介信息
                </p>
              </div>

              <div className="space-y-2">
                <Label>劇本</Label>
                <Select
                  value={editingForm.script_id}
                  onValueChange={(value) => setEditingForm({ ...editingForm, script_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="選擇劇本" />
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
                  選擇此帳號使用的劇本
                </p>
              </div>

              <div className="space-y-2">
                <Label>服務器</Label>
                <Select
                  value={editingForm.server_id}
                  onValueChange={(value) => setEditingForm({ ...editingForm, server_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="選擇服務器（可選）" />
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
                  選擇此帳號運行的服務器節點（可選，未分配則在本地運行）
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

      {/* 批量選擇Session對話框 */}
      <Dialog 
        open={batchSelectDialogOpen} 
        onOpenChange={(open) => {
          // 如果正在創建，不允許關閉對話框
          if (!open && batchCreating) {
            return
          }
          setBatchSelectDialogOpen(open)
        }}
      >
        <DialogContent className="max-w-4xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>批量選擇 Session 文件</DialogTitle>
            <DialogDescription>
              選擇一個或多個 Session 文件進行批量創建賬號。賬號 ID 將自動從文件名中提取（去掉 .session 擴展名）。
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-auto space-y-4 py-4">
            <div className="flex items-center justify-between pb-2 border-b">
              <div className="text-sm text-muted-foreground">
                已選擇 {selectedSessions.size} / {availableSessions.length} 個文件
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={toggleSelectAll}
                >
                  {selectedSessions.size === availableSessions.length ? "取消全選" : "全選"}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedSessions(new Set())}
                >
                  清除選擇
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              {availableSessions.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  暫無可用 session 文件，請點擊「掃描 Session」或「上傳 Session」
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
                          賬號 ID: <span className="font-mono">{accountId}</span>
                        </p>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>

          <div className="space-y-4 pt-4 border-t">
            {/* 創建進度條 */}
            {batchCreating && batchCreateProgress.total > 0 && (
              <div className="space-y-2 p-4 bg-muted rounded-lg">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">創建進度</span>
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
                    正在創建: <span className="font-mono font-medium">{batchCreateProgress.currentAccountId}</span>
                  </div>
                )}
              </div>
            )}

            <div className="space-y-2">
              <Label>劇本 ID *</Label>
              <Select
                value={formData.script_id}
                onValueChange={(value) => setFormData({ ...formData, script_id: value })}
                disabled={batchCreating}
              >
                <SelectTrigger>
                  <SelectValue placeholder="選擇劇本（所有選中的 Session 將使用此劇本）" />
                </SelectTrigger>
                <SelectContent>
                  {scripts.length === 0 ? (
                    <div className="px-2 py-1.5 text-sm text-muted-foreground">
                      暫無可用劇本，請先創建劇本
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
                      創建中... ({batchCreateProgress.current}/{batchCreateProgress.total})
                    </>
                  ) : (
                    `批量創建 (${selectedSessions.size} 個)`
                  )}
                </Button>
              </PermissionGuard>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 創建群組對話框 */}
      <Dialog open={createGroupDialogOpen} onOpenChange={setCreateGroupDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>創建新群組</DialogTitle>
            <DialogDescription>
              為賬號 {createGroupAccountId} 創建新的 Telegram 群組並啟動自動群聊
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>群組標題 *</Label>
              <Input
                placeholder="輸入群組名稱"
                value={createGroupForm.title}
                onChange={(e) => setCreateGroupForm({ ...createGroupForm, title: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>群組描述（可選）</Label>
              <Input
                placeholder="輸入群組描述"
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
                自動啟動群聊（啟用自動回復）
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
                創建並啟動
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 批量操作對話框 */}
      <Dialog open={batchOperationDialogOpen} onOpenChange={setBatchOperationDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {batchOperation === "update" && "批量更新配置"}
              {batchOperation === "start" && "批量啟動賬號"}
              {batchOperation === "stop" && "批量停止賬號"}
              {batchOperation === "delete" && "批量刪除賬號"}
            </DialogTitle>
            <DialogDescription>
              {batchOperation === "update" && `將更新 ${selectedAccounts.size} 個賬號的配置`}
              {batchOperation === "start" && `將啟動 ${selectedAccounts.size} 個賬號`}
              {batchOperation === "stop" && `將停止 ${selectedAccounts.size} 個賬號`}
              {batchOperation === "delete" && `確定要刪除 ${selectedAccounts.size} 個賬號嗎？此操作無法撤銷。`}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {batchOperation === "update" && (
              <>
                <div>
                  <Label htmlFor="batch_script_id">劇本（可選）</Label>
                  <Select
                    value={batchUpdateForm.script_id || "__none__"}
                    onValueChange={(value) => setBatchUpdateForm({ ...batchUpdateForm, script_id: value === "__none__" ? "" : value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="選擇劇本（留空不更新）" />
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
                  <Label htmlFor="batch_server_id">服務器（可選）</Label>
                  <Select
                    value={batchUpdateForm.server_id || "__none__"}
                    onValueChange={(value) => setBatchUpdateForm({ ...batchUpdateForm, server_id: value === "__none__" ? "" : value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="選擇服務器（留空不更新）" />
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
                  <Label htmlFor="batch_active">啟用狀態（可選）</Label>
                  <Select
                    value={batchUpdateForm.active === undefined ? "__none__" : batchUpdateForm.active ? "true" : "false"}
                    onValueChange={(value) => setBatchUpdateForm({ 
                      ...batchUpdateForm, 
                      active: value === "__none__" ? undefined : value === "true" 
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="選擇狀態（留空不更新）" />
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
                  {batchOperation === "start" && `確定要啟動 ${selectedAccounts.size} 個賬號嗎？`}
                  {batchOperation === "stop" && `確定要停止 ${selectedAccounts.size} 個賬號嗎？`}
                </AlertDescription>
              </Alert>
            )}
            {batchOperation === "delete" && (
              <Alert variant="destructive">
                <AlertDescription>
                  警告：此操作將永久刪除選中的 {selectedAccounts.size} 個賬號，無法撤銷。請確認您要刪除的賬號：
                  <ul className="list-disc list-inside mt-2">
                    {Array.from(selectedAccounts).slice(0, 10).map((id) => (
                      <li key={id} className="text-sm">{id}</li>
                    ))}
                    {selectedAccounts.size > 10 && <li className="text-sm">... 還有 {selectedAccounts.size - 10} 個</li>}
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
                {batchOperating ? "處理中..." : "確認"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
