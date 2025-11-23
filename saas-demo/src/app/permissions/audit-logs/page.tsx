/**
 * 審計日誌查詢頁面
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { useToast } from "@/hooks/use-toast"
import { PermissionGuard } from "@/components/permissions/permission-guard"
import { FileText, Search, Filter, Eye, Calendar } from "lucide-react"
import { listAuditLogs, getAuditLog, type AuditLog, type AuditLogQueryParams } from "@/lib/api/audit-logs"
// 日期格式化函數
const formatDateTime = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  })
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [skip, setSkip] = useState(0)
  const [limit, setLimit] = useState(50)
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null)
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false)
  
  // 篩選條件
  const [filters, setFilters] = useState<AuditLogQueryParams>({
    user_id: undefined,
    action: undefined,
    resource_type: undefined,
    resource_id: undefined,
    start_date: undefined,
    end_date: undefined,
  })
  
  const { toast } = useToast()

  const loadLogs = async () => {
    try {
      setLoading(true)
      const params: AuditLogQueryParams = {
        skip,
        limit,
        ...filters,
      }
      const response = await listAuditLogs(params)
      setLogs(response.items)
      setTotal(response.total)
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "加載審計日誌失敗",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadLogs()
  }, [skip, limit, filters])

  const handleViewDetail = async (logId: number) => {
    try {
      const log = await getAuditLog(logId)
      setSelectedLog(log)
      setIsDetailDialogOpen(true)
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "獲取審計日誌詳情失敗",
        variant: "destructive",
      })
    }
  }

  const handleFilterChange = (key: keyof AuditLogQueryParams, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value || undefined,
    }))
    setSkip(0) // 重置分頁
  }

  const handleResetFilters = () => {
    setFilters({
      user_id: undefined,
      action: undefined,
      resource_type: undefined,
      resource_id: undefined,
      start_date: undefined,
      end_date: undefined,
    })
    setSkip(0)
  }

  const getActionBadgeVariant = (action: string) => {
    switch (action) {
      case "create":
        return "default"
      case "update":
        return "secondary"
      case "delete":
        return "destructive"
      case "assign":
      case "revoke":
        return "outline"
      default:
        return "outline"
    }
  }

  const getActionLabel = (action: string) => {
    const labels: Record<string, string> = {
      create: "創建",
      update: "更新",
      delete: "刪除",
      assign: "分配",
      revoke: "撤銷",
      reset_password: "重置密碼",
    }
    return labels[action] || action
  }

  const getResourceTypeLabel = (resourceType: string) => {
    const labels: Record<string, string> = {
      user: "用戶",
      role: "角色",
      permission: "權限",
      account: "賬號",
      script: "劇本",
    }
    return labels[resourceType] || resourceType
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <FileText className="h-8 w-8" />
            審計日誌
          </h1>
          <p className="text-muted-foreground mt-2">
            查看系統操作審計記錄
          </p>
        </div>
      </div>

      <PermissionGuard permission="audit:view">
        {/* 篩選區域 */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              篩選條件
            </CardTitle>
            <CardDescription>根據條件篩選審計日誌</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <div>
                <Label htmlFor="filter-user-id">用戶 ID</Label>
                <Input
                  id="filter-user-id"
                  type="number"
                  placeholder="用戶 ID"
                  value={filters.user_id || ""}
                  onChange={(e) => handleFilterChange("user_id", e.target.value ? parseInt(e.target.value) : undefined)}
                />
              </div>
              <div>
                <Label htmlFor="filter-action">操作類型</Label>
                <Select
                  value={filters.action || "__all__"}
                  onValueChange={(value) => handleFilterChange("action", value === "__all__" ? undefined : value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="全部" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">全部</SelectItem>
                    <SelectItem value="create">創建</SelectItem>
                    <SelectItem value="update">更新</SelectItem>
                    <SelectItem value="delete">刪除</SelectItem>
                    <SelectItem value="assign">分配</SelectItem>
                    <SelectItem value="revoke">撤銷</SelectItem>
                    <SelectItem value="reset_password">重置密碼</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="filter-resource-type">資源類型</Label>
                <Select
                  value={filters.resource_type || "__all__"}
                  onValueChange={(value) => handleFilterChange("resource_type", value === "__all__" ? undefined : value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="全部" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">全部</SelectItem>
                    <SelectItem value="user">用戶</SelectItem>
                    <SelectItem value="role">角色</SelectItem>
                    <SelectItem value="permission">權限</SelectItem>
                    <SelectItem value="account">賬號</SelectItem>
                    <SelectItem value="script">劇本</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="filter-resource-id">資源 ID</Label>
                <Input
                  id="filter-resource-id"
                  placeholder="資源 ID"
                  value={filters.resource_id || ""}
                  onChange={(e) => handleFilterChange("resource_id", e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="filter-start-date">開始時間</Label>
                <Input
                  id="filter-start-date"
                  type="datetime-local"
                  value={filters.start_date || ""}
                  onChange={(e) => handleFilterChange("start_date", e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="filter-end-date">結束時間</Label>
                <Input
                  id="filter-end-date"
                  type="datetime-local"
                  value={filters.end_date || ""}
                  onChange={(e) => handleFilterChange("end_date", e.target.value)}
                />
              </div>
            </div>
            <div className="flex justify-end mt-4">
              <Button variant="outline" onClick={handleResetFilters}>
                重置篩選
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 審計日誌列表 */}
        {loading ? (
          <div className="text-center py-8">加載中...</div>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>審計日誌列表</CardTitle>
              <CardDescription>
                共 {total} 條記錄，顯示第 {skip + 1} - {Math.min(skip + limit, total)} 條
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border rounded-lg">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>時間</TableHead>
                      <TableHead>用戶</TableHead>
                      <TableHead>操作</TableHead>
                      <TableHead>資源類型</TableHead>
                      <TableHead>資源 ID</TableHead>
                      <TableHead>描述</TableHead>
                      <TableHead>IP 地址</TableHead>
                      <TableHead className="text-right">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {logs.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-8">
                          沒有審計日誌數據
                        </TableCell>
                      </TableRow>
                    ) : (
                      logs.map((log) => (
                        <TableRow key={log.id}>
                          <TableCell>
                            {formatDateTime(log.created_at)}
                          </TableCell>
                          <TableCell>
                            <div>
                              <div className="font-medium">{log.user_email}</div>
                              <div className="text-sm text-muted-foreground">ID: {log.user_id}</div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant={getActionBadgeVariant(log.action)}>
                              {getActionLabel(log.action)}
                            </Badge>
                          </TableCell>
                          <TableCell>{getResourceTypeLabel(log.resource_type)}</TableCell>
                          <TableCell>{log.resource_id || "-"}</TableCell>
                          <TableCell className="max-w-xs truncate">{log.description || "-"}</TableCell>
                          <TableCell>{log.ip_address || "-"}</TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleViewDetail(log.id)}
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              詳情
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>

              {/* 分頁 */}
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-muted-foreground">
                  顯示 {skip + 1} - {Math.min(skip + limit, total)} 條，共 {total} 條
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSkip(Math.max(0, skip - limit))}
                    disabled={skip === 0}
                  >
                    上一頁
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSkip(skip + limit)}
                    disabled={skip + limit >= total}
                  >
                    下一頁
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 詳情對話框 */}
        <Dialog open={isDetailDialogOpen} onOpenChange={setIsDetailDialogOpen}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>審計日誌詳情</DialogTitle>
              <DialogDescription>查看完整的審計日誌信息</DialogDescription>
            </DialogHeader>
            {selectedLog && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>日誌 ID</Label>
                    <div className="text-sm">{selectedLog.id}</div>
                  </div>
                  <div>
                    <Label>時間</Label>
                    <div className="text-sm">
                      {formatDateTime(selectedLog.created_at)}
                    </div>
                  </div>
                  <div>
                    <Label>用戶</Label>
                    <div className="text-sm">{selectedLog.user_email} (ID: {selectedLog.user_id})</div>
                  </div>
                  <div>
                    <Label>操作</Label>
                    <div className="text-sm">
                      <Badge variant={getActionBadgeVariant(selectedLog.action)}>
                        {getActionLabel(selectedLog.action)}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <Label>資源類型</Label>
                    <div className="text-sm">{getResourceTypeLabel(selectedLog.resource_type)}</div>
                  </div>
                  <div>
                    <Label>資源 ID</Label>
                    <div className="text-sm">{selectedLog.resource_id || "-"}</div>
                  </div>
                  <div>
                    <Label>IP 地址</Label>
                    <div className="text-sm">{selectedLog.ip_address || "-"}</div>
                  </div>
                  <div>
                    <Label>用戶代理</Label>
                    <div className="text-sm truncate">{selectedLog.user_agent || "-"}</div>
                  </div>
                </div>
                {selectedLog.description && (
                  <div>
                    <Label>描述</Label>
                    <div className="text-sm">{selectedLog.description}</div>
                  </div>
                )}
                {selectedLog.before_state && (
                  <div>
                    <Label>操作前狀態</Label>
                    <pre className="text-xs bg-muted p-3 rounded-md overflow-auto">
                      {JSON.stringify(selectedLog.before_state, null, 2)}
                    </pre>
                  </div>
                )}
                {selectedLog.after_state && (
                  <div>
                    <Label>操作後狀態</Label>
                    <pre className="text-xs bg-muted p-3 rounded-md overflow-auto">
                      {JSON.stringify(selectedLog.after_state, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </PermissionGuard>
    </div>
  )
}

