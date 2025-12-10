/**
 * 通知系統 API 客戶端
 */

import { getApiBaseUrl } from "./config";

const API_BASE = getApiBaseUrl();

export type NotificationType = "email" | "browser" | "webhook"
export type NotificationStatus = "pending" | "sent" | "failed"

export interface NotificationConfig {
  id: number
  name: string
  description?: string
  notification_type: NotificationType
  alert_levels?: string[]
  event_types?: string[]
  config_data: Record<string, any>
  recipients: string[]
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface Notification {
  id: number
  config_id?: number
  notification_type: NotificationType
  title: string
  message: string
  level?: string
  event_type?: string
  resource_type?: string
  resource_id?: string
  recipient: string
  status: NotificationStatus
  sent_at?: string
  error_message?: string
  metadata?: Record<string, any>
  read: boolean
  read_at?: string
  created_at: string
}

export interface NotificationTemplate {
  id: number
  name: string
  description?: string
  notification_type: NotificationType
  title_template: string
  body_template: string
  variables?: string[]
  conditions?: Record<string, any>
  default_metadata?: Record<string, any>
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface NotificationListResponse {
  items: Notification[]
  total: number
  skip: number
  limit: number
  unread_count: number
}

export interface NotificationTemplateListResponse {
  items: NotificationTemplate[]
  total: number
  skip: number
  limit: number
}

export interface NotificationConfigCreate {
  name: string
  description?: string
  notification_type: NotificationType
  alert_levels?: string[]
  event_types?: string[]
  config_data: Record<string, any>
  recipients: string[]
  enabled?: boolean
}

export interface NotificationConfigUpdate {
  name?: string
  description?: string
  alert_levels?: string[]
  event_types?: string[]
  config_data?: Record<string, any>
  recipients?: string[]
  enabled?: boolean
}

export interface NotificationTemplateCreate {
  name: string
  description?: string
  notification_type: NotificationType
  title_template: string
  body_template: string
  variables?: string[]
  conditions?: {
    alert_levels?: string[]
    event_types?: string[]
    resource_types?: string[]
  }
  default_metadata?: Record<string, any>
  enabled?: boolean
}

export interface NotificationTemplateUpdate {
  name?: string
  description?: string
  notification_type?: NotificationType
  title_template?: string
  body_template?: string
  variables?: string[]
  conditions?: {
    alert_levels?: string[]
    event_types?: string[]
    resource_types?: string[]
  }
  default_metadata?: Record<string, any>
  enabled?: boolean
}

export interface NotificationTemplatePreviewRequest {
  template_id?: number
  title_template?: string
  body_template?: string
  context?: Record<string, any>
}

export interface NotificationTemplatePreviewResponse {
  title: string
  message: string
}

/**
 * 創建通知配置
 */
export async function createNotificationConfig(
  config: NotificationConfigCreate
): Promise<NotificationConfig> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/notifications/configs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(config),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 列出通知配置
 */
export async function listNotificationConfigs(params?: {
  skip?: number
  limit?: number
  enabled?: boolean
}): Promise<NotificationConfig[]> {
  const { fetchWithAuth } = await import("./client")
  const urlParams = new URLSearchParams()
  if (params?.skip !== undefined) urlParams.append("skip", params.skip.toString())
  if (params?.limit !== undefined) urlParams.append("limit", params.limit.toString())
  if (params?.enabled !== undefined) urlParams.append("enabled", params.enabled.toString())

  const response = await fetchWithAuth(`${API_BASE}/notifications/configs?${urlParams}`, {
    credentials: "include",
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 獲取通知配置詳情
 */
export async function getNotificationConfig(configId: number): Promise<NotificationConfig> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/notifications/configs/${configId}`, {
    credentials: "include",
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 更新通知配置
 */
export async function updateNotificationConfig(
  configId: number,
  config: NotificationConfigUpdate
): Promise<NotificationConfig> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/notifications/configs/${configId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(config),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 刪除通知配置
 */
export async function deleteNotificationConfig(configId: number): Promise<{ message: string }> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/notifications/configs/${configId}`, {
    method: "DELETE",
    credentials: "include",
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 列出通知模板
 */
export async function listNotificationTemplates(params?: {
  skip?: number
  limit?: number
  enabled?: boolean
}): Promise<NotificationTemplateListResponse> {
  const { fetchWithAuth } = await import("./client")
  const urlParams = new URLSearchParams()
  if (params?.skip !== undefined) urlParams.append("skip", params.skip.toString())
  if (params?.limit !== undefined) urlParams.append("limit", params.limit.toString())
  if (params?.enabled !== undefined) urlParams.append("enabled", params.enabled.toString())

  const response = await fetchWithAuth(`${API_BASE}/notifications/templates?${urlParams}`, {
    credentials: "include",
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 創建通知模板
 */
export async function createNotificationTemplate(
  payload: NotificationTemplateCreate
): Promise<NotificationTemplate> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/notifications/templates`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 更新通知模板
 */
export async function updateNotificationTemplate(
  templateId: number,
  payload: NotificationTemplateUpdate
): Promise<NotificationTemplate> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/notifications/templates/${templateId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 刪除通知模板
 */
export async function deleteNotificationTemplate(templateId: number): Promise<{ message: string }> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/notifications/templates/${templateId}`, {
    method: "DELETE",
    credentials: "include",
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 預覽通知模板
 */
export async function previewNotificationTemplate(
  payload: NotificationTemplatePreviewRequest
): Promise<NotificationTemplatePreviewResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/notifications/templates/preview`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 查詢通知（當前用戶）
 */
export async function listNotifications(params?: {
  skip?: number
  limit?: number
  read?: boolean
  notification_type?: NotificationType
}): Promise<NotificationListResponse> {
  const { fetchWithAuth } = await import("./client")
  const urlParams = new URLSearchParams()
  if (params?.skip !== undefined) urlParams.append("skip", params.skip.toString())
  if (params?.limit !== undefined) urlParams.append("limit", params.limit.toString())
  if (params?.read !== undefined) urlParams.append("read", params.read.toString())
  if (params?.notification_type) urlParams.append("notification_type", params.notification_type)

  const response = await fetchWithAuth(`${API_BASE}/notifications/?${urlParams}`, {
    credentials: "include",
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 獲取未讀通知數量
 */
export async function getUnreadCount(): Promise<{ unread_count: number }> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/notifications/unread-count`, {
    credentials: "include",
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 標記通知為已讀
 */
export async function markNotificationRead(notificationId: number): Promise<{ message: string }> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/notifications/${notificationId}/read`, {
    method: "POST",
    credentials: "include",
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 標記所有通知為已讀
 */
export async function markAllRead(): Promise<{ message: string; count: number }> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/notifications/mark-all-read`, {
    method: "POST",
    credentials: "include",
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 批量標記通知為已讀
 */
export async function markNotificationsBulkRead(
  notificationIds: number[]
): Promise<{ message: string; count: number }> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/notifications/batch/read`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ notification_ids: notificationIds }),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 批量刪除通知
 */
export async function deleteNotificationsBulk(
  notificationIds: number[]
): Promise<{ message: string; count: number }> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/notifications/batch/delete`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ notification_ids: notificationIds }),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

