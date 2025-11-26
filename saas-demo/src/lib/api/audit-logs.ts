/**
 * 審計日誌 API 客戶端
 */

import { getApiBaseUrl } from "./config";

const API_BASE = getApiBaseUrl();

export interface AuditLog {
  id: number
  user_id: number
  user_email: string
  action: string
  resource_type: string
  resource_id?: string
  description?: string
  before_state?: Record<string, any>
  after_state?: Record<string, any>
  ip_address?: string
  user_agent?: string
  created_at: string
}

export interface AuditLogListResponse {
  items: AuditLog[]
  total: number
  skip: number
  limit: number
}

export interface AuditLogQueryParams {
  skip?: number
  limit?: number
  user_id?: number
  action?: string
  resource_type?: string
  resource_id?: string
  start_date?: string
  end_date?: string
}

/**
 * 查詢審計日誌
 */
export async function listAuditLogs(
  params?: AuditLogQueryParams
): Promise<AuditLogListResponse> {
  const urlParams = new URLSearchParams()
  if (params?.skip !== undefined) urlParams.append("skip", params.skip.toString())
  if (params?.limit !== undefined) urlParams.append("limit", params.limit.toString())
  if (params?.user_id !== undefined) urlParams.append("user_id", params.user_id.toString())
  if (params?.action) urlParams.append("action", params.action)
  if (params?.resource_type) urlParams.append("resource_type", params.resource_type)
  if (params?.resource_id) urlParams.append("resource_id", params.resource_id)
  if (params?.start_date) urlParams.append("start_date", params.start_date)
  if (params?.end_date) urlParams.append("end_date", params.end_date)

  const response = await fetch(`${API_BASE}/audit-logs/?${urlParams}`, {
    credentials: "include",
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 獲取審計日誌詳情
 */
export async function getAuditLog(logId: number): Promise<AuditLog> {
  const response = await fetch(`${API_BASE}/audit-logs/${logId}`, {
    credentials: "include",
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

