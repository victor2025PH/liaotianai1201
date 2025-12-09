"use client"

import { useState, useMemo, Suspense } from "react"
import dynamic from "next/dynamic"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useToast } from "@/hooks/use-toast"
import { useLogs } from "@/hooks/useLogs"
import { FileText, Search, Download, Eye, RefreshCw, AlertCircle, AlertTriangle, Info } from "lucide-react"
import { LogEntry } from "@/lib/api"
import { mockLogs } from "@/mock/logs"

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
const Dialog = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.Dialog })), { ssr: false })
const DialogContent = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogContent })), { ssr: false })
const DialogDescription = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogDescription })), { ssr: false })
const DialogHeader = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogHeader })), { ssr: false })
const DialogTitle = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogTitle })), { ssr: false })

// 格式化时间戳
const formatTimestamp = (timestamp: string): string => {
  try {
    const date = new Date(timestamp)
    return date.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    })
  } catch {
    return timestamp
  }
}

// 获取日志级别图标
const getLevelIcon = (level: string) => {
  switch (level.toLowerCase()) {
    case "error":
      return <AlertCircle className="h-4 w-4" />
    case "warning":
      return <AlertTriangle className="h-4 w-4" />
    case "info":
      return <Info className="h-4 w-4" />
    default:
      return <Info className="h-4 w-4" />
  }
}

// 获取日志级别颜色
const getLevelVariant = (level: string): "destructive" | "default" | "secondary" | "outline" => {
  switch (level.toLowerCase()) {
    case "error":
      return "destructive"
    case "warning":
      return "default"
    case "info":
      return "secondary"
    default:
      return "outline"
  }
}

// 获取日志级别标签
const getLevelLabel = (level: string): string => {
  switch (level.toLowerCase()) {
    case "error":
      return "错误"
    case "warning":
      return "警告"
    case "info":
      return "信息"
    default:
      return level
  }
}

// 导出为 CSV
const exportToCSV = (logs: LogEntry[], filename: string = "logs.csv") => {
  const headers = ["时间戳", "级别", "来源", "消息", "类型", "严重性"]
  const rows = logs.map((log) => [
    formatTimestamp(log.timestamp),
    getLevelLabel(log.level),
    log.source || "系统",
    log.message,
    log.type || "-",
    log.severity || "-",
  ])

  const csvContent = [
    headers.join(","),
    ...rows.map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(",")),
  ].join("\n")

  const blob = new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" })
  const link = document.createElement("a")
  const url = URL.createObjectURL(blob)
  link.setAttribute("href", url)
  link.setAttribute("download", filename)
  link.style.visibility = "hidden"
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

export default function LogsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedLevel, setSelectedLevel] = useState<"error" | "warning" | "info" | undefined>(undefined)
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null)
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false)
  const [useMockData, setUseMockData] = useState(false)
  const { toast } = useToast()

  // 使用 useLogs hook
  const {
    data,
    loading,
    error,
    isMock,
    refetch,
    page,
    pageSize,
    level,
    setPage,
    setPageSize,
    setLevel,
  } = useLogs(1, 20, selectedLevel, searchQuery || undefined)

  // 如果 API 失败，使用 mock 数据
  const logs = useMemo(() => {
    if (useMockData || (data && data.items.length === 0 && error)) {
      return mockLogs
    }
    return data?.items || []
  }, [data, error, useMockData])

  const total = data?.total || logs.length
  const isUsingMock = useMockData || isMock || (data && data.items.length === 0 && error)

  // 过滤日志（客户端过滤，用于 mock 数据）
  const filteredLogs = useMemo(() => {
    let filtered = logs

    // 按级别过滤
    if (selectedLevel) {
      filtered = filtered.filter((log) => log.level.toLowerCase() === selectedLevel.toLowerCase())
    }

    // 按搜索关键词过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(
        (log) =>
          log.message.toLowerCase().includes(query) ||
          log.source?.toLowerCase().includes(query) ||
          log.type?.toLowerCase().includes(query) ||
          log.logger?.toLowerCase().includes(query)
      )
    }

    return filtered
  }, [logs, selectedLevel, searchQuery])

  // 处理级别筛选
  const handleLevelChange = (value: string) => {
    if (value === "all") {
      setSelectedLevel(undefined)
      setLevel(undefined)
    } else {
      setSelectedLevel(value as "error" | "warning" | "info")
      setLevel(value as "error" | "warning" | "info")
    }
    setPage(1)
  }

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchQuery(value)
    setPage(1)
  }

  // 处理导出
  const handleExport = () => {
    try {
      const logsToExport = filteredLogs.length > 0 ? filteredLogs : logs
      exportToCSV(logsToExport, `logs-${new Date().toISOString().split("T")[0]}.csv`)
      toast({
        title: "导出成功",
        description: `已导出 ${logsToExport.length} 条日志`,
      })
    } catch (err) {
      toast({
        title: "导出失败",
        description: err instanceof Error ? err.message : "导出日志时发生错误",
        variant: "destructive",
      })
    }
  }

  // 查看详情
  const handleViewDetail = (log: LogEntry) => {
    setSelectedLog(log)
    setIsDetailDialogOpen(true)
  }

  // 计算分页
  const totalPages = Math.ceil(total / pageSize)
  const startIndex = (page - 1) * pageSize
  const endIndex = startIndex + pageSize
  const paginatedLogs = filteredLogs.slice(startIndex, endIndex)

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-6 w-6" />
          <h1 className="text-3xl font-bold">日志管理</h1>
        </div>
        {isUsingMock && (
          <Badge variant="outline" className="text-yellow-600 border-yellow-600">
            使用 Mock 数据
          </Badge>
        )}
      </div>

      {/* 搜索和筛选卡片 */}
      <Card>
        <CardHeader>
          <CardTitle>搜索与筛选</CardTitle>
          <CardDescription>按关键词、级别筛选日志</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4">
            {/* 搜索框 */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="搜索日志（消息、来源、类型...）"
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* 级别筛选 */}
            <Select value={selectedLevel || "all"} onValueChange={handleLevelChange}>
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="选择级别" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有级别</SelectItem>
                <SelectItem value="error">仅错误</SelectItem>
                <SelectItem value="warning">仅警告</SelectItem>
                <SelectItem value="info">仅信息</SelectItem>
              </SelectContent>
            </Select>

            {/* 操作按钮 */}
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => refetch()}
                disabled={loading}
                className="flex items-center gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                刷新
              </Button>
              <Button
                onClick={handleExport}
                className="flex items-center gap-2"
                disabled={filteredLogs.length === 0}
              >
                <Download className="h-4 w-4" />
                导出 CSV
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 日志表格 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>日志列表</CardTitle>
              <CardDescription>
                共 {total} 条日志
                {selectedLevel && `（已筛选：${getLevelLabel(selectedLevel)}）`}
                {searchQuery && `（搜索：${searchQuery}）`}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-muted-foreground">加载中...</span>
            </div>
          ) : error && !isUsingMock ? (
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <AlertCircle className="h-12 w-12 text-destructive" />
              <div className="text-center">
                <p className="text-lg font-semibold">加载日志失败</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {error.message || "无法连接到后端服务"}
                </p>
                <Button
                  variant="outline"
                  onClick={() => {
                    setUseMockData(true)
                    toast({
                      title: "已切换到 Mock 数据",
                      description: "使用模拟数据进行演示",
                    })
                  }}
                  className="mt-4"
                >
                  使用 Mock 数据
                </Button>
              </div>
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <FileText className="h-12 w-12 text-muted-foreground" />
              <div className="text-center">
                <p className="text-lg font-semibold">暂无日志</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {searchQuery || selectedLevel
                    ? "请尝试调整筛选条件"
                    : "系统暂无日志记录"}
                </p>
              </div>
            </div>
          ) : (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[180px]">时间戳</TableHead>
                      <TableHead className="w-[100px]">级别</TableHead>
                      <TableHead className="w-[150px]">来源</TableHead>
                      <TableHead>消息</TableHead>
                      <TableHead className="w-[100px]">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginatedLogs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell className="font-mono text-sm">
                          {formatTimestamp(log.timestamp)}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={getLevelVariant(log.level)}
                            className="flex items-center gap-1 w-fit"
                          >
                            {getLevelIcon(log.level)}
                            {getLevelLabel(log.level)}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col">
                            <span className="text-sm font-medium">
                              {log.source || log.logger || "系统"}
                            </span>
                            {log.type && (
                              <span className="text-xs text-muted-foreground">{log.type}</span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="max-w-md">
                            <p className="text-sm line-clamp-2">{log.message}</p>
                            {log.severity && (
                              <Badge variant="outline" className="mt-1 text-xs">
                                {log.severity === "high"
                                  ? "高"
                                  : log.severity === "medium"
                                  ? "中"
                                  : "低"}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewDetail(log)}
                            className="flex items-center gap-1"
                          >
                            <Eye className="h-4 w-4" />
                            详情
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* 分页 */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <div className="text-sm text-muted-foreground">
                    显示 {startIndex + 1} - {Math.min(endIndex, total)} 条，共 {total} 条
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(page - 1)}
                      disabled={page === 1}
                    >
                      上一页
                    </Button>
                    <div className="text-sm">
                      第 {page} / {totalPages} 页
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(page + 1)}
                      disabled={page >= totalPages}
                    >
                      下一页
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* 日志详情对话框 */}
      <Dialog open={isDetailDialogOpen} onOpenChange={setIsDetailDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedLog && (
                <>
                  {getLevelIcon(selectedLog.level)}
                  日志详情
                </>
              )}
            </DialogTitle>
            <DialogDescription>查看完整的日志信息</DialogDescription>
          </DialogHeader>
          {selectedLog && (
            <ScrollArea className="max-h-[60vh] pr-4">
              <div className="space-y-4">
                {/* 基本信息 */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">时间戳</label>
                    <p className="text-sm font-mono mt-1">{formatTimestamp(selectedLog.timestamp)}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">级别</label>
                    <div className="mt-1">
                      <Badge
                        variant={getLevelVariant(selectedLog.level)}
                        className="flex items-center gap-1 w-fit"
                      >
                        {getLevelIcon(selectedLog.level)}
                        {getLevelLabel(selectedLog.level)}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">来源</label>
                    <p className="text-sm mt-1">{selectedLog.source || selectedLog.logger || "系统"}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">类型</label>
                    <p className="text-sm mt-1">{selectedLog.type || "-"}</p>
                  </div>
                  {selectedLog.severity && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">严重性</label>
                      <p className="text-sm mt-1">
                        {selectedLog.severity === "high"
                          ? "高"
                          : selectedLog.severity === "medium"
                          ? "中"
                          : "低"}
                      </p>
                    </div>
                  )}
                  {selectedLog.request_id && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">请求 ID</label>
                      <p className="text-sm font-mono mt-1">{selectedLog.request_id}</p>
                    </div>
                  )}
                </div>

                {/* 消息 */}
                <div>
                  <label className="text-sm font-medium text-muted-foreground">消息</label>
                  <p className="text-sm mt-1 whitespace-pre-wrap break-words">
                    {selectedLog.message}
                  </p>
                </div>

                {/* 元数据 */}
                {selectedLog.metadata && Object.keys(selectedLog.metadata).length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">元数据</label>
                    <pre className="text-xs bg-muted p-3 rounded-md mt-1 overflow-auto">
                      {JSON.stringify(selectedLog.metadata, null, 2)}
                    </pre>
                  </div>
                )}

                {/* 堆栈跟踪 */}
                {selectedLog.stack_trace && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">堆栈跟踪</label>
                    <pre className="text-xs bg-muted p-3 rounded-md mt-1 overflow-auto whitespace-pre-wrap">
                      {selectedLog.stack_trace}
                    </pre>
                  </div>
                )}
              </div>
            </ScrollArea>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
