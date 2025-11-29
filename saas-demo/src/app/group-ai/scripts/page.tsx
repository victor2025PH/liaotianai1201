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
    title: "剧本管理",
    description: "创建和管理 AI 对话剧本（必需）",
    href: "/group-ai/scripts",
    status: "current",
  },
  {
    number: 2,
    title: "账号管理",
    description: "创建和管理 Telegram 账号，关联剧本",
    href: "/group-ai/accounts",
    status: "pending",
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
  
  // 版本管理相關状态
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
  
  // 審核與发布相關状态
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
  
  // 批量操作相關状态
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

  // 打開版本历史对话框
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
      showErrorDialog("加载失败", err instanceof Error ? err.message : "无法加载版本历史")
    } finally {
      setVersionsLoading(false)
    }
  }

  // 查看版本详情
  const viewVersionDetail = async (version: ScriptVersion) => {
    if (!versionsDialogScriptId) return
    try {
      setSelectedVersion(version)
      const content = await getScriptVersionContent(versionsDialogScriptId, version.version)
      setVersionContent(content.yaml_content)
      setVersionDetailOpen(true)
    } catch (err) {
      showErrorDialog("加载失败", err instanceof Error ? err.message : "无法加载版本内容")
    }
  }

  // 版本对比
  const handleCompareVersions = async () => {
    if (!versionsDialogScriptId || !selectedVersion1 || !selectedVersion2) {
      showErrorDialog("参数错误", "請选择兩个版本进行对比")
      return
    }
    if (selectedVersion1 === selectedVersion2) {
      showErrorDialog("参数错误", "請选择不同的版本进行对比")
      return
    }
    try {
      const result = await compareScriptVersions(versionsDialogScriptId, selectedVersion1, selectedVersion2)
      setCompareResult(result)
      setCompareDialogOpen(true)
    } catch (err) {
      showErrorDialog("对比失败", err instanceof Error ? err.message : "无法对比版本")
    }
  }

  // 恢复版本
  const handleRestoreVersion = async (version: ScriptVersion) => {
    if (!versionsDialogScriptId) return
    showWarningDialog(
      "确认恢复版本",
      `确定要恢复剧本到版本 ${version.version} 嗎？当前版本將自动保存到历史記錄。`,
      async () => {
        try {
          setRestoring(true)
          await restoreScriptVersion(versionsDialogScriptId, version.version, {
            change_summary: `恢复到版本 ${version.version}`
          })
          toast({
            title: "恢复成功",
            description: `剧本已恢复到版本 ${version.version}`,
          })
          await fetchVersions(versionsDialogScriptId)
          // 强制刷新列表（不使用缓存）
          await fetchScripts(undefined, true)
          setVersionDialogOpen(false)
        } catch (err) {
          showErrorDialog("恢复失败", err instanceof Error ? err.message : "无法恢复版本")
        } finally {
          setRestoring(false)
        }
      }
    )
  }

  // 格式化时间
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
      setError(err instanceof Error ? err.message : "加载失败")
      showErrorDialog("加载失败", err instanceof Error ? err.message : "无法加载剧本列表")
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
        showErrorDialog("错误", `请填写所有必填项\n\n当前状态:\n- 剧本ID: ${formData.script_id ? '✓' : '✗'}\n- 剧本名称: ${formData.name ? '✓' : '✗'}\n- YAML内容: ${yamlContentTrimmed ? '✓' : '✗'}`)
        return
      }

      // 检查是否為舊格式，如果是則自动转换
      const yamlContent = yamlContentTrimmed
      const isOldFormat = yamlContent.includes("step:") && 
                         yamlContent.includes("actor:") && 
                         !yamlContent.includes("script_id:")
      
      if (isOldFormat) {
        // 使用居中警告对话框
        showWarningDialog(
          "格式检测",
          "检测到舊格式YAML，是否自动转换為新格式？\n\n点击「确定」自动转换，点击「取消」手动转换。",
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
                // 更新表單数据
                setFormData({
                  ...formData,
                  yaml_content: result.yaml_content,
                  script_id: result.script_id || formData.script_id,
                  version: result.version || formData.version,
                  description: result.description || formData.description,
                })
                
                // 转换後继续创建
                await createScript({
                  ...formData,
                  yaml_content: result.yaml_content,
                  script_id: result.script_id || formData.script_id,
                  version: result.version || formData.version,
                  description: result.description || formData.description,
                })
                
                toast({
                  title: "成功",
                  description: `格式已自动转换！共 ${result.scene_count} 个場景，剧本创建成功。`,
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
                showErrorDialog("错误", "自动转换失败，請手动点击「智能转换」按鈕")
              }
            } catch (err) {
              const errorMsg = err instanceof Error ? err.message : "自动转换失败，請手动点击「智能转换」按鈕"
              showErrorDialog("转换失败", errorMsg)
            } finally {
              setConverting(false)
            }
          }
        )
        return
      }
      
      // 新格式，直接创建
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
        description: "剧本创建成功",
      })
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "创建剧本失败"
      showErrorDialog("创建失败", errorMsg)
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
        description: "剧本更新成功",
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
      const errorMsg = err instanceof Error ? err.message : "更新剧本失败"
      showErrorDialog("更新失败", errorMsg)
    }
  }

  const handleDelete = async (scriptId: string) => {
    showWarningDialog(
      "确认删除",
      "确定要删除這个剧本嗎？此操作无法撤銷。",
      async () => {
        try {
          await deleteScript(scriptId)
          toast({
            title: "成功",
            description: "剧本删除成功",
          })
          // 强制刷新列表（不使用缓存）
          fetchScripts(undefined, true)
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : "删除剧本失败"
          showErrorDialog("删除失败", errorMsg)
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
      showErrorDialog("错误", "請至少选择一个剧本")
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
          delete: "批量删除",
          submit_review: "批量提交审核",
          publish: "批量发布",
          disable: "批量停用",
          revert_to_draft: "批量还原為草稿",
        }[batchOperation]
        
        toast({
          title: `${actionText}成功`,
          description: `成功${actionText} ${result.success_count} 个剧本`,
        })
        setSelectedScripts(new Set())
        // 强制刷新列表，不使用缓存
        await fetchScripts(undefined, true)
      } else {
        const actionText = {
          delete: "批量删除",
          submit_review: "批量提交审核",
          publish: "批量发布",
          disable: "批量停用",
          revert_to_draft: "批量还原為草稿",
        }[batchOperation]
        
        const successMsg = result.success_count > 0
          ? `成功：${result.success_count} 个\n${result.success_ids.join(", ")}\n\n`
          : ""
        const failedMsg = `失败：${result.failed_count} 个\n${result.failed_items.map(f => `${f.script_id}: ${f.error}`).join("\n")}`
        
        showErrorDialog(`${actionText}部分失败`, successMsg + failedMsg)
        
        // 清除成功的选项
        const newSelected = new Set(selectedScripts)
        result.success_ids.forEach(id => newSelected.delete(id))
        setSelectedScripts(newSelected)
        
        // 強制刷新列表（不使用緩存）
        await fetchScripts(undefined, true)
        
        // 如果所有選中的都不存在，清空选择並提示
        if (result.failed_count === selectedScripts.size && result.success_count === 0) {
          toast({
            title: "提示",
            description: "所選剧本已不存在，列表已刷新。這些剧本可能已被删除或從未存在。",
            variant: "default",
          })
          setSelectedScripts(new Set())
        }
      }
    } catch (err) {
      const actionText = {
        delete: "批量删除",
        submit_review: "批量提交审核",
        publish: "批量发布",
        disable: "批量停用",
        revert_to_draft: "批量还原為草稿",
      }[batchOperation]
      
      showErrorDialog(`${actionText}失败`, err instanceof Error ? err.message : `${actionText}剧本失败`)
    } finally {
      setBatchOperating(false)
      setBatchOperationDialogOpen(false)
    }
  }

  const handleTest = async () => {
    if (!testingScriptId || !testMessage.trim()) {
      showErrorDialog("错误", "请输入测试消息")
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
      let errorMsg = "测试失败"
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
      showErrorDialog("测试失败", errorMsg)
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
      showErrorDialog("错误", "无法加载剧本详情")
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
      showErrorDialog("错误", "請先输入或粘贴YAML内容")
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
        // 更新表單数据
        setFormData({
          ...formData,
          yaml_content: result.yaml_content,
          script_id: result.script_id || formData.script_id,
          version: result.version || formData.version,
          description: result.description || formData.description,
        })

        toast({
          title: "成功",
          description: `格式转换成功！共 ${result.scene_count} 个場景`,
        })
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "格式转换失败"
      showErrorDialog("转换失败", errorMsg)
    } finally {
      setConverting(false)
    }
  }

  const handleOptimize = async () => {
    if (!formData.yaml_content.trim()) {
      showErrorDialog("错误", "請先输入YAML内容")
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
          description: "内容优化成功！",
        })
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "内容优化失败"
      showErrorDialog("优化失败", errorMsg)
    } finally {
      setOptimizing(false)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // 检查文件大小（限制10MB）
    if (file.size > 10 * 1024 * 1024) {
      showErrorDialog("错误", "文件大小不能超過10MB")
      return
    }

    try {
      const text = await file.text()
      
      // 如果是YAML文件，直接读取
      if (file.name.endsWith('.yaml') || file.name.endsWith('.yml')) {
        setFormData({
          ...formData,
          yaml_content: text,
        })
        toast({
          title: "成功",
          description: "文件上傳成功，請点击「智能转换」进行格式转换",
        })
      } else {
        // 其他格式，提示用户
        toast({
          title: "提示",
          description: "已读取文件内容，請检查並点击「智能转换」进行格式转换",
        })
        setFormData({
          ...formData,
          yaml_content: text,
        })
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "文件读取失败"
      showErrorDialog("文件读取失败", errorMsg)
    }
  }

  // 獲取状态顯示文本和顏色
  const getStatusDisplay = (status?: string) => {
    const statusMap: Record<string, { text: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
      draft: { text: "草稿", variant: "secondary" },
      reviewing: { text: "审核中", variant: "outline" },
      approved: { text: "已审核通过", variant: "default" },
      rejected: { text: "已拒绝", variant: "destructive" },
      published: { text: "已发布", variant: "default" },
      disabled: { text: "已停用", variant: "secondary" },
    }
    return statusMap[status || "draft"] || { text: status || "未知", variant: "secondary" as const }
  }

  // 打開審核对话框
  const openReviewDialog = (scriptId: string, action: "submit" | "approve" | "reject" | "publish" | "disable" | "revert") => {
    setReviewingScriptId(scriptId)
    setReviewAction(action)
    setReviewComment("")
    setChangeSummary("")
    setReviewDialogOpen(true)
  }

  // 处理審核操作
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
      const errorMsg = err instanceof Error ? err.message : "操作失败"
      showErrorDialog("操作失败", errorMsg)
    } finally {
      setReviewing(false)
    }
  }

  // 獲取可用的操作按鈕（根據状态）
  const getAvailableActions = (script: Script) => {
    const status = script.status || "draft"
    const actions: Array<{ label: string; action: typeof reviewAction; icon: React.ReactNode; variant?: "default" | "destructive" | "outline" }> = []

    switch (status) {
      case "draft":
        actions.push({ label: "提交审核", action: "submit", icon: <Send className="h-4 w-4 mr-1" /> })
        actions.push({ label: "停用", action: "disable", icon: <EyeOff className="h-4 w-4 mr-1" /> })
        break
      case "reviewing":
        actions.push({ label: "审核通过", action: "approve", icon: <CheckCircle className="h-4 w-4 mr-1" /> })
        actions.push({ label: "审核拒绝", action: "reject", icon: <XCircle className="h-4 w-4 mr-1" />, variant: "destructive" })
        actions.push({ label: "撤回", action: "revert", icon: <RotateCcw className="h-4 w-4 mr-1" /> })
        break
      case "approved":
        actions.push({ label: "发布", action: "publish", icon: <Eye className="h-4 w-4 mr-1" /> })
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
        actions.push({ label: "重新发布", action: "publish", icon: <Eye className="h-4 w-4 mr-1" /> })
        actions.push({ label: "撤回", action: "revert", icon: <RotateCcw className="h-4 w-4 mr-1" /> })
        break
    }

    return actions
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <StepIndicator currentStep={1} steps={workflowSteps} />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">剧本管理</h1>
          <p className="text-muted-foreground mt-2">管理 AI 对话剧本</p>
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
                  创建剧本
                </Button>
              </DialogTrigger>
            <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{editingScript ? "编辑剧本" : "创建剧本"}</DialogTitle>
                <DialogDescription>
                  {editingScript ? "修改剧本内容" : "创建新的对话剧本"}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="script_id">剧本 ID *</Label>
                  <Input
                    id="script_id"
                    value={formData.script_id}
                    onChange={(e) => setFormData({ ...formData, script_id: e.target.value })}
                    disabled={!!editingScript}
                    placeholder="daily_chat"
                  />
                </div>
                <div>
                  <Label htmlFor="name">剧本名稱 *</Label>
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
                    placeholder="剧本描述"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label htmlFor="yaml_content">YAML 内容 *</Label>
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
                            上传文件
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
                        {converting ? "转换中..." : "智能转换"}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleOptimize}
                        disabled={optimizing || !formData.yaml_content.trim()}
                      >
                        <Wand2 className="h-4 w-4 mr-1" />
                        {optimizing ? "优化中..." : "内容优化"}
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
                    placeholder="script_id: daily_chat&#10;version: 1.0&#10;scenes: ...&#10;&#10;或粘贴舊格式：&#10;- step: 9&#10;  actor: siya&#10;  action: speak&#10;  lines:&#10;    - 好的,那什么时候开始啊?"
                    className="font-mono text-sm"
                    rows={15}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    支持直接粘贴舊格式YAML，点击「智能转换」自动转换為新格式
                  </p>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setDialogOpen(false)}>
                    取消
                  </Button>
                  <PermissionGuard permission={editingScript ? "script:update" : "script:create"}>
                    <Button onClick={editingScript ? handleEdit : handleCreate}>
                      {editingScript ? "更新" : "创建"}
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
            placeholder="搜索剧本名稱、ID或描述..."
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
            <SelectValue placeholder="全部状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">全部状态</SelectItem>
            <SelectItem value="draft">草稿</SelectItem>
            <SelectItem value="reviewing">审核中</SelectItem>
            <SelectItem value="published">已发布</SelectItem>
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
            <SelectItem value="created_at">创建时间</SelectItem>
            <SelectItem value="updated_at">更新时间</SelectItem>
            <SelectItem value="name">名稱</SelectItem>
            <SelectItem value="status">状态</SelectItem>
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
              <CardTitle>剧本列表</CardTitle>
              <CardDescription>所有已创建的对话剧本</CardDescription>
            </div>
            <PermissionGuard permission="export:script">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" disabled={loading || scripts.length === 0}>
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
                      const blob = await exportScripts("csv")
                      const filename = `剧本列表_${new Date().toISOString().slice(0, 10)}.csv`
                      downloadBlob(blob, filename)
                      toast({ title: "导出成功", description: "剧本列表已导出為 CSV" })
                    } catch (error: any) {
                      toast({
                        title: "导出失败",
                        description: error.message || "无法导出剧本列表",
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
                      const filename = `剧本列表_${new Date().toISOString().slice(0, 10)}.xlsx`
                      downloadBlob(blob, filename)
                      toast({ title: "导出成功", description: "剧本列表已导出為 Excel" })
                    } catch (error: any) {
                      toast({
                        title: "导出失败",
                        description: error.message || "无法导出剧本列表",
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
                      const filename = `剧本列表_${new Date().toISOString().slice(0, 10)}.pdf`
                      downloadBlob(blob, filename)
                      toast({ title: "导出成功", description: "剧本列表已导出為 PDF" })
                    } catch (error: any) {
                      toast({
                        title: "导出失败",
                        description: error.message || "无法导出剧本列表",
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
                  已选择 {selectedScripts.size} 个剧本
                </span>
                <PermissionGuard permission="script:delete">
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => openBatchOperationDialog("delete")}
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    批量删除
                  </Button>
                </PermissionGuard>
                <PermissionGuard permission="script:review">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openBatchOperationDialog("submit_review")}
                  >
                    <Send className="h-4 w-4 mr-1" />
                    批量提交审核
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openBatchOperationDialog("revert_to_draft")}
                  >
                    <RotateCcw className="h-4 w-4 mr-1" />
                    批量还原為草稿
                  </Button>
                </PermissionGuard>
                <PermissionGuard permission="script:publish">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openBatchOperationDialog("publish")}
                  >
                    <CheckCircle className="h-4 w-4 mr-1" />
                    批量发布
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
                  取消选择
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
              暫无剧本，点击「创建剧本」开始
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <div 
                      className="flex items-center justify-center cursor-pointer"
                      onClick={toggleSelectAllScripts}
                      title={selectedScripts.size === scripts.length ? "取消全选" : "全选"}
                    >
                      {selectedScripts.size === scripts.length && scripts.length > 0 ? (
                        <CheckSquare className="h-4 w-4 text-primary" />
                      ) : (
                        <SquareIcon className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>
                  </TableHead>
                  <TableHead>剧本 ID</TableHead>
                  <TableHead>名稱</TableHead>
                  <TableHead>版本</TableHead>
                  <TableHead>状态</TableHead>
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
                        title={selectedScripts.has(script.script_id) ? "取消选择" : "选择"}
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
                            测试
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
                            编辑
                          </Button>
                        </PermissionGuard>
                        <PermissionGuard permission="script:delete">
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handleDelete(script.script_id)}
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

      {/* 测试对话框 */}
      <Dialog open={testDialogOpen} onOpenChange={setTestDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>测试剧本</DialogTitle>
            <DialogDescription>输入测试消息，查看剧本回复</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="test_message">测试消息</Label>
              <Input
                id="test_message"
                value={testMessage}
                onChange={(e) => setTestMessage(e.target.value)}
                placeholder="输入测试消息..."
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
                <Label>回复</Label>
                <div className="p-3 bg-muted rounded-md">
                  {testResult}
                </div>
              </div>
            )}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setTestDialogOpen(false)}>
                关闭
              </Button>
              <PermissionGuard permission="script:test">
                <Button onClick={handleTest} disabled={testLoading}>
                  {testLoading ? "测试中..." : "测试"}
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

      {/* 版本历史对话框 */}
      <Dialog open={versionDialogOpen} onOpenChange={setVersionDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>版本历史</DialogTitle>
            <DialogDescription>
              剧本 ID: {versionsDialogScriptId}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {/* 版本对比工具 */}
            <div className="flex gap-2 items-end pb-4 border-b">
              <div className="flex-1">
                <Label>版本 1</Label>
                <select
                  className="w-full px-3 py-2 border rounded-md"
                  value={selectedVersion1}
                  onChange={(e) => setSelectedVersion1(e.target.value)}
                >
                  <option value="">选择版本</option>
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
                  <option value="">选择版本</option>
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
                对比
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
                暫无版本历史
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
                              创建者: {version.created_by}
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
                            恢复
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

      {/* 版本详情对话框 */}
      <Dialog open={versionDetailOpen} onOpenChange={setVersionDetailOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              版本详情 - v{selectedVersion?.version}
            </DialogTitle>
            <DialogDescription>
              创建时间: {selectedVersion ? formatDate(selectedVersion.created_at) : ""}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {selectedVersion?.change_summary && (
              <div>
                <Label>变更说明</Label>
                <p className="text-sm text-muted-foreground mt-1">
                  {selectedVersion.change_summary}
                </p>
              </div>
            )}
            <div>
              <Label>YAML 内容</Label>
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

      {/* 版本对比对话框 */}
      <Dialog open={compareDialogOpen} onOpenChange={setCompareDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>版本对比</DialogTitle>
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
                  无明顯差異
                </p>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 審核與发布对话框 */}
      <Dialog open={reviewDialogOpen} onOpenChange={setReviewDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {reviewAction === "submit" && "提交审核"}
              {reviewAction === "approve" && "审核通过"}
              {reviewAction === "reject" && "审核拒绝"}
              {reviewAction === "publish" && "发布剧本"}
              {reviewAction === "disable" && "停用剧本"}
              {reviewAction === "revert" && "撤回为草稿"}
            </DialogTitle>
            <DialogDescription>
              {reviewAction === "submit" && "將剧本提交审核"}
              {reviewAction === "approve" && "审核通过此剧本"}
              {reviewAction === "reject" && "拒絕此剧本"}
              {reviewAction === "publish" && "发布剧本到生產环境"}
              {reviewAction === "disable" && "停用此剧本"}
              {reviewAction === "revert" && "撤回剧本為草稿状态"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {(reviewAction === "submit" || reviewAction === "publish") && (
              <div>
                <Label htmlFor="change_summary">变更说明（可选）</Label>
                <Textarea
                  id="change_summary"
                  value={changeSummary}
                  onChange={(e) => setChangeSummary(e.target.value)}
                  placeholder="請描述此次變更的内容..."
                  rows={3}
                />
              </div>
            )}
            {(reviewAction === "approve" || reviewAction === "reject") && (
              <div>
                <Label htmlFor="review_comment">审核意见（可选）</Label>
                <Textarea
                  id="review_comment"
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                  placeholder="请输入审核意见..."
                  rows={3}
                />
              </div>
            )}
            {(reviewAction === "disable" || reviewAction === "revert") && (
              <Alert>
                <AlertDescription>
                  {reviewAction === "disable" && "确定要停用此剧本嗎？停用後將无法使用。"}
                  {reviewAction === "revert" && "确定要撤回此剧本為草稿状态嗎？"}
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
                  {reviewing ? "处理中..." : "确认"}
                </Button>
              </PermissionGuard>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 批量操作确认对话框 */}
      <AlertDialog open={batchOperationDialogOpen} onOpenChange={setBatchOperationDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {{
                delete: "确认批量删除",
                submit_review: "确认批量提交审核",
                publish: "确认批量发布",
                disable: "确认批量停用",
                revert_to_draft: "确认批量还原為草稿",
              }[batchOperation]}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {{
                delete: `确定要删除所選的 ${selectedScripts.size} 个剧本嗎？此操作无法撤銷。`,
                submit_review: `确定要提交所選的 ${selectedScripts.size} 个剧本进行審核嗎？`,
                publish: `确定要发布所選的 ${selectedScripts.size} 个剧本嗎？`,
                disable: `确定要停用所選的 ${selectedScripts.size} 个剧本嗎？`,
                revert_to_draft: `确定要將所選的 ${selectedScripts.size} 个剧本还原為草稿嗎？`,
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
              {batchOperating ? "处理中..." : "确认"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
