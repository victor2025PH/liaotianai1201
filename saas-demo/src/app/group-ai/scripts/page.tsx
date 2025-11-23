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
import { Plus, FileText, Play, Edit, Trash2, RefreshCw, Sparkles, Upload, Wand2, History, GitCompare, RotateCcw, CheckCircle, XCircle, Send, Eye, EyeOff, Download, Search, X, CheckSquare, Square as SquareIcon } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { PermissionGuard } from "@/components/permissions/permission-guard"
import { PermissionButton } from "@/components/permissions/permission-button"
import { StepIndicator, type Step } from "@/components/step-indicator"
import Link from "next/link"
  import {
  getScripts,
  getScript,
  createScript,
  updateScript,
  deleteScript,
  testScript,
  convertFormat,
  optimizeContent,
  listScriptVersions,
  getScriptVersionContent,
  compareScriptVersions,
  restoreScriptVersion,
  submitScriptReview,
  reviewScript,
  publishScript,
  disableScriptReview,
  revertScriptToDraft,
  exportScripts,
  downloadBlob,
  batchOperateScripts,
  type Script,
  type ScriptCreateRequest,
  type ScriptUpdateRequest,
  type ScriptVersion,
  type VersionCompareResponse,
  type ExportFormat,
  type BatchScriptRequest,
} from "@/lib/api/group-ai"

const workflowSteps: Step[] = [
  {
    number: 1,
    title: "劇本管理",
    description: "創建和管理 AI 對話劇本（必需）",
    href: "/group-ai/scripts",
    status: "current",
  },
  {
    number: 2,
    title: "賬號管理",
    description: "創建和管理 Telegram 賬號，關聯劇本",
    href: "/group-ai/accounts",
    status: "pending",
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

export default function GroupAIScriptsPage() {
  const [scripts, setScripts] = useState<Script[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchFilters, setSearchFilters] = useState<{
    search?: string
    status?: string
    sort_by?: string
    sort_order?: "asc" | "desc"
  }>({})
  const [dialogOpen, setDialogOpen] = useState(false)
  const [testDialogOpen, setTestDialogOpen] = useState(false)
  const [editingScript, setEditingScript] = useState<Script | null>(null)
  const [testingScriptId, setTestingScriptId] = useState<string | null>(null)
  const [testMessage, setTestMessage] = useState("")
  const [testResult, setTestResult] = useState<string | null>(null)
  const [testLoading, setTestLoading] = useState(false)
  const [converting, setConverting] = useState(false)
  const [optimizing, setOptimizing] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewContent, setPreviewContent] = useState<string>("")
  const [errorDialogOpen, setErrorDialogOpen] = useState(false)
  const [errorDialogTitle, setErrorDialogTitle] = useState("")
  const [errorDialogMessage, setErrorDialogMessage] = useState("")
  const [warningDialogOpen, setWarningDialogOpen] = useState(false)
  const [warningDialogTitle, setWarningDialogTitle] = useState("")
  const [warningDialogMessage, setWarningDialogMessage] = useState("")
  const [warningDialogOnConfirm, setWarningDialogOnConfirm] = useState<(() => void) | null>(null)
  
  // 版本管理相關狀態
  const [versionDialogOpen, setVersionDialogOpen] = useState(false)
  const [versionsDialogScriptId, setVersionsDialogScriptId] = useState<string | null>(null)
  const [versions, setVersions] = useState<ScriptVersion[]>([])
  const [versionsLoading, setVersionsLoading] = useState(false)
  const [versionDetailOpen, setVersionDetailOpen] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState<ScriptVersion | null>(null)
  const [versionContent, setVersionContent] = useState<string>("")
  const [compareDialogOpen, setCompareDialogOpen] = useState(false)
  const [compareResult, setCompareResult] = useState<VersionCompareResponse | null>(null)
  const [selectedVersion1, setSelectedVersion1] = useState<string>("")
  const [selectedVersion2, setSelectedVersion2] = useState<string>("")
  const [restoring, setRestoring] = useState(false)
  
  // 審核與發布相關狀態
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false)
  const [reviewingScriptId, setReviewingScriptId] = useState<string | null>(null)
  const [reviewAction, setReviewAction] = useState<"submit" | "approve" | "reject" | "publish" | "disable" | "revert">("submit")
  const [reviewComment, setReviewComment] = useState("")
  const [changeSummary, setChangeSummary] = useState("")
  const [reviewing, setReviewing] = useState(false)
  
  const [formData, setFormData] = useState<ScriptCreateRequest>({
    script_id: "",
    name: "",
    version: "1.0",
    yaml_content: "",
    description: "",
  })
  
  // 批量操作相關狀態
  const [selectedScripts, setSelectedScripts] = useState<Set<string>>(new Set())
  const [batchOperationDialogOpen, setBatchOperationDialogOpen] = useState(false)
  const [batchOperation, setBatchOperation] = useState<"delete" | "submit_review" | "publish" | "disable" | "revert_to_draft">("delete")
  const [batchOperating, setBatchOperating] = useState(false)
  
  const { toast } = useToast()

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

  // 打開版本歷史對話框
  const openVersionDialog = async (scriptId: string) => {
    setVersionsDialogScriptId(scriptId)
    setVersionDialogOpen(true)
    await fetchVersions(scriptId)
  }

  // 獲取版本列表
  const fetchVersions = async (scriptId: string) => {
    try {
      setVersionsLoading(true)
      const data = await listScriptVersions(scriptId)
      setVersions(data)
    } catch (err) {
      showErrorDialog("加載失敗", err instanceof Error ? err.message : "無法加載版本歷史")
    } finally {
      setVersionsLoading(false)
    }
  }

  // 查看版本詳情
  const viewVersionDetail = async (version: ScriptVersion) => {
    if (!versionsDialogScriptId) return
    try {
      setSelectedVersion(version)
      const content = await getScriptVersionContent(versionsDialogScriptId, version.version)
      setVersionContent(content.yaml_content)
      setVersionDetailOpen(true)
    } catch (err) {
      showErrorDialog("加載失敗", err instanceof Error ? err.message : "無法加載版本內容")
    }
  }

  // 版本對比
  const handleCompareVersions = async () => {
    if (!versionsDialogScriptId || !selectedVersion1 || !selectedVersion2) {
      showErrorDialog("參數錯誤", "請選擇兩個版本進行對比")
      return
    }
    if (selectedVersion1 === selectedVersion2) {
      showErrorDialog("參數錯誤", "請選擇不同的版本進行對比")
      return
    }
    try {
      const result = await compareScriptVersions(versionsDialogScriptId, selectedVersion1, selectedVersion2)
      setCompareResult(result)
      setCompareDialogOpen(true)
    } catch (err) {
      showErrorDialog("對比失敗", err instanceof Error ? err.message : "無法對比版本")
    }
  }

  // 恢復版本
  const handleRestoreVersion = async (version: ScriptVersion) => {
    if (!versionsDialogScriptId) return
    showWarningDialog(
      "確認恢復版本",
      `確定要恢復劇本到版本 ${version.version} 嗎？當前版本將自動保存到歷史記錄。`,
      async () => {
        try {
          setRestoring(true)
          await restoreScriptVersion(versionsDialogScriptId, version.version, {
            change_summary: `恢復到版本 ${version.version}`
          })
          toast({
            title: "恢復成功",
            description: `劇本已恢復到版本 ${version.version}`,
          })
          await fetchVersions(versionsDialogScriptId)
          // 强制刷新列表（不使用缓存）
          await fetchScripts(undefined, true)
          setVersionDialogOpen(false)
        } catch (err) {
          showErrorDialog("恢復失敗", err instanceof Error ? err.message : "無法恢復版本")
        } finally {
          setRestoring(false)
        }
      }
    )
  }

  // 格式化時間
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleString("zh-TW", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      })
    } catch {
      return dateString
    }
  }

  const fetchScripts = async (filters?: typeof searchFilters, forceRefresh: boolean = false) => {
    try {
      setLoading(true)
      setError(null)
      const params = {
        skip: 0,
        limit: 1000,
        // 添加强制刷新参数（如果有搜索条件则不使用缓存）
        ...(filters || searchFilters),
        // 如果强制刷新，添加时间戳参数以绕过缓存
        ...(forceRefresh ? { _t: Date.now() } : {}),
      }
      const data = await getScripts(params)
      // 确保每个script都有id字段
      const scriptsWithId = data.map(script => ({
        ...script,
        id: script.id || script.script_id,
      }))
      setScripts(scriptsWithId)
    } catch (err) {
      setError(err instanceof Error ? err.message : "加載失敗")
      showErrorDialog("加載失敗", err instanceof Error ? err.message : "無法加載劇本列表")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchScripts()
  }, [])

  const handleCreate = async () => {
    try {
      // 检查必填项，确保yaml_content不为空（包括只有空白字符的情况）
      const yamlContentTrimmed = formData.yaml_content?.trim() || ""
      if (!formData.script_id || !formData.name || !yamlContentTrimmed) {
        showErrorDialog("錯誤", `請填寫所有必填項\n\n当前状态:\n- 剧本ID: ${formData.script_id ? '✓' : '✗'}\n- 剧本名称: ${formData.name ? '✓' : '✗'}\n- YAML内容: ${yamlContentTrimmed ? '✓' : '✗'}`)
        return
      }

      // 檢查是否為舊格式，如果是則自動轉換
      const yamlContent = yamlContentTrimmed
      const isOldFormat = yamlContent.includes("step:") && 
                         yamlContent.includes("actor:") && 
                         !yamlContent.includes("script_id:")
      
      if (isOldFormat) {
        // 使用居中警告对话框
        showWarningDialog(
          "格式檢測",
          "檢測到舊格式YAML，是否自動轉換為新格式？\n\n點擊「確定」自動轉換，點擊「取消」手動轉換。",
          async () => {
            // 用户确认后执行转换
            try {
              setConverting(true)
              const result = await convertFormat({
                yaml_content: formData.yaml_content,
                script_id: formData.script_id,
                script_name: formData.name,
                optimize: false,
              })

              if (result.success) {
                // 更新表單數據
                setFormData({
                  ...formData,
                  yaml_content: result.yaml_content,
                  script_id: result.script_id || formData.script_id,
                  version: result.version || formData.version,
                  description: result.description || formData.description,
                })
                
                // 轉換後繼續創建
                await createScript({
                  ...formData,
                  yaml_content: result.yaml_content,
                  script_id: result.script_id || formData.script_id,
                  version: result.version || formData.version,
                  description: result.description || formData.description,
                })
                
                toast({
                  title: "成功",
                  description: `格式已自動轉換！共 ${result.scene_count} 個場景，劇本創建成功。`,
                })
                
                setDialogOpen(false)
                setFormData({
                  script_id: "",
                  name: "",
                  version: "1.0",
                  yaml_content: "",
                  description: "",
                })
                // 立即强制刷新列表（不使用缓存）
                await fetchScripts(undefined, true)
              } else {
                showErrorDialog("錯誤", "自動轉換失敗，請手動點擊「智能轉換」按鈕")
              }
            } catch (err) {
              const errorMsg = err instanceof Error ? err.message : "自動轉換失敗，請手動點擊「智能轉換」按鈕"
              showErrorDialog("轉換失敗", errorMsg)
            } finally {
              setConverting(false)
            }
          }
        )
        return
      }
      
      // 新格式，直接創建
      await createScript(formData)
      setDialogOpen(false)
      setFormData({
        script_id: "",
        name: "",
        version: "1.0",
        yaml_content: "",
        description: "",
      })
      // 立即强制刷新列表（不使用缓存）
      await fetchScripts(undefined, true)
      toast({
        title: "成功",
        description: "劇本創建成功",
      })
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "創建劇本失敗"
      showErrorDialog("創建失敗", errorMsg)
    }
  }

  const handleEdit = async () => {
    if (!editingScript) return

    try {
      const updateData: ScriptUpdateRequest = {
        name: formData.name,
        version: formData.version,
        yaml_content: formData.yaml_content,
        description: formData.description,
      }

      await updateScript(editingScript.id, updateData)
      toast({
        title: "成功",
        description: "劇本更新成功",
      })
      setDialogOpen(false)
      setEditingScript(null)
      setFormData({
        script_id: "",
        name: "",
        version: "1.0",
        yaml_content: "",
        description: "",
      })
      // 强制刷新列表（不使用缓存）
      fetchScripts(undefined, true)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "更新劇本失敗"
      showErrorDialog("更新失敗", errorMsg)
    }
  }

  const handleDelete = async (scriptId: string) => {
    showWarningDialog(
      "確認刪除",
      "確定要刪除這個劇本嗎？此操作無法撤銷。",
      async () => {
        try {
          await deleteScript(scriptId)
          toast({
            title: "成功",
            description: "劇本刪除成功",
          })
          // 强制刷新列表（不使用缓存）
          fetchScripts(undefined, true)
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : "刪除劇本失敗"
          showErrorDialog("刪除失敗", errorMsg)
        }
      }
    )
  }

  // 批量操作相關函數
  const toggleScriptSelect = (scriptId: string) => {
    const newSelected = new Set(selectedScripts)
    if (newSelected.has(scriptId)) {
      newSelected.delete(scriptId)
    } else {
      newSelected.add(scriptId)
    }
    setSelectedScripts(newSelected)
  }

  const toggleSelectAllScripts = () => {
    if (selectedScripts.size === scripts.length) {
      setSelectedScripts(new Set())
    } else {
      setSelectedScripts(new Set(scripts.map(s => s.script_id)))
    }
  }

  const openBatchOperationDialog = (action: "delete" | "submit_review" | "publish" | "disable" | "revert_to_draft") => {
    if (selectedScripts.size === 0) {
      showErrorDialog("錯誤", "請至少選擇一個劇本")
      return
    }
    setBatchOperation(action)
    setBatchOperationDialogOpen(true)
  }

  const handleBatchOperation = async () => {
    if (selectedScripts.size === 0) return

    try {
      setBatchOperating(true)
      const scriptIds = Array.from(selectedScripts)
      
      const request: BatchScriptRequest = {
        script_ids: scriptIds,
        action: batchOperation,
      }

      const result = await batchOperateScripts(request)

      if (result.failed_count === 0) {
        const actionText = {
          delete: "批量刪除",
          submit_review: "批量提交審核",
          publish: "批量發布",
          disable: "批量停用",
          revert_to_draft: "批量還原為草稿",
        }[batchOperation]
        
        toast({
          title: `${actionText}成功`,
          description: `成功${actionText} ${result.success_count} 個劇本`,
        })
        setSelectedScripts(new Set())
        // 强制刷新列表，不使用缓存
        await fetchScripts(undefined, true)
      } else {
        const actionText = {
          delete: "批量刪除",
          submit_review: "批量提交審核",
          publish: "批量發布",
          disable: "批量停用",
          revert_to_draft: "批量還原為草稿",
        }[batchOperation]
        
        const successMsg = result.success_count > 0
          ? `成功：${result.success_count} 個\n${result.success_ids.join(", ")}\n\n`
          : ""
        const failedMsg = `失敗：${result.failed_count} 個\n${result.failed_items.map(f => `${f.script_id}: ${f.error}`).join("\n")}`
        
        showErrorDialog(`${actionText}部分失敗`, successMsg + failedMsg)
        
        // 清除成功的選項
        const newSelected = new Set(selectedScripts)
        result.success_ids.forEach(id => newSelected.delete(id))
        setSelectedScripts(newSelected)
        
        // 強制刷新列表（不使用緩存）
        await fetchScripts(undefined, true)
        
        // 如果所有選中的都不存在，清空選擇並提示
        if (result.failed_count === selectedScripts.size && result.success_count === 0) {
          toast({
            title: "提示",
            description: "所選劇本已不存在，列表已刷新。這些劇本可能已被刪除或從未存在。",
            variant: "default",
          })
          setSelectedScripts(new Set())
        }
      }
    } catch (err) {
      const actionText = {
        delete: "批量刪除",
        submit_review: "批量提交審核",
        publish: "批量發布",
        disable: "批量停用",
        revert_to_draft: "批量還原為草稿",
      }[batchOperation]
      
      showErrorDialog(`${actionText}失敗`, err instanceof Error ? err.message : `${actionText}劇本失敗`)
    } finally {
      setBatchOperating(false)
      setBatchOperationDialogOpen(false)
    }
  }

  const handleTest = async () => {
    if (!testingScriptId || !testMessage.trim()) {
      showErrorDialog("錯誤", "請輸入測試消息")
      return
    }

    try {
      setTestLoading(true)
      const result = await testScript(testingScriptId, {
        message_text: testMessage,
      })
      setTestResult(result.reply)
    } catch (err) {
      // 正确提取错误消息
      let errorMsg = "測試失敗"
      if (err instanceof Error) {
        errorMsg = err.message
      } else if (typeof err === 'string') {
        errorMsg = err
      } else if (err && typeof err === 'object') {
        // 尝试从错误对象中提取消息
        const errorObj = err as any
        if (errorObj.detail) {
          errorMsg = errorObj.detail
        } else if (errorObj.message) {
          errorMsg = errorObj.message
        } else {
          errorMsg = JSON.stringify(err)
        }
      }
      showErrorDialog("測試失敗", errorMsg)
      setTestResult(null)
    } finally {
      setTestLoading(false)
    }
  }

  const openEditDialog = async (script: Script) => {
    try {
      const fullScript = await getScript(script.script_id)
      setEditingScript(fullScript)
      setFormData({
        script_id: fullScript.script_id,
        name: fullScript.name,
        version: fullScript.version,
        yaml_content: fullScript.yaml_content,
        description: fullScript.description || "",
      })
      setDialogOpen(true)
    } catch (err) {
      showErrorDialog("錯誤", "無法加載劇本詳情")
    }
  }

  const openTestDialog = (scriptId: string) => {
    setTestingScriptId(scriptId)
    setTestMessage("")
    setTestResult(null)
    setTestDialogOpen(true)
  }

  const handleSmartConvert = async () => {
    if (!formData.yaml_content.trim()) {
      showErrorDialog("錯誤", "請先輸入或粘貼YAML內容")
      return
    }

    try {
      setConverting(true)
      const result = await convertFormat({
        yaml_content: formData.yaml_content,
        script_id: formData.script_id || undefined,
        script_name: formData.name || undefined,
        optimize: false,
      })

      if (result.success) {
        // 更新表單數據
        setFormData({
          ...formData,
          yaml_content: result.yaml_content,
          script_id: result.script_id || formData.script_id,
          version: result.version || formData.version,
          description: result.description || formData.description,
        })

        toast({
          title: "成功",
          description: `格式轉換成功！共 ${result.scene_count} 個場景`,
        })
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "格式轉換失敗"
      showErrorDialog("轉換失敗", errorMsg)
    } finally {
      setConverting(false)
    }
  }

  const handleOptimize = async () => {
    if (!formData.yaml_content.trim()) {
      showErrorDialog("錯誤", "請先輸入YAML內容")
      return
    }

    try {
      setOptimizing(true)
      const result = await optimizeContent({
        yaml_content: formData.yaml_content,
        optimize_type: "all",
      })

      if (result.success) {
        setFormData({
          ...formData,
          yaml_content: result.yaml_content,
        })

        toast({
          title: "成功",
          description: "內容優化成功！",
        })
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "內容優化失敗"
      showErrorDialog("優化失敗", errorMsg)
    } finally {
      setOptimizing(false)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // 檢查文件大小（限制10MB）
    if (file.size > 10 * 1024 * 1024) {
      showErrorDialog("錯誤", "文件大小不能超過10MB")
      return
    }

    try {
      const text = await file.text()
      
      // 如果是YAML文件，直接讀取
      if (file.name.endsWith('.yaml') || file.name.endsWith('.yml')) {
        setFormData({
          ...formData,
          yaml_content: text,
        })
        toast({
          title: "成功",
          description: "文件上傳成功，請點擊「智能轉換」進行格式轉換",
        })
      } else {
        // 其他格式，提示用戶
        toast({
          title: "提示",
          description: "已讀取文件內容，請檢查並點擊「智能轉換」進行格式轉換",
        })
        setFormData({
          ...formData,
          yaml_content: text,
        })
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "文件讀取失敗"
      showErrorDialog("文件讀取失敗", errorMsg)
    }
  }

  // 獲取狀態顯示文本和顏色
  const getStatusDisplay = (status?: string) => {
    const statusMap: Record<string, { text: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
      draft: { text: "草稿", variant: "secondary" },
      reviewing: { text: "審核中", variant: "outline" },
      approved: { text: "已審核通過", variant: "default" },
      rejected: { text: "已拒絕", variant: "destructive" },
      published: { text: "已發布", variant: "default" },
      disabled: { text: "已停用", variant: "secondary" },
    }
    return statusMap[status || "draft"] || { text: status || "未知", variant: "secondary" as const }
  }

  // 打開審核對話框
  const openReviewDialog = (scriptId: string, action: "submit" | "approve" | "reject" | "publish" | "disable" | "revert") => {
    setReviewingScriptId(scriptId)
    setReviewAction(action)
    setReviewComment("")
    setChangeSummary("")
    setReviewDialogOpen(true)
  }

  // 處理審核操作
  const handleReview = async () => {
    if (!reviewingScriptId) return

    try {
      setReviewing(true)
      let result

      switch (reviewAction) {
        case "submit":
          result = await submitScriptReview(reviewingScriptId, { change_summary: changeSummary || undefined })
          break
        case "approve":
          result = await reviewScript(reviewingScriptId, {
            decision: "approve",
            review_comment: reviewComment || undefined,
          })
          break
        case "reject":
          result = await reviewScript(reviewingScriptId, {
            decision: "reject",
            review_comment: reviewComment || undefined,
          })
          break
        case "publish":
          result = await publishScript(reviewingScriptId, { change_summary: changeSummary || undefined })
          break
        case "disable":
          result = await disableScriptReview(reviewingScriptId)
          break
        case "revert":
          result = await revertScriptToDraft(reviewingScriptId)
          break
      }

      toast({
        title: "成功",
        description: result.message || "操作成功",
      })

      setReviewDialogOpen(false)
      // 强制刷新列表（不使用缓存）
      await fetchScripts(undefined, true)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "操作失敗"
      showErrorDialog("操作失敗", errorMsg)
    } finally {
      setReviewing(false)
    }
  }

  // 獲取可用的操作按鈕（根據狀態）
  const getAvailableActions = (script: Script) => {
    const status = script.status || "draft"
    const actions: Array<{ label: string; action: typeof reviewAction; icon: React.ReactNode; variant?: "default" | "destructive" | "outline" }> = []

    switch (status) {
      case "draft":
        actions.push({ label: "提交審核", action: "submit", icon: <Send className="h-4 w-4 mr-1" /> })
        actions.push({ label: "停用", action: "disable", icon: <EyeOff className="h-4 w-4 mr-1" /> })
        break
      case "reviewing":
        actions.push({ label: "審核通過", action: "approve", icon: <CheckCircle className="h-4 w-4 mr-1" /> })
        actions.push({ label: "審核拒絕", action: "reject", icon: <XCircle className="h-4 w-4 mr-1" />, variant: "destructive" })
        actions.push({ label: "撤回", action: "revert", icon: <RotateCcw className="h-4 w-4 mr-1" /> })
        break
      case "approved":
        actions.push({ label: "發布", action: "publish", icon: <Eye className="h-4 w-4 mr-1" /> })
        actions.push({ label: "撤回", action: "revert", icon: <RotateCcw className="h-4 w-4 mr-1" /> })
        break
      case "rejected":
        actions.push({ label: "重新提交", action: "submit", icon: <Send className="h-4 w-4 mr-1" /> })
        actions.push({ label: "撤回", action: "revert", icon: <RotateCcw className="h-4 w-4 mr-1" /> })
        break
      case "published":
        actions.push({ label: "停用", action: "disable", icon: <EyeOff className="h-4 w-4 mr-1" /> })
        actions.push({ label: "撤回", action: "revert", icon: <RotateCcw className="h-4 w-4 mr-1" /> })
        break
      case "disabled":
        actions.push({ label: "重新發布", action: "publish", icon: <Eye className="h-4 w-4 mr-1" /> })
        actions.push({ label: "撤回", action: "revert", icon: <RotateCcw className="h-4 w-4 mr-1" /> })
        break
    }

    return actions
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <StepIndicator
        currentStep={1}
        steps={workflowSteps}
        title="劇本管理"
        description="創建和管理 AI 對話劇本，這是配置系統的第一步"
        guideContent={
          <>
            <p className="font-semibold mb-2">使用指導：</p>
            <ol className="list-decimal list-inside space-y-1 text-sm">
              <li>點擊「創建劇本」按鈕創建新劇本</li>
              <li>填寫劇本 ID、名稱、版本和描述</li>
              <li>編寫 YAML 格式的劇本內容，定義對話場景和角色</li>
              <li>使用「智能轉換」功能將舊格式轉換為新格式</li>
              <li>使用「內容優化」功能優化劇本內容</li>
              <li>保存劇本後，進入 <Link href="/group-ai/accounts" className="text-primary underline">步驟 2：賬號管理</Link></li>
            </ol>
          </>
        }
      />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">劇本管理</h1>
          <p className="text-muted-foreground mt-2">管理 AI 對話劇本</p>
        </div>
        <div className="flex gap-2">
            <Button onClick={() => fetchScripts(undefined, true)} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              刷新
            </Button>
          <PermissionGuard permission="script:create">
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button onClick={() => {
                  setEditingScript(null)
                  setFormData({
                    script_id: "",
                    name: "",
                    version: "1.0",
                    yaml_content: "",
                    description: "",
                  })
                }}>
                  <Plus className="h-4 w-4 mr-2" />
                  創建劇本
                </Button>
              </DialogTrigger>
            <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{editingScript ? "編輯劇本" : "創建劇本"}</DialogTitle>
                <DialogDescription>
                  {editingScript ? "修改劇本內容" : "創建新的對話劇本"}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="script_id">劇本 ID *</Label>
                  <Input
                    id="script_id"
                    value={formData.script_id}
                    onChange={(e) => setFormData({ ...formData, script_id: e.target.value })}
                    disabled={!!editingScript}
                    placeholder="daily_chat"
                  />
                </div>
                <div>
                  <Label htmlFor="name">劇本名稱 *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="日常聊天"
                  />
                </div>
                <div>
                  <Label htmlFor="version">版本</Label>
                  <Input
                    id="version"
                    value={formData.version}
                    onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                    placeholder="1.0"
                  />
                </div>
                <div>
                  <Label htmlFor="description">描述</Label>
                  <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="劇本描述"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label htmlFor="yaml_content">YAML 內容 *</Label>
                    <div className="flex gap-2">
                      <input
                        type="file"
                        id="file-upload"
                        accept=".yaml,.yml,.txt,.md,.json"
                        onChange={handleFileUpload}
                        className="hidden"
                      />
                      <label htmlFor="file-upload">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          asChild
                        >
                          <span>
                            <Upload className="h-4 w-4 mr-1" />
                            上傳文件
                          </span>
                        </Button>
                      </label>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleSmartConvert}
                        disabled={converting || !formData.yaml_content.trim()}
                      >
                        <Sparkles className="h-4 w-4 mr-1" />
                        {converting ? "轉換中..." : "智能轉換"}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleOptimize}
                        disabled={optimizing || !formData.yaml_content.trim()}
                      >
                        <Wand2 className="h-4 w-4 mr-1" />
                        {optimizing ? "優化中..." : "內容優化"}
                      </Button>
                    </div>
                  </div>
                  <Textarea
                    id="yaml_content"
                    value={formData.yaml_content}
                    onChange={(e) => {
                      const newValue = e.target.value;
                      setFormData(prev => ({ ...prev, yaml_content: newValue }));
                    }}
                    onBlur={(e) => {
                      // 确保值被正确更新（用于浏览器自动化工具）
                      const newValue = e.target.value;
                      if (formData.yaml_content !== newValue) {
                        setFormData(prev => ({ ...prev, yaml_content: newValue }));
                      }
                    }}
                    placeholder="script_id: daily_chat&#10;version: 1.0&#10;scenes: ...&#10;&#10;或粘貼舊格式：&#10;- step: 9&#10;  actor: siya&#10;  action: speak&#10;  lines:&#10;    - 好的,那什么时候开始啊?"
                    className="font-mono text-sm"
                    rows={15}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    支持直接粘貼舊格式YAML，點擊「智能轉換」自動轉換為新格式
                  </p>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setDialogOpen(false)}>
                    取消
                  </Button>
                  <PermissionGuard permission={editingScript ? "script:update" : "script:create"}>
                    <Button onClick={editingScript ? handleEdit : handleCreate}>
                      {editingScript ? "更新" : "創建"}
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

      {/* 搜索和過濾 */}
      <div className="flex gap-4 mb-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索劇本名稱、ID或描述..."
            value={searchFilters.search || ""}
            onChange={(e) => {
              const newFilters = { ...searchFilters, search: e.target.value }
              setSearchFilters(newFilters)
              if (!e.target.value) {
                fetchScripts({ ...newFilters, search: undefined })
              }
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                fetchScripts(undefined, true)
              }
            }}
            className="pl-10"
          />
        </div>
        <Select
          value={searchFilters.status || "__all__"}
          onValueChange={(value) => {
            const newFilters = { ...searchFilters, status: value === "__all__" ? undefined : value }
            setSearchFilters(newFilters)
            fetchScripts(newFilters)
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="全部狀態" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">全部狀態</SelectItem>
            <SelectItem value="draft">草稿</SelectItem>
            <SelectItem value="reviewing">審核中</SelectItem>
            <SelectItem value="published">已發布</SelectItem>
            <SelectItem value="disabled">已停用</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={searchFilters.sort_by || "created_at"}
          onValueChange={(value) => {
            const newFilters = { ...searchFilters, sort_by: value }
            setSearchFilters(newFilters)
            fetchScripts(newFilters)
          }}
        >
          <SelectTrigger className="w-[150px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="created_at">創建時間</SelectItem>
            <SelectItem value="updated_at">更新時間</SelectItem>
            <SelectItem value="name">名稱</SelectItem>
            <SelectItem value="status">狀態</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={searchFilters.sort_order || "desc"}
          onValueChange={(value: "asc" | "desc") => {
            const newFilters = { ...searchFilters, sort_order: value }
            setSearchFilters(newFilters)
            fetchScripts(newFilters)
          }}
        >
          <SelectTrigger className="w-[120px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="desc">降序</SelectItem>
            <SelectItem value="asc">升序</SelectItem>
          </SelectContent>
        </Select>
        {(searchFilters.search || searchFilters.status) && (
          <Button
            variant="outline"
            onClick={() => {
              setSearchFilters({})
              fetchScripts({})
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
              <CardTitle>劇本列表</CardTitle>
              <CardDescription>所有已創建的對話劇本</CardDescription>
            </div>
            <PermissionGuard permission="export:script">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" disabled={loading || scripts.length === 0}>
                    <Download className="mr-2 h-4 w-4" />
                    導出
                  </Button>
                </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>選擇導出格式</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={async () => {
                    try {
                      const blob = await exportScripts("csv")
                      const filename = `劇本列表_${new Date().toISOString().slice(0, 10)}.csv`
                      downloadBlob(blob, filename)
                      toast({ title: "導出成功", description: "劇本列表已導出為 CSV" })
                    } catch (error: any) {
                      toast({
                        title: "導出失敗",
                        description: error.message || "無法導出劇本列表",
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
                      const blob = await exportScripts("excel")
                      const filename = `劇本列表_${new Date().toISOString().slice(0, 10)}.xlsx`
                      downloadBlob(blob, filename)
                      toast({ title: "導出成功", description: "劇本列表已導出為 Excel" })
                    } catch (error: any) {
                      toast({
                        title: "導出失敗",
                        description: error.message || "無法導出劇本列表",
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
                      const blob = await exportScripts("pdf")
                      const filename = `劇本列表_${new Date().toISOString().slice(0, 10)}.pdf`
                      downloadBlob(blob, filename)
                      toast({ title: "導出成功", description: "劇本列表已導出為 PDF" })
                    } catch (error: any) {
                      toast({
                        title: "導出失敗",
                        description: error.message || "無法導出劇本列表",
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
            {selectedScripts.size > 0 && (
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm text-muted-foreground">
                  已選擇 {selectedScripts.size} 個劇本
                </span>
                <PermissionGuard permission="script:delete">
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => openBatchOperationDialog("delete")}
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    批量刪除
                  </Button>
                </PermissionGuard>
                <PermissionGuard permission="script:review">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openBatchOperationDialog("submit_review")}
                  >
                    <Send className="h-4 w-4 mr-1" />
                    批量提交審核
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openBatchOperationDialog("revert_to_draft")}
                  >
                    <RotateCcw className="h-4 w-4 mr-1" />
                    批量還原為草稿
                  </Button>
                </PermissionGuard>
                <PermissionGuard permission="script:publish">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openBatchOperationDialog("publish")}
                  >
                    <CheckCircle className="h-4 w-4 mr-1" />
                    批量發布
                  </Button>
                </PermissionGuard>
                <PermissionGuard permission="script:disable">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openBatchOperationDialog("disable")}
                  >
                    <EyeOff className="h-4 w-4 mr-1" />
                    批量停用
                  </Button>
                </PermissionGuard>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedScripts(new Set())}
                >
                  取消選擇
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : scripts.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              暫無劇本，點擊「創建劇本」開始
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <div 
                      className="flex items-center justify-center cursor-pointer"
                      onClick={toggleSelectAllScripts}
                      title={selectedScripts.size === scripts.length ? "取消全選" : "全選"}
                    >
                      {selectedScripts.size === scripts.length && scripts.length > 0 ? (
                        <CheckSquare className="h-4 w-4 text-primary" />
                      ) : (
                        <SquareIcon className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>
                  </TableHead>
                  <TableHead>劇本 ID</TableHead>
                  <TableHead>名稱</TableHead>
                  <TableHead>版本</TableHead>
                  <TableHead>狀態</TableHead>
                  <TableHead>描述</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {scripts.map((script) => (
                  <TableRow key={script.id}>
                    <TableCell>
                      <div 
                        className="flex items-center justify-center cursor-pointer"
                        onClick={() => toggleScriptSelect(script.script_id)}
                        title={selectedScripts.has(script.script_id) ? "取消選擇" : "選擇"}
                      >
                        {selectedScripts.has(script.script_id) ? (
                          <CheckSquare className="h-4 w-4 text-primary" />
                        ) : (
                          <SquareIcon className="h-4 w-4 text-muted-foreground" />
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="font-medium">{script.script_id}</TableCell>
                    <TableCell>{script.name}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{script.version}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusDisplay(script.status).variant}>
                        {getStatusDisplay(script.status).text}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {script.description || "-"}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2 flex-wrap">
                        {/* 審核相關按鈕 */}
                        {getAvailableActions(script).map((action, idx) => {
                          let permission = "script:review"
                          if (action.action === "publish") permission = "script:publish"
                          if (action.action === "disable") permission = "script:disable"
                          
                          return (
                            <PermissionGuard key={idx} permission={permission}>
                              <Button
                                size="sm"
                                variant={action.variant || "outline"}
                                onClick={() => openReviewDialog(script.script_id, action.action)}
                              >
                                {action.icon}
                                {action.label}
                              </Button>
                            </PermissionGuard>
                          )
                        })}
                        {/* 其他操作按鈕 */}
                        <PermissionGuard permission="script:test">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openTestDialog(script.script_id)}
                          >
                            <Play className="h-4 w-4 mr-1" />
                            測試
                          </Button>
                        </PermissionGuard>
                        <PermissionGuard permission="script:version:view">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openVersionDialog(script.script_id)}
                          >
                            <History className="h-4 w-4 mr-1" />
                            版本
                          </Button>
                        </PermissionGuard>
                        <PermissionGuard permission="script:update">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openEditDialog(script)}
                          >
                            <Edit className="h-4 w-4 mr-1" />
                            編輯
                          </Button>
                        </PermissionGuard>
                        <PermissionGuard permission="script:delete">
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handleDelete(script.script_id)}
                          >
                            <Trash2 className="h-4 w-4 mr-1" />
                            刪除
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

      {/* 測試對話框 */}
      <Dialog open={testDialogOpen} onOpenChange={setTestDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>測試劇本</DialogTitle>
            <DialogDescription>輸入測試消息，查看劇本回復</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="test_message">測試消息</Label>
              <Input
                id="test_message"
                value={testMessage}
                onChange={(e) => setTestMessage(e.target.value)}
                placeholder="輸入測試消息..."
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault()
                    handleTest()
                  }
                }}
              />
            </div>
            {testResult && (
              <div>
                <Label>回復</Label>
                <div className="p-3 bg-muted rounded-md">
                  {testResult}
                </div>
              </div>
            )}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setTestDialogOpen(false)}>
                關閉
              </Button>
              <PermissionGuard permission="script:test">
                <Button onClick={handleTest} disabled={testLoading}>
                  {testLoading ? "測試中..." : "測試"}
                </Button>
              </PermissionGuard>
            </div>
          </div>
        </DialogContent>
      </Dialog>

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

      {/* 版本歷史對話框 */}
      <Dialog open={versionDialogOpen} onOpenChange={setVersionDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>版本歷史</DialogTitle>
            <DialogDescription>
              劇本 ID: {versionsDialogScriptId}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {/* 版本對比工具 */}
            <div className="flex gap-2 items-end pb-4 border-b">
              <div className="flex-1">
                <Label>版本 1</Label>
                <select
                  className="w-full px-3 py-2 border rounded-md"
                  value={selectedVersion1}
                  onChange={(e) => setSelectedVersion1(e.target.value)}
                >
                  <option value="">選擇版本</option>
                  {versions.map((v) => (
                    <option key={v.version} value={v.version}>
                      v{v.version} - {formatDate(v.created_at)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex-1">
                <Label>版本 2</Label>
                <select
                  className="w-full px-3 py-2 border rounded-md"
                  value={selectedVersion2}
                  onChange={(e) => setSelectedVersion2(e.target.value)}
                >
                  <option value="">選擇版本</option>
                  {versions.map((v) => (
                    <option key={v.version} value={v.version}>
                      v{v.version} - {formatDate(v.created_at)}
                    </option>
                  ))}
                </select>
              </div>
              <Button
                onClick={handleCompareVersions}
                disabled={!selectedVersion1 || !selectedVersion2 || selectedVersion1 === selectedVersion2}
              >
                <GitCompare className="h-4 w-4 mr-1" />
                對比
              </Button>
            </div>

            {/* 版本列表 */}
            {versionsLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : versions.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                暫無版本歷史
              </div>
            ) : (
              <div className="space-y-2">
                {versions.map((version) => (
                  <Card key={version.id}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary">v{version.version}</Badge>
                            <span className="text-sm text-muted-foreground">
                              {formatDate(version.created_at)}
                            </span>
                          </div>
                          {version.change_summary && (
                            <p className="text-sm mt-1 text-muted-foreground">
                              {version.change_summary}
                            </p>
                          )}
                          {version.description && (
                            <p className="text-sm mt-1">{version.description}</p>
                          )}
                          {version.created_by && (
                            <p className="text-xs mt-1 text-muted-foreground">
                              創建者: {version.created_by}
                            </p>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => viewVersionDetail(version)}
                          >
                            <FileText className="h-4 w-4 mr-1" />
                            查看
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleRestoreVersion(version)}
                            disabled={restoring}
                          >
                            <RotateCcw className="h-4 w-4 mr-1" />
                            恢復
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* 版本詳情對話框 */}
      <Dialog open={versionDetailOpen} onOpenChange={setVersionDetailOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              版本詳情 - v{selectedVersion?.version}
            </DialogTitle>
            <DialogDescription>
              創建時間: {selectedVersion ? formatDate(selectedVersion.created_at) : ""}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {selectedVersion?.change_summary && (
              <div>
                <Label>變更說明</Label>
                <p className="text-sm text-muted-foreground mt-1">
                  {selectedVersion.change_summary}
                </p>
              </div>
            )}
            <div>
              <Label>YAML 內容</Label>
              <Textarea
                value={versionContent}
                readOnly
                className="font-mono text-sm mt-1"
                rows={20}
              />
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 版本對比對話框 */}
      <Dialog open={compareDialogOpen} onOpenChange={setCompareDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>版本對比</DialogTitle>
            <DialogDescription>
              v{compareResult?.version1.version} vs v{compareResult?.version2.version}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">版本 1 (v{compareResult?.version1.version})</CardTitle>
                  <CardDescription className="text-xs">
                    {compareResult?.version1.created_at ? formatDate(compareResult.version1.created_at) : ""}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {compareResult?.version1.change_summary && (
                    <p className="text-sm text-muted-foreground">
                      {compareResult.version1.change_summary}
                    </p>
                  )}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">版本 2 (v{compareResult?.version2.version})</CardTitle>
                  <CardDescription className="text-xs">
                    {compareResult?.version2.created_at ? formatDate(compareResult.version2.created_at) : ""}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {compareResult?.version2.change_summary && (
                    <p className="text-sm text-muted-foreground">
                      {compareResult.version2.change_summary}
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
            <div>
              <Label>差異摘要</Label>
              {compareResult?.differences && compareResult.differences.length > 0 ? (
                <ul className="list-disc list-inside space-y-1 mt-2">
                  {compareResult.differences.map((diff, index) => (
                    <li key={index} className="text-sm">
                      <strong>{diff.type}:</strong> {diff.description}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground mt-2">
                  無明顯差異
                </p>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 審核與發布對話框 */}
      <Dialog open={reviewDialogOpen} onOpenChange={setReviewDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {reviewAction === "submit" && "提交審核"}
              {reviewAction === "approve" && "審核通過"}
              {reviewAction === "reject" && "審核拒絕"}
              {reviewAction === "publish" && "發布劇本"}
              {reviewAction === "disable" && "停用劇本"}
              {reviewAction === "revert" && "撤回為草稿"}
            </DialogTitle>
            <DialogDescription>
              {reviewAction === "submit" && "將劇本提交審核"}
              {reviewAction === "approve" && "審核通過此劇本"}
              {reviewAction === "reject" && "拒絕此劇本"}
              {reviewAction === "publish" && "發布劇本到生產環境"}
              {reviewAction === "disable" && "停用此劇本"}
              {reviewAction === "revert" && "撤回劇本為草稿狀態"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {(reviewAction === "submit" || reviewAction === "publish") && (
              <div>
                <Label htmlFor="change_summary">變更說明（可選）</Label>
                <Textarea
                  id="change_summary"
                  value={changeSummary}
                  onChange={(e) => setChangeSummary(e.target.value)}
                  placeholder="請描述此次變更的內容..."
                  rows={3}
                />
              </div>
            )}
            {(reviewAction === "approve" || reviewAction === "reject") && (
              <div>
                <Label htmlFor="review_comment">審核意見（可選）</Label>
                <Textarea
                  id="review_comment"
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                  placeholder="請輸入審核意見..."
                  rows={3}
                />
              </div>
            )}
            {(reviewAction === "disable" || reviewAction === "revert") && (
              <Alert>
                <AlertDescription>
                  {reviewAction === "disable" && "確定要停用此劇本嗎？停用後將無法使用。"}
                  {reviewAction === "revert" && "確定要撤回此劇本為草稿狀態嗎？"}
                </AlertDescription>
              </Alert>
            )}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setReviewDialogOpen(false)}>
                取消
              </Button>
              <PermissionGuard 
                permission={
                  reviewAction === "publish" ? "script:publish" :
                  reviewAction === "disable" ? "script:disable" :
                  "script:review"
                }
              >
                <Button onClick={handleReview} disabled={reviewing}>
                  {reviewing ? "處理中..." : "確認"}
                </Button>
              </PermissionGuard>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 批量操作確認對話框 */}
      <AlertDialog open={batchOperationDialogOpen} onOpenChange={setBatchOperationDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {{
                delete: "確認批量刪除",
                submit_review: "確認批量提交審核",
                publish: "確認批量發布",
                disable: "確認批量停用",
                revert_to_draft: "確認批量還原為草稿",
              }[batchOperation]}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {{
                delete: `確定要刪除所選的 ${selectedScripts.size} 個劇本嗎？此操作無法撤銷。`,
                submit_review: `確定要提交所選的 ${selectedScripts.size} 個劇本進行審核嗎？`,
                publish: `確定要發布所選的 ${selectedScripts.size} 個劇本嗎？`,
                disable: `確定要停用所選的 ${selectedScripts.size} 個劇本嗎？`,
                revert_to_draft: `確定要將所選的 ${selectedScripts.size} 個劇本還原為草稿嗎？`,
              }[batchOperation]}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={batchOperating}>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBatchOperation}
              disabled={batchOperating}
              className={
                batchOperation === "delete"
                  ? "bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  : ""
              }
            >
              {batchOperating ? "處理中..." : "確認"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
