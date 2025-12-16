"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { useToast } from "@/hooks/use-toast"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import {
  Upload, Download, Trash2, RefreshCw, File, Loader2,
  AlertCircle, CheckCircle2
} from "lucide-react"
import { getApiBaseUrl } from "@/lib/api/config"
import { Checkbox } from "@/components/ui/checkbox"

const API_BASE = getApiBaseUrl()

interface SessionFile {
  filename: string
  size: number
  modified_time?: string
  path?: string
}

interface WorkerSessionManagerProps {
  workerId: string
  workerName?: string
}

export function WorkerSessionManager({ workerId, workerName }: WorkerSessionManagerProps) {
  const { toast } = useToast()
  const [sessions, setSessions] = useState<SessionFile[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [fileToDelete, setFileToDelete] = useState<string | null>(null)
  const [batchDeleteDialogOpen, setBatchDeleteDialogOpen] = useState(false)

  const fetchSessions = async () => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/workers/${workerId}/sessions?timeout=30`)
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      
      const data = await res.json()
      setSessions(data.sessions || [])
    } catch (error: any) {
      console.error("获取 Session 列表失败:", error)
      toast({
        title: "获取失败",
        description: error.message || "无法获取 Session 文件列表",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (workerId) {
      fetchSessions()
    }
  }, [workerId])

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    setUploading(true)
    const { fetchWithAuth } = await import("@/lib/api/client")

    try {
      for (const file of Array.from(files)) {
        if (!file.name.endsWith('.session')) {
          toast({
            title: "文件格式错误",
            description: `${file.name} 不是 .session 文件`,
            variant: "destructive"
          })
          continue
        }

        const formData = new FormData()
        formData.append('file', file)

        const res = await fetchWithAuth(`${API_BASE}/workers/${workerId}/sessions/upload?timeout=60`, {
          method: 'POST',
          body: formData
        })

        if (!res.ok) {
          const error = await res.json()
          throw new Error(error.detail || `HTTP ${res.status}`)
        }

        const data = await res.json()
        toast({
          title: "上传成功",
          description: `${file.name} 已上传到节点 ${workerId}`
        })
      }

      // 刷新列表
      await fetchSessions()
    } catch (error: any) {
      toast({
        title: "上传失败",
        description: error.message || "上传 Session 文件失败",
        variant: "destructive"
      })
    } finally {
      setUploading(false)
      // 清空文件选择
      event.target.value = ''
    }
  }

  const handleDownload = async (filename: string) => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/workers/${workerId}/sessions/${encodeURIComponent(filename)}/download?timeout=30`)
      
      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || `HTTP ${res.status}`)
      }

      const data = await res.json()
      
      // 解码 base64
      const binaryString = atob(data.file_content)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      
      // 创建 Blob 并下载
      const blob = new Blob([bytes], { type: 'application/octet-stream' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast({
        title: "下载成功",
        description: `${filename} 已下载`
      })
    } catch (error: any) {
      toast({
        title: "下载失败",
        description: error.message || "下载 Session 文件失败",
        variant: "destructive"
      })
    }
  }

  const handleDelete = async (filename: string) => {
    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/workers/${workerId}/sessions/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
      })
      
      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || `HTTP ${res.status}`)
      }

      toast({
        title: "删除成功",
        description: `${filename} 已删除`
      })

      // 刷新列表
      await fetchSessions()
      setDeleteDialogOpen(false)
      setFileToDelete(null)
    } catch (error: any) {
      toast({
        title: "删除失败",
        description: error.message || "删除 Session 文件失败",
        variant: "destructive"
      })
    }
  }

  const handleBatchDownload = async () => {
    if (selectedFiles.size === 0) {
      toast({
        title: "请选择文件",
        description: "请至少选择一个文件进行下载",
        variant: "destructive"
      })
      return
    }

    try {
      for (const filename of selectedFiles) {
        await handleDownload(filename)
        // 添加小延迟避免并发过多
        await new Promise(resolve => setTimeout(resolve, 500))
      }
      
      toast({
        title: "批量下载完成",
        description: `已下载 ${selectedFiles.size} 个文件`
      })
      
      setSelectedFiles(new Set())
    } catch (error: any) {
      toast({
        title: "批量下载失败",
        description: error.message || "批量下载失败",
        variant: "destructive"
      })
    }
  }

  const handleBatchDelete = async () => {
    if (selectedFiles.size === 0) {
      toast({
        title: "请选择文件",
        description: "请至少选择一个文件进行删除",
        variant: "destructive"
      })
      return
    }

    try {
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/workers/${workerId}/sessions/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filenames: Array.from(selectedFiles),
          operation: 'delete'
        })
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || `HTTP ${res.status}`)
      }

      const data = await res.json()
      
      toast({
        title: "批量删除完成",
        description: `成功删除 ${data.successful} 个文件，失败 ${data.failed} 个`
      })

      // 刷新列表
      await fetchSessions()
      setSelectedFiles(new Set())
      setBatchDeleteDialogOpen(false)
    } catch (error: any) {
      toast({
        title: "批量删除失败",
        description: error.message || "批量删除失败",
        variant: "destructive"
      })
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-'
    try {
      return new Date(dateString).toLocaleString('zh-CN')
    } catch {
      return dateString
    }
  }

  const toggleFileSelection = (filename: string) => {
    const newSelected = new Set(selectedFiles)
    if (newSelected.has(filename)) {
      newSelected.delete(filename)
    } else {
      newSelected.add(filename)
    }
    setSelectedFiles(newSelected)
  }

  const toggleSelectAll = () => {
    if (selectedFiles.size === sessions.length) {
      setSelectedFiles(new Set())
    } else {
      setSelectedFiles(new Set(sessions.map(s => s.filename)))
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Session 文件管理</CardTitle>
            <CardDescription>
              {workerName ? `管理节点 ${workerName} 的 Session 文件` : `管理节点 ${workerId} 的 Session 文件`}
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchSessions}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
            <label>
              <Button
                variant="default"
                size="sm"
                asChild
                disabled={uploading}
              >
                <span>
                  <Upload className="h-4 w-4 mr-2" />
                  {uploading ? '上传中...' : '上传文件'}
                </span>
              </Button>
              <Input
                type="file"
                accept=".session"
                multiple
                onChange={handleUpload}
                className="hidden"
                disabled={uploading}
              />
            </label>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin mr-2" />
            <span>加载中...</span>
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <File className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>暂无 Session 文件</p>
            <p className="text-sm mt-2">点击"上传文件"按钮添加 Session 文件</p>
          </div>
        ) : (
          <>
            {selectedFiles.size > 0 && (
              <div className="mb-4 p-3 bg-muted rounded-lg flex items-center justify-between">
                <span className="text-sm">
                  已选择 {selectedFiles.size} 个文件
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleBatchDownload}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    批量下载
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => setBatchDeleteDialogOpen(true)}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    批量删除
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedFiles(new Set())}
                  >
                    取消选择
                  </Button>
                </div>
              </div>
            )}
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={selectedFiles.size === sessions.length && sessions.length > 0}
                        onCheckedChange={toggleSelectAll}
                      />
                    </TableHead>
                    <TableHead>文件名</TableHead>
                    <TableHead>大小</TableHead>
                    <TableHead>修改时间</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sessions.map((session) => (
                    <TableRow key={session.filename}>
                      <TableCell>
                        <Checkbox
                          checked={selectedFiles.has(session.filename)}
                          onCheckedChange={() => toggleFileSelection(session.filename)}
                        />
                      </TableCell>
                      <TableCell className="font-medium">{session.filename}</TableCell>
                      <TableCell>{formatFileSize(session.size)}</TableCell>
                      <TableCell>{formatDate(session.modified_time)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDownload(session.filename)}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setFileToDelete(session.filename)
                              setDeleteDialogOpen(true)
                            }}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="mt-4 text-sm text-muted-foreground">
              共 {sessions.length} 个文件
            </div>
          </>
        )}

        {/* 删除确认对话框 */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>确认删除</AlertDialogTitle>
              <AlertDialogDescription>
                确定要删除文件 <strong>{fileToDelete}</strong> 吗？此操作无法撤销。
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>取消</AlertDialogCancel>
              <AlertDialogAction
                onClick={() => fileToDelete && handleDelete(fileToDelete)}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                删除
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* 批量删除确认对话框 */}
        <AlertDialog open={batchDeleteDialogOpen} onOpenChange={setBatchDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>确认批量删除</AlertDialogTitle>
              <AlertDialogDescription>
                确定要删除选中的 {selectedFiles.size} 个文件吗？此操作无法撤销。
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>取消</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleBatchDelete}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                删除
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </CardContent>
    </Card>
  )
}

