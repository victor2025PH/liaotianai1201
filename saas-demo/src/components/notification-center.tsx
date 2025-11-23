/**
 * 通知中心組件
 */
"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Bell, Check, CheckCheck, Loader2, WifiOff, RefreshCcw } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { useToast } from "@/hooks/use-toast"
import {
  listNotifications,
  getUnreadCount,
  markNotificationRead,
  markAllRead,
  type Notification,
} from "@/lib/api/notifications"

// 日期格式化函數
const formatDateTime = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function NotificationCenter() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const disconnectToastShownRef = useRef(false)
  const { toast } = useToast()

  // 獲取當前用戶郵箱（從API獲取）
  const [userEmail, setUserEmail] = useState<string>("")
  const [connectionState, setConnectionState] = useState<"idle" | "connecting" | "connected" | "error" | "reconnecting">("idle")
  
  useEffect(() => {
    // 從API獲取當前用戶信息
    const fetchUserEmail = async () => {
      try {
        const { fetchWithAuth } = await import("@/lib/api/client");
        const response = await fetchWithAuth(`${process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1"}/users/me`, {
          credentials: "include",
        })
        
        if (!response.ok) {
          // 如果 API 返回 404 或 401，可能是禁用認證模式或未登錄
          if (response.status === 404 || response.status === 401) {
            console.warn("無法獲取用戶信息（可能是禁用認證模式），使用匿名用戶")
            // 在禁用認證模式下，使用匿名用戶或跳過通知功能
            setUserEmail("anonymous@example.com")
            return
          }
          throw new Error(`HTTP ${response.status}`)
        }
        
        const user = await response.json()
        if (user.email) {
          setUserEmail(user.email)
        } else {
          // 如果沒有郵箱，使用匿名用戶
          setUserEmail("anonymous@example.com")
        }
      } catch (err) {
        console.warn("獲取用戶信息失敗，使用匿名用戶:", err)
        // API 失敗時，使用匿名用戶（通知功能可能會受限）
        setUserEmail("anonymous@example.com")
      }
    }
    
    fetchUserEmail()
  }, [])

  const loadNotifications = useCallback(async () => {
    try {
      setLoading(true)
      const response = await listNotifications({ skip: 0, limit: 20 })
      setNotifications(response.items || [])
      setUnreadCount(response.unread_count || 0)
    } catch (err) {
      console.warn("加載通知失敗（可能是 API 不可用）:", err)
      // API 失敗時，設置空數組和零未讀數
      setNotifications([])
      setUnreadCount(0)
    } finally {
      setLoading(false)
    }
  }, [])

  const loadUnreadCount = useCallback(async () => {
    try {
      const response = await getUnreadCount()
      setUnreadCount(response.unread_count || 0)
    } catch (err) {
      console.warn("獲取未讀數量失敗（可能是 API 不可用）:", err)
      // API 失敗時，設置零未讀數
      setUnreadCount(0)
    }
  }, [])

  const clearHeartbeat = () => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current)
      heartbeatRef.current = null
    }
  }

  const connectWebSocket = useCallback(() => {
    // 如果沒有用戶郵箱或使用匿名用戶，跳過 WebSocket 連接
    if (!userEmail || userEmail === "anonymous@example.com") {
      console.warn("跳過 WebSocket 連接（匿名用戶或禁用認證模式）")
      return
    }

    try {
      const wsUrl =
        process.env.NEXT_PUBLIC_WS_URL ||
        (typeof window !== "undefined"
          ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/api/v1/notifications/ws`
          : "ws://localhost:8000/api/v1/notifications/ws")

      setConnectionState(reconnectAttemptsRef.current > 0 ? "reconnecting" : "connecting")
      const ws = new WebSocket(`${wsUrl}/${encodeURIComponent(userEmail)}`)
      wsRef.current = ws

      ws.onopen = () => {
        if (reconnectTimerRef.current) {
          clearTimeout(reconnectTimerRef.current)
          reconnectTimerRef.current = null
        }
        setConnectionState("connected")
        reconnectAttemptsRef.current = 0
        disconnectToastShownRef.current = false

        clearHeartbeat()
        heartbeatRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send("ping")
          }
        }, 30000)
      }

      ws.onmessage = (event) => {
        try {
          if (event.data === "pong") {
            return
          }

          const data = JSON.parse(event.data)
          if (data.type === "notification") {
            loadNotifications()
            loadUnreadCount()

            if (typeof window !== "undefined" && "Notification" in window) {
              if (Notification.permission === "granted") {
                new Notification(data.title, {
                  body: data.message,
                  icon: "/favicon.ico",
                })
              } else if (Notification.permission === "default") {
                Notification.requestPermission()
              }
            }
          }
        } catch (err) {
          console.error("解析 WebSocket 消息失敗:", err)
        }
      }

      ws.onerror = (error) => {
        console.error("WebSocket 錯誤:", error)
        setConnectionState("error")
      }

      ws.onclose = () => {
        clearHeartbeat()
        if (!disconnectToastShownRef.current) {
          toast({
            title: "通知連線中斷",
            description: "正在嘗試重新連線...",
            variant: "destructive",
          })
          disconnectToastShownRef.current = true
        }
        if (reconnectTimerRef.current) {
          return
        }
        const attempt = reconnectAttemptsRef.current + 1
        reconnectAttemptsRef.current = attempt
        const delay = Math.min(30000, 2000 * attempt)
        setConnectionState("reconnecting")
        reconnectTimerRef.current = setTimeout(() => {
          reconnectTimerRef.current = null
          connectWebSocket()
        }, delay)
      }
    } catch (err) {
      console.error("建立 WebSocket 連接失敗:", err)
      setConnectionState("error")
      if (!reconnectTimerRef.current) {
        const attempt = reconnectAttemptsRef.current + 1
        reconnectAttemptsRef.current = attempt
        const delay = Math.min(30000, 2000 * attempt)
        reconnectTimerRef.current = setTimeout(() => {
          reconnectTimerRef.current = null
          connectWebSocket()
        }, delay)
      }
    }
  }, [loadNotifications, loadUnreadCount, toast, userEmail])

  useEffect(() => {
    if (!userEmail) return

    // 只在有有效用户邮箱时执行
    if (userEmail === "anonymous@example.com") {
      // 匿名用户只加载通知，不连接 WebSocket
      loadNotifications().catch((err) => {
        console.warn("匿名用戶加載通知失敗:", err)
      })
      return
    }

    let interval: NodeJS.Timeout | null = null

    const initialize = async () => {
      try {
        await Promise.all([
          loadNotifications(),
          loadUnreadCount()
        ])
        connectWebSocket()

        interval = setInterval(() => {
          loadUnreadCount().catch((err) => {
            console.warn("定期加載未讀數量失敗:", err)
          })
        }, 30000)
      } catch (err) {
        console.error("初始化通知中心失敗:", err)
      }
    }

    initialize()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      clearHeartbeat()
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }
      if (interval) {
        clearInterval(interval)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userEmail]) // 只依賴 userEmail，避免無限循環。loadNotifications, loadUnreadCount, connectWebSocket 是穩定的 useCallback

  // 當彈窗打開時，加載通知
  useEffect(() => {
    if (open) {
      loadNotifications()
    }
  }, [open])

  const handleMarkRead = async (notificationId: number) => {
    try {
      await markNotificationRead(notificationId)
      setNotifications((prev) =>
        prev.map((n) =>
          n.id === notificationId ? { ...n, read: true } : n
        )
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
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
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, read: true }))
      )
      setUnreadCount(0)
      toast({
        title: "成功",
        description: "已標記所有通知為已讀",
      })
    } catch (err) {
      toast({
        title: "錯誤",
        description: "標記全部已讀失敗",
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

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
            >
              {unreadCount > 99 ? "99+" : unreadCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-0" align="end">
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold">通知</h3>
            <div
              className={`flex items-center gap-1 text-xs ${
                connectionState === "connected"
                  ? "text-emerald-600"
                  : connectionState === "connecting" || connectionState === "reconnecting"
                  ? "text-amber-600"
                  : "text-destructive"
              }`}
            >
              {connectionState === "connected" && "即時同步"}
              {connectionState === "connecting" && (
                <>
                  <Loader2 className="h-3 w-3 animate-spin" />
                  連線中...
                </>
              )}
              {connectionState === "reconnecting" && (
                <>
                  <RefreshCcw className="h-3 w-3 animate-spin" />
                  重新連線...
                </>
              )}
              {connectionState === "error" && (
                <>
                  <WifiOff className="h-3 w-3" />
                  連線中斷
                </>
              )}
            </div>
          </div>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleMarkAllRead}
              className="h-8 text-xs"
            >
              <CheckCheck className="h-3 w-3 mr-1" />
              全部已讀
            </Button>
          )}
        </div>
        <ScrollArea className="h-[400px]">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : notifications.length === 0 ? (
            <div className="flex items-center justify-center py-8 text-muted-foreground text-sm">
              沒有通知
            </div>
          ) : (
            <div className="divide-y">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 hover:bg-muted/50 transition-colors ${
                    !notification.read ? "bg-muted/30" : ""
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium text-sm truncate">
                          {notification.title}
                        </h4>
                        {notification.level && (
                          <Badge
                            variant={getLevelBadgeVariant(notification.level)}
                            className="text-xs"
                          >
                            {notification.level}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {notification.message}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {formatDateTime(notification.created_at)}
                      </p>
                    </div>
                    {!notification.read && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={() => handleMarkRead(notification.id)}
                      >
                        <Check className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
        {notifications.length > 0 && (
          <div className="p-2 border-t">
            <Button
              variant="ghost"
              size="sm"
              className="w-full"
              onClick={() => {
                // 導航到通知列表頁面
                window.location.href = "/notifications"
              }}
            >
              查看全部
            </Button>
          </div>
        )}
      </PopoverContent>
    </Popover>
  )
}

