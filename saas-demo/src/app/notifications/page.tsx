/**
 * 通知列表頁面
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
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { useToast } from "@/hooks/use-toast"
import { Bell, Check, CheckCheck, Loader2, Trash2 } from "lucide-react"
import {
  listNotifications,
  markNotificationRead,
  markAllRead,
  markNotificationsBulkRead,
  deleteNotificationsBulk,
  type Notification,
} from "@/lib/api/notifications"

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

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [unreadCount, setUnreadCount] = useState(0)
  const [skip, setSkip] = useState(0)
  const [limit, setLimit] = useState(50)
  const [filterRead, setFilterRead] = useState<boolean | undefined>(undefined)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [bulkProcessing, setBulkProcessing] = useState(false)
  const { toast } = useToast()

  const loadNotifications = async () => {
    try {
      setLoading(true)
      const response = await listNotifications({
        skip,
        limit,
        read: filterRead,
      })
      setNotifications(response.items)
      setTotal(response.total)
      setUnreadCount(response.unread_count)
      setSelectedIds(new Set())
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "加載通知失敗",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadNotifications()
  }, [skip, limit, filterRead])

  const handleMarkRead = async (notificationId: number) => {
    try {
      await markNotificationRead(notificationId)
      setNotifications((prev) =>
        prev.map((n) =>
          n.id === notificationId ? { ...n, read: true } : n
        )
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
      toast({
        title: "成功",
        description: "通知已標記為已讀",
      })
    } catch (err) {
      toast({
        title: "錯誤",
        description: "標記已讀失敗",
        variant: "destructive",
      })
    }
  }

  const handleMarkAllRead = async () => {
    try {
      await markAllRead()
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
      setUnreadCount(0)
      toast({
        title: "成功",
        description: "所有通知已標記為已讀",
      })
    } catch (err) {
      toast({
        title: "錯誤",
        description: "標記已讀失敗",
        variant: "destructive",
      })
    }
  }

  const toggleSelect = (notificationId: number, checked: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (checked) {
        next.add(notificationId)
      } else {
        next.delete(notificationId)
      }
      return next
    })
  }

  const toggleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(new Set(notifications.map((n) => n.id)))
    } else {
      setSelectedIds(new Set())
    }
  }

  const handleBulkMarkRead = async () => {
    if (selectedIds.size === 0) return
    try {
      setBulkProcessing(true)
      const idArray = Array.from(selectedIds)
      await markNotificationsBulkRead(idArray)
      setNotifications((prev) =>
        prev.map((n) =>
          idArray.includes(n.id) ? { ...n, read: true } : n
        )
      )
      setUnreadCount((prev) => Math.max(0, prev - idArray.filter((id) => {
        const item = notifications.find((n) => n.id === id)
        return item && !item.read
      }).length))
      setSelectedIds(new Set())
      toast({ title: "成功", description: "選中通知已標記為已讀" })
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "批量標記已讀失敗",
        variant: "destructive",
      })
    } finally {
      setBulkProcessing(false)
    }
  }

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return
    if (!confirm(`確定刪除選中的 ${selectedIds.size} 條通知？`)) return
    try {
      setBulkProcessing(true)
      const idArray = Array.from(selectedIds)
      await deleteNotificationsBulk(idArray)
      setNotifications((prev) => prev.filter((n) => !idArray.includes(n.id)))
      setTotal((prev) => Math.max(0, prev - idArray.length))
      setUnreadCount((prev) =>
        Math.max(
          0,
          prev -
            idArray.filter((id) => {
              const n = notifications.find((item) => item.id === id)
              return n && !n.read
            }).length
        )
      )
      setSelectedIds(new Set())
      toast({ title: "成功", description: "選中通知已刪除" })
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "批量刪除失敗",
        variant: "destructive",
      })
    } finally {
      setBulkProcessing(false)
    }
  }

  const handleDeleteSingle = async (notificationId: number) => {
    if (!confirm("確定刪除此通知？")) return
    try {
      await deleteNotificationsBulk([notificationId])
      setNotifications((prev) => prev.filter((n) => n.id !== notificationId))
      setTotal((prev) => Math.max(0, prev - 1))
      setUnreadCount((prev) => {
        const removed = notifications.find((n) => n.id === notificationId)
        return removed && !removed.read ? Math.max(0, prev - 1) : prev
      })
      setSelectedIds((prev) => {
        const next = new Set(prev)
        next.delete(notificationId)
        return next
      })
      toast({ title: "成功", description: "通知已刪除" })
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "刪除通知失敗",
        variant: "destructive",
      })
    }
  }

  const getLevelBadgeVariant = (level?: string) => {
    switch (level) {
      case "high":
        return "destructive"
      case "medium":
        return "default"
      case "low":
        return "secondary"
      default:
        return "outline"
    }
  }

  const getLevelLabel = (level?: string) => {
    const labels: Record<string, string> = {
      high: "高",
      medium: "中",
      low: "低",
    }
    return labels[level || ""] || level || "信息"
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Bell className="h-8 w-8" />
            通知中心
          </h1>
          <p className="text-muted-foreground mt-2">
            查看和管理所有通知
          </p>
        </div>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <Button onClick={handleMarkAllRead} variant="outline">
              <CheckCheck className="h-4 w-4 mr-2" />
              全部已讀
            </Button>
          )}
          <Button
            variant={filterRead === undefined ? "default" : "outline"}
            onClick={() => setFilterRead(undefined)}
          >
            全部
          </Button>
          <Button
            variant={filterRead === false ? "default" : "outline"}
            onClick={() => setFilterRead(false)}
          >
            未讀 ({unreadCount})
          </Button>
          <Button
            variant={filterRead === true ? "default" : "outline"}
            onClick={() => setFilterRead(true)}
          >
            已讀
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              setSelectedIds(new Set())
              loadNotifications()
            }}
          >
            刷新
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>通知列表</CardTitle>
          <CardDescription>
            共 {total} 條通知，{unreadCount} 條未讀，顯示第 {skip + 1} - {Math.min(skip + limit, total)} 條
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">
              <Loader2 className="h-6 w-6 animate-spin mx-auto" />
            </div>
          ) : (
            <div className="border rounded-lg">
              {selectedIds.size > 0 && (
                <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/40">
                  <span className="text-sm text-muted-foreground">
                    已選 {selectedIds.size} 條
                  </span>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={handleBulkMarkRead}
                      disabled={bulkProcessing}
                    >
                      {bulkProcessing ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Check className="h-4 w-4 mr-2" />
                      )}
                      批量已讀
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={handleBulkDelete}
                      disabled={bulkProcessing}
                    >
                      {bulkProcessing ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4 mr-2" />
                      )}
                      批量刪除
                    </Button>
                  </div>
                </div>
              )}
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={notifications.length > 0 && selectedIds.size === notifications.length}
                        onCheckedChange={(checked) => toggleSelectAll(Boolean(checked))}
                        aria-label="全選"
                      />
                    </TableHead>
                    <TableHead>標題</TableHead>
                    <TableHead>級別</TableHead>
                    <TableHead>類型</TableHead>
                    <TableHead>時間</TableHead>
                    <TableHead>狀態</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {notifications.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8">
                        沒有通知
                      </TableCell>
                    </TableRow>
                  ) : (
                    notifications.map((notification) => (
                      <TableRow
                        key={notification.id}
                        className={!notification.read ? "bg-muted/30" : ""}
                      >
                        <TableCell>
                          <Checkbox
                            checked={selectedIds.has(notification.id)}
                            onCheckedChange={(checked) =>
                              toggleSelect(notification.id, Boolean(checked))
                            }
                            aria-label={`選擇通知 ${notification.title}`}
                          />
                        </TableCell>
                        <TableCell>
                          <div>
                            <div className="font-medium">{notification.title}</div>
                            <div className="text-sm text-muted-foreground line-clamp-1">
                              {notification.message}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          {notification.level && (
                            <Badge variant={getLevelBadgeVariant(notification.level)}>
                              {getLevelLabel(notification.level)}
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{notification.event_type || "-"}</Badge>
                        </TableCell>
                        <TableCell>{formatDateTime(notification.created_at)}</TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              notification.status === "sent"
                                ? "default"
                                : notification.status === "failed"
                                ? "destructive"
                                : "secondary"
                            }
                          >
                            {notification.status === "sent"
                              ? "已發送"
                              : notification.status === "failed"
                              ? "失敗"
                              : "待發送"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1">
                            {!notification.read && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleMarkRead(notification.id)}
                              >
                                <Check className="h-4 w-4 mr-1" />
                                已讀
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteSingle(notification.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}

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
    </div>
  )
}

